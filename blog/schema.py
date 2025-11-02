import graphene
from django.contrib.auth import get_user_model, authenticate
from graphene_django import DjangoObjectType
import graphql_jwt
from graphql_jwt.shortcuts import  get_token
from blog import models
from django.contrib.auth import get_user_model
from blog.models import Post, Profile
from social_django.utils import load_strategy
from social_core.backends.google import GoogleOAuth2
from social_core.exceptions import AuthTokenError
from graphql_jwt.shortcuts import get_token

class InteractionType(DjangoObjectType):
    class Meta:
        model = models.Interaction
        fields ='__all__'
       
User = get_user_model()
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email','is_active','is_staff', 'is_superuser', 'date_joined', 'last_login')
    bio = graphene.String()
    image = graphene.String()
    website = graphene.String()

    def resolve_bio(self, info):
        profile = models.Profile.objects.filter(user=self).first()
        return profile.bio if profile else None

    def resolve_website(self, info):
        profile = models.Profile.objects.filter(user=self).first()
        return profile.website if profile else None
    
class ProfileType(DjangoObjectType):
    class Meta:
        model = models.Profile
        fields = ("id", "user", "website", "bio")

    # Explicitly define the user field to return UserType
    user = graphene.Field(UserType)

    def resolve_user(self, info):
        return self.user  # Ensure this returns the related User instance
    
class PostType(DjangoObjectType):
    interactions = graphene.List(InteractionType)
    is_admin_or_staff = graphene.Boolean()
    formatted_date = graphene.String()
    author = graphene.Field(ProfileType)
    excerpt = graphene.String()

    class Meta:
        model = models.Post
        fields = ('id', 'title', 'subtitle', 'excerpt', 'created_at', 'updated_at', 'publish_date', 'published', 'meta_description', 'slug', 'body', 'author', 'tags', 'interactions')
    
    def resolve_is_admin_or_staff(self, info):
        user = info.context.user
        return user.is_staff or user.is_superuser  # True for admin/staff
    
    def resolve_formatted_date(self, info):
         # Provide a default formatted date
        if self.publish_date:
            if info.context.user.is_staff or info.context.user.is_superuser:
                return self.publish_date.isoformat()  # Return full datetime for admin/staff
            return self.publish_date.strftime('%A, %B %d, %Y')  # Return date only for others
        return None
    
    def resolve_interactions(self, info):
        interactions = models.Interaction.objects.filter(post=self)
        return interactions if interactions.exists() else None # Return None instead of []

    def resolve_author(self, info):
        return self.author  # Ensure this returns a Profile object
    
    def resolve_excerpt(self, info):
        return self.body[:240]  # Return the first 240 characters of the body
class PaginatedPostType(graphene.ObjectType):
    posts = graphene.List(PostType, required=True)
    total_count = graphene.Int()  # total number of posts
    total_pages = graphene.Int()  # total pages based on page size

class TagType(DjangoObjectType):
    class Meta:
        model = models.Tag

class CreatePostInput(graphene.InputObjectType):
        title = graphene.String(required=True)
        subtitle = graphene.String(required=False)
        slug = graphene.String(required=True)
        body = graphene.String(required=True)
        tags = graphene.List(graphene.String, required=False)
        author = graphene.String(required=True)
        createdAt = graphene.DateTime(required=True)
        updatedAt = graphene.DateTime(required=True)
    
    
class CreatePostMutation(graphene.Mutation):
    class Arguments:
        input = CreatePostInput(required=True)

    post = graphene.Field(PostType)
    next_post_id = graphene.Int() # Return the predicted next ID
    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        user = info.context.user
        print(f"User: {user}")
        print("Headers:", info.context.headers)

        # Ensure the user is authenticated and is an admin
        if not user.is_authenticated:
            return CreatePostMutation(success=False, message="Permission denied. Please log in.")
        if not user.is_staff:  # Adjust this check if your admin logic is different
            return CreatePostMutation(success=False, message="Permission denied. Only admins can create posts.")

        # Create the post
        post = models.Post.objects.create(
            title=input.title,
            subtitle=input.subtitle,
            slug=input.slug,
            body=input.body,
            author=user.profile,
            created_at=input.createdAt,
            updated_at=input.updatedAt,
        )
        if input.tags:
            post.tags.set(input.tags)

        # Get the last post and predict the next ID
        last_post = models.Post.objects.order_by('-id').first()
        next_post_id = (last_post.id + 1) if last_post else 1  # If no posts exist, start from 1
        return CreatePostMutation(success=True, post=post, next_id=next_post_id, message="Post created successfully.")

class DeletePostMutation(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, post_id):
        user = info.context.user
        if not user.is_authenticated:
            return DeletePostMutation(success=False, message="Permission denied. Please log in.")
        
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return DeletePostMutation(success=False, message="Post does not exist.")
        
        # Ensure the Profile object exists
        try:
            profile = Profile.objects.get(id=post.author.id)
        except Profile.DoesNotExist:
            return DeletePostMutation(success=False, message="Author profile does not exist.")
        
        # Ensure the user is the author of the post or an admin
        if user.profile != post.author and not user.is_staff:
            return DeletePostMutation(success=False, message="You do not have permission to delete this post.")
        
        post.delete()
        return DeletePostMutation(success=True, message="Post deleted successfully.")

class AdUnitType(DjangoObjectType):
    class Meta:
        model = models.AdUnit

class TrackAdImpression(graphene.Mutation):
    class Arguments:
        ad_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, ad_id):
        try:
            ad = models.AdUnit.objects.get(id=ad_id)
            ad.impressions += 1
            ad.save()
            return TrackAdImpression(success=True)
        except models.AdUnit.DoesNotExist:
            return TrackAdImpression(success=False)
class CustomObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def resolve(cls, root, info, **kwargs):
        user = info.context.user
        return cls(user=user, success=True, message="Login successful")

    @classmethod
    def mutate(cls, root, info, **kwargs):
        # Custom mutation logic with error handling
        try:
            result = super().mutate(root, info, **kwargs)
            return result
        except Exception as e:
            return cls(success=False, message=str(e))

class UpdateInteractions(graphene.Mutation):
    class Arguments:
        postId = graphene.ID(required=True)
        action = graphene.String(required=True)
        sessionId = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    interactions= graphene.Field(InteractionType)  # Use DjangoObjectType

    def mutate(self, info, postId, action, sessionId=None):
        try:
            post = Post.objects.get(id=postId)
        except Post.DoesNotExist:
            return UpdateInteractions(success=False, message="Post not found")

        interaction, created = models.Interaction.objects.get_or_create(post=post, action=action)

        interaction.count += 1
        interaction.save()

        return UpdateInteractions(
            success=True,
            message=f"{action} updated successfully",
            interaction=interaction
        )
class Signup(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self,info, username, password, email):
        user = User.objects.create_user(username=username, password=password, email=email)
        return Signup(success=True, message="User registered successfully!")

class Login(graphene.Mutation):
    token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):  # Authenticate manually
            token = get_token(user)
            return Login(success=True, token=token, message="Login successful!", user=user)
        return Login(success=False, token=None, message="Invalid credentials!")
    
    
class AuthenticateWithGoogle(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)

    success = graphene.Boolean()
    user_id = graphene.Int()
    email = graphene.String()
    jwt_token = graphene.String()

    def mutate(self, info, token):
        strategy = load_strategy()
        backend = GoogleOAuth2(strategy=strategy)

        try:
            user_data = backend.do_auth(token)
            user, created = User.objects.get_or_create(email=user_data.email)

            jwt_token = get_token(user)  # Generate JWT token

            return AuthenticateWithGoogle(
                success=True, user_id=user.id, email=user.email, jwt_token=jwt_token
            )
        except AuthTokenError:
            raise Exception("Invalid token")
        
class BookType(DjangoObjectType):
    class Meta:
        model = models.Book
        fields = ("id", "title", "description",  "excerpt", "author",  "published_date", "price","cover_image")
    
    # Add a custom field for the excerpt
    excerpt = graphene.String()

    def resolve_excerpt(self, info):
        return self.excerpt
class CreateBook(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        author = graphene.String(required=True)
        published_date = graphene.Date(required=True)
        price = graphene.Float(required=True)
        cover_image = graphene.String(required=False)

    book = graphene.Field(BookType)

    def mutate(self, info, title, description, author, published_date, price,cover_image=None):
        book = models.Book(
            title=title,
            description=description,
            author=author,
            published_date=published_date,
            price=price,
            cover_image=cover_image,
        )
        book.save()
        return CreateBook(book=book)

class Query(graphene.ObjectType):
    me=graphene.Field(UserType)
    all_posts = graphene.Field(PaginatedPostType, page=graphene.Int(), page_size=graphene.Int())
    allPostsCount = graphene.Int()
    author_by_username = graphene.Field(UserType, username=graphene.String())
    post_by_slug = graphene.Field(PostType, slug=graphene.String())
    posts_by_author = graphene.List(PostType, username=graphene.String())
    posts_by_tag = graphene.List(PostType, tag=graphene.String())
    post_by_id = graphene.Field(PostType, id=graphene.ID(required= True))
    
    posts = graphene.List(PostType)
    tags = graphene.List(TagType)

    all_profiles = graphene.List(ProfileType)
    user= graphene.Field(UserType)

    ad_units = graphene.List(AdUnitType, position=graphene.String())
    interactions = graphene.List(InteractionType, post_id=graphene.ID(required=True))
    book_details = graphene.Field(BookType, id=graphene.ID(required=True))
    def resolve_posts(self, info):
        return models.Post.objects.all()

    def resolve_tags(self, info):
        return models.Tag.objects.all()
    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required!")
        return user

    def resolve_all_posts(self, info, page=1, page_size=10):
        total_count = models.Post.objects.count()  # Get the total count of posts
        total_pages = (total_count + page_size - 1) // page_size  # Calculate total pages
        offset = (page - 1) * page_size
        posts = models.Post.objects.all()[offset:offset + page_size] # Fetch paginated posts
        return PaginatedPostType(posts=posts, total_count=total_count, total_pages=total_pages)


    def resolve_author_by_username(root, info, username):
        return models.Profile.objects.select_related("user").get(
            user__username=username
        )

    def resolve_post_by_slug(root, info, slug):
        return models.Post.objects.filter(slug=slug).first()
    
    def resolve_post_by_id(self, info, id):
        try:
            return models.Post.objects.get(pk=id)
        except models.Post.DoesNotExist:
            return None

    def resolve_posts_by_author(root, info, username):
        return (
            models.Post.objects.prefetch_related("tags")
            .select_related("author")
            .filter(author__user__username=username)
        )

    def resolve_posts_by_tag(root, info, tag):
        return (
            models.Post.objects.prefetch_related("tags")
            .select_related("author")
            .filter(tags__name__iexact=tag)
        )
    def resolve_all_profiles(self, info):
        return models.Profile.objects.select_related("user").all()
    
    def resolve_user(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    def resolve_ad_units(self, info, position=None):
        if position:
            return models.AdUnit.objects.filter(position=position)
        return models.AdUnit.objects.all()
    
    def resolve_interactions(self, info, post_id):
        interactions = models.Interaction.objects.filter(post_id=post_id)
        if not interactions.exists():
            return []
        return interactions # Ensure empty set is returned None instead of []
    
    def resolve_book_details(root, info, id):
        return models.Book.objects.get(pk=id)
class Mutation(graphene.ObjectType):
    token_auth = CustomObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    update_interactions = UpdateInteractions.Field()
    signup = Signup.Field()
    login = Login.Field()
    create_post = CreatePostMutation.Field()
    delete_post = DeletePostMutation.Field()

    track_ad_impression = TrackAdImpression.Field() # Track ad impressions
    authenticate_with_google = AuthenticateWithGoogle.Field()

    create_book = CreateBook.Field()
schema = graphene.Schema(query=Query, mutation=Mutation)
