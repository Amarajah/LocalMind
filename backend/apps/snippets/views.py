import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Snippet

logger = logging.getLogger(__name__)

EXTENSION_MAP = {
    'python': 'py', 'javascript': 'js', 'typescript': 'ts',
    'php': 'php', 'java': 'java', 'go': 'go', 'rust': 'rs',
    'sql': 'sql', 'bash': 'sh', 'other': 'txt',
}

@require_http_methods(['GET'])
def list_snippets(request):
    snippets = Snippet.objects.all()
    search = request.GET.get('q', '')
    if search:
        snippets = snippets.filter(title__icontains=search)
    return JsonResponse({
        'success': True,
        'snippets': [{
            'id': s.id,
            'title': s.title,
            'language': s.language,
            'task_mode': s.task_mode,
            'source_code': s.source_code,
            'created_at': s.created_at.isoformat(),
            'preview': s.content[:200],
        } for s in snippets]
    })

@csrf_exempt
@require_http_methods(['POST'])
def create_snippet(request):
    try:
        data = json.loads(request.body)
        snippet = Snippet.objects.create(
            title=data.get('title', 'Untitled'),
            language=data.get('language', 'other'),
            content=data.get('content', ''),
            source_code=data.get('source_code', ''),
            task_mode=data.get('task_mode', 'chat'),
        )
        return JsonResponse({'success': True, 'id': snippet.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(['GET', 'PATCH', 'DELETE'])
def snippet_detail(request, pk):
    try:
        snippet = Snippet.objects.get(pk=pk)
    except Snippet.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'snippet': {
            'id': snippet.id, 'title': snippet.title,
            'language': snippet.language, 'content': snippet.content, 'source_code': snippet.source_code,
            'task_mode': snippet.task_mode, 'created_at': snippet.created_at.isoformat(),
        }})
    elif request.method == 'PATCH':
        data = json.loads(request.body)
        if 'title' in data:
            snippet.title = data['title']
            snippet.save()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        snippet.delete()
        return JsonResponse({'success': True})

@require_http_methods(['GET'])
def export_snippet(request, pk):
    try:
        snippet = Snippet.objects.get(pk=pk)
    except Snippet.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
    ext = EXTENSION_MAP.get(snippet.language, 'txt')
    response = HttpResponse(snippet.source_code or snippet.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{snippet.title}.{ext}"'
    return response