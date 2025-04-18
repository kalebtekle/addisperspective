from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from graphene_file_upload.django import FileUploadGraphQLView
from blog.schema import schema  # or wherever your GraphQL schema is
from blog.views import get_csrf_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path("csrf/", get_csrf_token),  # Just GET this before your GraphQL calls
    path('graphql/', FileUploadGraphQLView.as_view(graphiql=True, schema=schema)),
]

# Serve static and media files only in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
