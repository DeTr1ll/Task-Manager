from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver
from .models import Task, Tag
from django.db.models import Count

def delete_unused_tags():
    unused_tags = Tag.objects.annotate(task_count=Count('tasks')).filter(task_count=0)
    unused_tags.delete()

@receiver(m2m_changed, sender=Task.tags.through)
def tags_changed(sender, instance, action, **kwargs):
    if action in ['post_remove', 'post_clear', 'post_add']:
        delete_unused_tags()

@receiver(post_delete, sender=Task)
def task_deleted(sender, instance, **kwargs):
    delete_unused_tags()
