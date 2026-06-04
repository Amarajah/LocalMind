from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_snippets, name='list_snippets'),
    path('create/', views.create_snippet, name='create_snippet'),
    path('<int:pk>/', views.snippet_detail, name='snippet_detail'),
    path('<int:pk>/export/', views.export_snippet, name='export_snippet'),
]