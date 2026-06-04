from django.db import models


class Snippet(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('php', 'PHP'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('sql', 'SQL'),
        ('bash', 'Bash'),
        ('other', 'Other'),
    ]

    TASK_MODE_CHOICES = [
        ('explain', 'Explain Code'),
        ('test', 'Write Tests'),
        ('docstring', 'Generate Docstrings'),
        ('review', 'Code Review'),
        ('chat', 'Chat'),
        ('pr_review', 'PR Review'),
    ]

    title = models.CharField(max_length=255)
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default='python')
    content = models.TextField()
    source_code = models.TextField(blank=True, default='')
    task_mode = models.CharField(max_length=50, choices=TASK_MODE_CHOICES, default='chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.language})'