# mutations.py

import graphene
from graphene import ObjectType, String, ID, Boolean
from .models import Post, UserInteractions

class InteractionsType(graphene.ObjectType):
    likes = graphene.Int()
    dislikes = graphene.Int()
    shares = graphene.Int()

class UpdateInteractions(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        action = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    interactions = graphene.Field(InteractionsType)

    def mutate(self, info, id, action):
        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            return UpdateInteractions(success=False, message="Post not found")

        user_interactions, created = UserInteractions.objects.get_or_create(post=post)

        if action == "like":
            user_interactions.likes += 1
        elif action == "dislike":
            user_interactions.dislikes += 1
        elif action == "share":
            user_interactions.shares += 1
        else:
            return UpdateInteractions(success=False, message="Invalid action")

        user_interactions.save()

        return UpdateInteractions(
            success=True,
            message="Interactions updated successfully",
            interactions=user_interactions
        )
        

class Mutation(ObjectType):
    update_interactions = UpdateInteractions.Field()
