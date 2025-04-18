# example/views.py
from django.http import JsonResponse
from graphene_django.views import GraphQLView
from blog.schema import schema
from django.views.decorators.csrf import ensure_csrf_cookie


def graphql_view(request):
    response = GraphQLView.as_view(schema=schema)(request)
    return JsonResponse(response.content)


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set"})
