from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Task(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_IN_PROGRESS, _('In progress')),
        (STATUS_COMPLETED, _('Completed')),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
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
    chat_id = models.BigIntegerField(unique=True, null=True, blank=True)
    temp_token = models.CharField(max_length=32, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} – {self.chat_id}"