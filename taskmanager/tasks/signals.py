"""Signals for automatically cleaning up unused tags in tasks app."""

from django.db.models import Count
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from .models import Task, Tag


def delete_unused_tags():
    """
    Delete tags that are not associated with any tasks.
    """
    unused_tags = Tag.objects.annotate(
        task_count=Count('tasks'),
    ).filter(task_count=0)
    unused_tags.delete()


@receiver(m2m_changed, sender=Task.tags.through)
def tags_changed(sender, instance, action, **kwargs):
    """
    Signal handler triggered when Task.tags ManyToMany field changes.

    Deletes unused tags after tasks are updated.
    """
    if action in ['post_remove', 'post_clear', 'post_add']:
        delete_unused_tags()


@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
    """
    Signal handler triggered when a Task instance is deleted.

    Ensures unused tags are removed after task deletion.
    """
    delete_unused_tags()
