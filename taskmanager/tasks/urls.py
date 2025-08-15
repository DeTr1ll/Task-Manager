"""URL configuration for the tasks app, including REST API routes and standard views."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# DRF router for TaskViewSet
router = DefaultRouter()
router.register(r'api', views.TaskViewSet, basename='task')

urlpatterns = [
    # Standard task views
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('delete/<int:task_id>/', views.task_delete, name='task_delete'),
    path('edit/<int:task_id>/', views.task_edit, name='task_edit'),
    path(
        '<int:task_id>/update-status/',
        views.task_update_status_ajax,
        name='task_update_status_ajax'
    ),
    path('tags/autocomplete/', views.tag_autocomplete, name='tag_autocomplete'),

    # Include DRF router URLs
    path('', include(router.urls)),
]
