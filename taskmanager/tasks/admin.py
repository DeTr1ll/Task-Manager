"""Admin configuration for the tasks app."""

from django.contrib import admin
from .models import Task, Tag

# Register Task and Tag models to appear in the Django admin interface
admin.site.register(Task)
admin.site.register(Tag)
