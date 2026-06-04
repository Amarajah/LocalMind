import json
import logging
import time
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .prompts import get_system_prompt
from .models import ModelUsageLog, AppSettings

logger = logging.getLogger(__name__)


@sync_to_async
def get_setting(key, default):
    try:
        setting = AppSettings.objects.get(key=key)
        return setting.value
    except AppSettings.DoesNotExist:
        return default


@sync_to_async
def save_usage_log(model_name, task_mode, prompt_chars, response_chars, duration_ms):
    ModelUsageLog.objects.create(
        model_name=model_name,
        task_mode=task_mode,
        prompt_char_count=prompt_chars,
        response_char_count=response_chars,
        duration_ms=duration_ms,
    )


class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.streaming = False

    async def connect(self):
        await self.accept()
        logger.info('WebSocket connection established')
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'LocalMind WebSocket ready',
        }))

    async def disconnect(self, close_code):
        logger.info(f'WebSocket disconnected: {close_code}')
        self.streaming = False

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON received')
            return

        msg_type = data.get('type')

        if msg_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return

        if msg_type == 'stop':
            self.streaming = False
            await self.send(text_data=json.dumps({'type': 'stopped'}))
            return

        if msg_type == 'query':
            await self.handle_query(data)
            return

        await self.send_error(f'Unknown message type: {msg_type}')

    async def handle_query(self, data):
        mode = data.get('mode', 'chat')
        code = data.get('code', '')
        language = data.get('language', '')
        verbosity = data.get('verbosity', 'detailed')
        conversation_history = data.get('conversation_history', [])

        model_name = data.get('model') or await get_setting('default_model', 'gemma4:e2b')

        if not code and not conversation_history:
            await self.send_error('No code or message provided')
            return

        # Build user message
        if mode == 'chat':
            user_content = code
        elif mode in ('explain', 'review', 'docstring', 'test'):
            lang_hint = f'Language: {language}\n\n' if language else ''
            user_content = f'{lang_hint}```\n{code}\n```'
        elif mode == 'pr_review':
            user_content = f'Please review this PR diff:\n\n```diff\n{code}\n```'
        else:
            user_content = code

        messages = list(conversation_history)
        messages.append({'role': 'user', 'content': user_content})
        system_prompt = get_system_prompt(mode, verbosity)

        self.streaming = True
        await self.send(text_data=json.dumps({'type': 'stream_start'}))

        start_time = time.time()
        response_text = ''

        try:
            import ollama
            from django.conf import settings as django_settings

            client = ollama.Client(host=django_settings.OLLAMA_HOST)

            full_messages = []
            if system_prompt:
                full_messages.append({'role': 'system', 'content': system_prompt})
            full_messages.extend(messages)

            loop = asyncio.get_event_loop()
            queue = asyncio.Queue()

            def stream_to_queue():
                try:
                    for chunk in client.chat(
                        model=model_name,
                        messages=full_messages,
                        stream=True,
                    ):
                        if not self.streaming:
                            break
                        if chunk.message and chunk.message.content:
                            loop.call_soon_threadsafe(
                                queue.put_nowait,
                                {'type': 'token', 'content': chunk.message.content}
                            )
                    loop.call_soon_threadsafe(queue.put_nowait, {'type': 'done'})
                except Exception as e:
                    loop.call_soon_threadsafe(
                        queue.put_nowait,
                        {'type': 'error', 'message': str(e)}
                    )

            # Start streaming in background thread
            loop.run_in_executor(None, stream_to_queue)

            # Read tokens from queue and forward to WebSocket
            while True:
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    await self.send_error('Stream timed out after 120 seconds')
                    break

                if chunk['type'] == 'token':
                    response_text += chunk['content']
                    await self.send(text_data=json.dumps({
                        'type': 'token',
                        'content': chunk['content'],
                    }))

                elif chunk['type'] == 'error':
                    await self.send_error(chunk['message'])
                    return

                elif chunk['type'] == 'done':
                    break

        except Exception as e:
            logger.error(f'Streaming error: {e}')
            await self.send_error(str(e))
            return

        duration_ms = int((time.time() - start_time) * 1000)

        await save_usage_log(
            model_name=model_name,
            task_mode=mode,
            prompt_chars=len(user_content),
            response_chars=len(response_text),
            duration_ms=duration_ms,
        )

        await self.send(text_data=json.dumps({
            'type': 'done',
            'total_chars': len(response_text),
            'duration_ms': duration_ms,
            'model': model_name,
        }))

        self.streaming = False

    async def send_error(self, message: str):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
        }))