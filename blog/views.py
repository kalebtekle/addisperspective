# example/views.py
from django.http import JsonResponse
from graphene_django.views import GraphQLView

def graphql_view(request):
    response = GraphQLView.as_view(schema=schema)(request)
    return JsonResponse(response.content)

