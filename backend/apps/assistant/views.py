import json
import logging
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .ollama_client import list_models, pull_model, delete_model, get_system_stats
from .models import AppSettings

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def list_models_view(request):
    result = list_models()
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(['POST'])
def pull_model_view(request):
    try:
        data = json.loads(request.body)
        model_name = data.get('model_name', '').strip()
        if not model_name:
            return JsonResponse({'success': False, 'error': 'model_name is required'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    def progress_stream():
        for progress in pull_model(model_name):
            yield f"data: {json.dumps(progress)}\n\n"
        yield "data: {\"status\": \"complete\"}\n\n"

    response = StreamingHttpResponse(
        progress_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@csrf_exempt
@require_http_methods(['POST'])
def delete_model_view(request):
    try:
        data = json.loads(request.body)
        model_name = data.get('model_name', '').strip()
        if not model_name:
            return JsonResponse({'success': False, 'error': 'model_name is required'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    result = delete_model(model_name)
    status_code = 200 if result['success'] else 400
    return JsonResponse(result, status=status_code)


@require_http_methods(['GET'])
def system_stats_view(request):
    result = get_system_stats()
    return JsonResponse(result)


@require_http_methods(['GET'])
def get_settings_view(request):
    settings_qs = AppSettings.objects.all()
    settings_dict = {s.key: s.value for s in settings_qs}

    defaults = {
        'default_model': 'gemma4:e2b',
        'default_mode': 'chat',
        'verbosity': 'detailed',
        'theme': 'dark',
    }
    defaults.update(settings_dict)
    return JsonResponse({'success': True, 'settings': defaults})


@csrf_exempt
@require_http_methods(['POST'])
def update_settings_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    allowed_keys = {'default_model', 'default_mode', 'verbosity', 'theme', 'ollama_host'}
    updated = {}

    for key, value in data.items():
        if key in allowed_keys:
            AppSettings.objects.update_or_create(
                key=key,
                defaults={'value': str(value)}
            )
            updated[key] = value

    return JsonResponse({'success': True, 'updated': updated})