import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from blog import models

class InteractionsType(graphene.ObjectType):
    like_count = graphene.Int()
    dislike_count = graphene.Int()
    share_count = graphene.Int()

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class AuthorType(DjangoObjectType):
    class Meta:
        model = models.Profile

class PostType(DjangoObjectType):
    interactions = graphene.Field(InteractionsType)

    class Meta:
        model = models.Post
        fields = ('id', 'title', 'subtitle', 'publish_date', 'published', 'meta_description', 'slug', 'body', 'author', 'tags', 'interactions')

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

class TagType(DjangoObjectType):
    class Meta:
        model = models.Tag

class Query(graphene.ObjectType):
    all_posts = graphene.List(PostType, page=graphene.Int(), page_size=graphene.Int())
    allPostsCount = graphene.Int()
    author_by_username = graphene.Field(AuthorType, username=graphene.String())
    post_by_slug = graphene.Field(PostType, slug=graphene.String())
    posts_by_author = graphene.List(PostType, username=graphene.String())
    posts_by_tag = graphene.List(PostType, tag=graphene.String())
    post_by_id = graphene.Field(PostType, id=graphene.ID(required= True))

    def resolve_all_posts(self, info, page=1, page_size=10):
        offset = (page - 1) * page_size
        return models.Post.objects.all()[offset:offset + page_size]

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
        elif action == "dislike":
            if interaction.dislike:
                interaction.dislike = False
                post.dislike_count -= 1
            else:
                interaction.dislike = True
                post.dislike_count += 1
        elif action == "share":
            if not interaction.share:
                interaction.share = True
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
 
class Mutation(graphene.ObjectType):
    update_interactions = UpdateInteractions.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
