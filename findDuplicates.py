import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv()

# Set DJANGO_SETTINGS_MODULE and configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', r'C:\Users\Administrator\Desktop\VueProjects\dvg\backend\backend\settings.py')
import django
django.setup()

from django.db import connection
from django.db.models import Count
from blog.models import Interaction

def find_duplicates():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT post_id, COUNT(*)
            FROM blog_interaction
            GROUP BY post_id
            HAVING COUNT(*) > 1
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f'Post ID {row[0]} has {row[1]} interactions')

def remove_duplicates():
    interactions = Interaction.objects.values('post_id').annotate(count=Count('id')).filter(count__gt=1)
    for interaction in interactions:
        duplicates = Interaction.objects.filter(post_id=interaction['post_id'])
        duplicates.exclude(id=duplicates.first().id).delete()

# Find and remove duplicates
find_duplicates()
remove_duplicates()
