from django.contrib.auth.models import User
from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=[
            ('pending', 'В очікуванні'), 
            ('in_progress', 'Виконується'), 
            ('completed', 'Виконано')
        ], default='pending')
        
    due_date = models.DateField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Tag(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tasks = models.ManyToManyField('Task', related_name='tags')
    
    def __str__(self):
        return self.name

class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Telegram"