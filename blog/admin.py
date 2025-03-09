from django.contrib import admin

from blog.models import Profile, Post, Tag, Interaction
from django import forms
from django.db import models



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    model = Profile


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    model = Tag

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'action', 'created_at')
    actions = ['delete_selected_interactions']  # Add custom actions
    model = Interaction


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    model = Post
    
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'class': 'tinymce'})},
    }
       

    list_display = (
        "id",
        "title",
        "subtitle",
        "slug",
        "publish_date",
        "published",
        "body",
        
    )
    list_filter = (
        "published",
        "publish_date",
    )
    list_editable = (
        "title",
        "subtitle",
        "slug",
        "publish_date",
        "published",
        "body",
    )
    search_fields = (
        "title",
        "subtitle",
        "slug",
        "body",
    )
    prepopulated_fields = {
        "slug": (
            "title",
            "subtitle",
        )
    }
    date_hierarchy = "publish_date"
    save_on_top = True

def delete_selected_interactions(modeladmin, request, queryset):
    """Custom action to delete selected interactions."""
    queryset.delete()

delete_selected_interactions.short_description = "Delete selected interactions"
