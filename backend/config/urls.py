from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'LocalMind API'})

def chat_view(request):
    return render(request, 'chat.html')

def models_view(request):
    return render(request, 'models.html', {
        'recommended_models': [
            'codellama:7b',
            'deepseek-coder:6.7b',
            'qwen2.5-coder:7b',
            'mistral:7b',
        ]
    })

def snippets_view(request):
    return render(request, 'snippets.html')

def pr_review_view(request):
    return render(request, 'pr_review.html')

def settings_view(request):
    return render(request, 'settings.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check),
    # Frontend pages
    path('', chat_view, name='chat'),
    path('models/', models_view, name='models'),
    path('snippets/', snippets_view, name='snippets'),
    path('pr-review/', pr_review_view, name='pr_review'),
    path('settings/', settings_view, name='settings'),
    # API
    path('api/assistant/', include('apps.assistant.urls')),
    path('api/snippets/', include('apps.snippets.urls')),
]