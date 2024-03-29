# myapp/signals.py
# backend/blog/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post


@receiver(post_save, sender=Post)
def post_save_handler(instance, **kwargs):
    # Your signal handling code here
    pass
