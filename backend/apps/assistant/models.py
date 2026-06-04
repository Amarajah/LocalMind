from django.db import models


class ModelUsageLog(models.Model):
    model_name = models.CharField(max_length=100)
    task_mode = models.CharField(max_length=50)
    prompt_char_count = models.IntegerField(default=0)
    response_char_count = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.model_name} | {self.task_mode} | {self.created_at}'


class AppSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'App Settings'

    def __str__(self):
        return f'{self.key}: {self.value}'