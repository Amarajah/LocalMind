from django.urls import path
from . import views

urlpatterns = [
    path('models/', views.list_models_view, name='list_models'),
    path('models/pull/', views.pull_model_view, name='pull_model'),
    path('models/delete/', views.delete_model_view, name='delete_model'),
    path('stats/', views.system_stats_view, name='system_stats'),
    path('settings/', views.get_settings_view, name='get_settings'),
    path('settings/update/', views.update_settings_view, name='update_settings'),
]