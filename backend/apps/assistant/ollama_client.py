import logging
import psutil
import ollama
from django.conf import settings

logger = logging.getLogger(__name__)

def get_ollama_client():
    return ollama.Client(host=settings.OLLAMA_HOST)


def list_models():
    """Return all locally installed Ollama models."""
    try:
        client = get_ollama_client()
        response = client.list()
        models = []
        for model in response.models:
            models.append({
                'name': model.model,
                'size': model.size,
                'size_gb': round(model.size / (1024 ** 3), 2),
                'digest': model.digest,
                'modified_at': model.modified_at.isoformat() if model.modified_at else None,
                'details': {
                    'family': model.details.family if model.details else None,
                    'parameter_size': model.details.parameter_size if model.details else None,
                    'quantization_level': model.details.quantization_level if model.details else None,
                },
            })
        return {'success': True, 'models': models}
    except Exception as e:
        logger.error(f'Failed to list models: {e}')
        return {'success': False, 'error': str(e), 'models': []}


def pull_model(model_name: str):
    """
    Pull a model from Ollama registry.
    This is a generator — yields progress dicts as the pull progresses.
    """
    try:
        client = get_ollama_client()
        for progress in client.pull(model_name, stream=True):
            yield {
                'status': progress.status,
                'digest': progress.digest if progress.digest else None,
                'total': progress.total if progress.total else None,
                'completed': progress.completed if progress.completed else None,
            }
    except Exception as e:
        logger.error(f'Failed to pull model {model_name}: {e}')
        yield {'status': 'error', 'error': str(e)}


def delete_model(model_name: str):
    """Delete a locally installed model."""
    try:
        client = get_ollama_client()
        client.delete(model_name)
        return {'success': True, 'message': f'Model {model_name} deleted successfully'}
    except Exception as e:
        logger.error(f'Failed to delete model {model_name}: {e}')
        return {'success': False, 'error': str(e)}


def get_system_stats():
    """Return host system resource usage."""
    try:
        ram = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')

        # Check if Ollama is reachable
        try:
            client = get_ollama_client()
            client.list()
            ollama_status = 'online'
        except Exception:
            ollama_status = 'offline'

        return {
            'success': True,
            'ollama_status': ollama_status,
            'ollama_host': settings.OLLAMA_HOST,
            'ram': {
                'total_gb': round(ram.total / (1024 ** 3), 2),
                'used_gb': round(ram.used / (1024 ** 3), 2),
                'available_gb': round(ram.available / (1024 ** 3), 2),
                'percent': ram.percent,
            },
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
            },
            'disk': {
                'total_gb': round(disk.total / (1024 ** 3), 2),
                'used_gb': round(disk.used / (1024 ** 3), 2),
                'free_gb': round(disk.free / (1024 ** 3), 2),
                'percent': disk.percent,
            },
        }
    except Exception as e:
        logger.error(f'Failed to get system stats: {e}')
        return {'success': False, 'error': str(e)}


def chat_with_model(model_name: str, messages: list, system_prompt: str = None):
    """
    Stream a chat response from Ollama.
    This is a generator — yields text chunks as they arrive.
    messages format: [{'role': 'user'|'assistant', 'content': '...'}]
    """
    try:
        client = get_ollama_client()
        full_messages = []

        if system_prompt:
            full_messages.append({'role': 'system', 'content': system_prompt})

        full_messages.extend(messages)

        for chunk in client.chat(
            model=model_name,
            messages=full_messages,
            stream=True,
        ):
            if chunk.message and chunk.message.content:
                yield {
                    'type': 'token',
                    'content': chunk.message.content,
                }

        yield {'type': 'done'}

    except Exception as e:
        logger.error(f'Chat failed with model {model_name}: {e}')
        yield {'type': 'error', 'message': str(e)}