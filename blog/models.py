from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import reverse
from django.utils.text import slugify
from tinymce.models import HTMLField


class Profile(models.Model):
    objects = None
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    website = models.URLField(blank=True, null=True)
    bio = models.CharField(max_length=240, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    objects = None
    
    class Meta:
        ordering = ["-publish_date"]

    title = models.CharField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=255, blank=True, null=False)
    slug = models.SlugField(max_length=255, unique=False)
    body = HTMLField()
    meta_description = models.CharField(max_length=150, blank=True, null=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    publish_date = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)
    author = models.ForeignKey(Profile, on_delete=models.PROTECT)
    tags = models.ManyToManyField(Tag, blank=True)

    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)

    def get_absolute_url(self):
        return reverse("blog:post", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        # Generate a unique slug based on the post's title
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure the slug is unique
            num = 1
            while Post.objects.filter(slug=self.slug).exists():
                self.slug = f"{slugify(self.title)}-{num}"
                num += 1
        super().save(*args, **kwargs)


class Interaction(models.Model):
    post = models.ForeignKey(Post, related_name='interactions', on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255)
    like = models.BooleanField(default=False)
    dislike = models.BooleanField(default=False)
    share = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'session_id')

