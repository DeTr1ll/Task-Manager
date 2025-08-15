"""Models for the tasks app."""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Task(models.Model):
    """
    Model representing a Task.

    Attributes:
        STATUS_PENDING: Task is pending.
        STATUS_IN_PROGRESS: Task is in progress.
        STATUS_COMPLETED: Task is completed.
    """

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
        default=STATUS_PENDING,
    )
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the string representation of the task."""
        return self.title


class Tag(models.Model):
    """
    Model representing a Tag associated with tasks.

    Attributes:
        name: The name of the tag.
        user: The user who created the tag.
        tasks: Many-to-many relationship with Task model.
    """

    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tasks = models.ManyToManyField('Task', related_name='tags')

    def __str__(self):
        """Return the string representation of the tag."""
        return self.name
