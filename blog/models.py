from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.shortcuts import reverse
from django.utils.text import slugify
from tinymce.models import HTMLField


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='profile')
    website = models.URLField(blank=True, null=True)
    bio = models.CharField(max_length=240, blank=True, null=True)
    image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    class Meta:
        ordering = ["-publish_date"]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, unique=True)
    subtitle = models.CharField(max_length=255, blank=True, null=False)
    slug = models.SlugField(max_length=255, unique=False)
    body = HTMLField()
    meta_description = models.CharField(max_length=150, blank=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    publish_date = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True)

    @property
    def excerpt(self):
        return self.body[:240]

    def get_absolute_url(self):
        return reverse("blog:post", kwargs={"slug": self.slug})

    def delete(self, *args, **kwargs):
        # Delete all interactions associated with the post
        self.interactions.all().delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Generate a unique slug based on the post's title
        if not self.slug:
            self.slug = slugify(self.title)
            num = 1
            while Post.objects.filter(slug=self.slug).exists():
                self.slug = f'{slugify(self.title)}-{num}'
                num += 1
        super().save(*args, **kwargs)

    def like_count(self):
        return self.interactions.filter(like=True).count()

    def dislike_count(self):
        return self.interactions.filter(dislike=True).count()

    def share_count(self):
        return self.interactions.filter(share=True).count()


class Interaction(models.Model):
    ACTION_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('share', 'Share'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="interactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Optional for anonymous users
    action = models.CharField(
    max_length=10, 
    choices=[('like', 'Like'), ('dislike', 'Dislike'), ('share', 'Share')],
    default='like'  # Set a default value
)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user', 'action')  # Prevent duplicate actions per user


class AdUnit(models.Model):
    name = models.CharField(max_length=100)  # Name of the ad slot
    position = models.CharField(max_length=50)  # e.g., "sidebar", "header"
    width = models.IntegerField()  # Ad width
    height = models.IntegerField()  # Ad height
    ad_code = models.TextField(blank=True, null=True)  # HTML/JS Ad code
    custom_ad = models.TextField(blank=True, null=True)  # Custom Ad content
    impressions = models.IntegerField(default=0)  # Track number of views
    clicks = models.IntegerField(default=0)  # Track number of clicks
    cost_per_click = models.DecimalField(max_digits=10, decimal_places=2, default=0.50)  # Cost per click
    cost_per_impression = models.DecimalField(max_digits=10, decimal_places=2, default=0.05)  # Cost per impression
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def calculate_revenue(self):
        ''' Calculate revenue based on impressions and clicks
         Example: revenue = clicks * cost_per_click + impressions * cost_per_impression'''
        revenue = (self.clicks * self.cost_per_click) + (self.impressions * self.cost_per_impression)
        return revenue


@receiver(pre_delete, sender=Post)
def delete_related_interactions(sender, instance, **kwargs):
    # Delete related interactions
    instance.interactions.all().delete()
