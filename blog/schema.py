import graphene
from django.contrib.auth import get_user_model, authenticate
from graphene_django import DjangoObjectType
import graphql_jwt
from graphql_jwt.shortcuts import  get_token
from blog import models
from django.contrib.auth import get_user_model

class InteractionsType(graphene.ObjectType):
    like_count = graphene.Int()
    dislike_count = graphene.Int()
    share_count = graphene.Int()

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
    interactions = graphene.Field(InteractionsType)
    is_admin_or_staff = graphene.Boolean()
    formatted_date = graphene.String()
    author = graphene.Field(ProfileType)

    class Meta:
        model = models.Post
        fields = ('id', 'title', 'subtitle', 'created_at', 'updated_at', 'publish_date', 'published', 'meta_description', 'slug', 'body', 'author', 'tags', 'interactions')
    
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
        like_count = interactions.filter(like=True).count()
        dislike_count = interactions.filter(dislike=True).count()
        share_count = interactions.filter(share=True).count()
        
        return InteractionsType(
            like_count=like_count,
            dislike_count=dislike_count,
            share_count=share_count
        )
    def resolve_author(self, info):
        return self.author  # Ensure this returns a Profile object

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
        return CreatePostMutation(success=True, post=post, message="Post created successfully.")

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
        return (
            models.Post.objects.prefetch_related("tags")
            .select_related("author")
            .get(slug=slug)
        )
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
        post_id = graphene.ID(required=True)
        action = graphene.String(required=True)
        session_id = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    interactions = graphene.Field(InteractionsType)

    def mutate(self, info, post_id, action, session_id):
        try:
            post = models.Post.objects.get(id=post_id)
        except models.Post.DoesNotExist:
            return UpdateInteractions(success=False, message="Post not found")

        interaction, created = models.Interaction.objects.get_or_create(post=post, session_id=session_id)

        if action == "like":
            if interaction.like:
                interaction.like = False
                post.like_count -= 1
                
            else:
                interaction.like = True
                post.like_count += 1

                 # If previously disliked, reset dislike
                if interaction.dislike:
                    interaction.dislike = False
                    post.dislike_count -= 1 

        elif action == "dislike":
            if interaction.dislike:
                interaction.dislike = False
                post.dislike_count -= 1
                
            else:
                interaction.dislike = True
                post.dislike_count += 1

                # If previously liked, reset like
                if interaction.like:
                    interaction.like = False
                    post.like_count -= 1
        elif action == "share":
                    post.share_count += 1
        else:
            return UpdateInteractions(success=False, message="Invalid action")

        interaction.save()
        post.save()

        return UpdateInteractions(
            success=True,
            message="Interactions updated successfully",
            interactions=InteractionsType(
                like_count=post.like_count,
                dislike_count=post.dislike_count,
                share_count=post.share_count
            )
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

    def mutate(self,info,email, password):
        user = authenticate(email=email, password=password)
        if user:
            print("User authenticated successfully:", user)
            # Generate JWT token for authenticated user
            token = get_token(user)
            print("Generated token:", token) # Check what token is being generated
            if token:
                return Login(
                    success=True,
                    token=token,
                    message="Login successful!",
                    user=user
                )
                
            else:
                return Login(success=False, token=None, message="Token generation failed!")
        else:
            return Login(success=False, token=None, message="Invalid credentials!")

class Mutation(graphene.ObjectType):
    token_auth = CustomObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    update_interactions = UpdateInteractions.Field()
    signup = Signup.Field()
    login = Login.Field()
    create_post = CreatePostMutation.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
