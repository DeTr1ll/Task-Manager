from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('delete/<int:id>/', views.task_delete, name='task_delete'),
    path('edit/<int:id>/', views.task_edit, name='task_edit'),
    path('<int:id>/update-status/', views.task_update_status_ajax, name='task_update_status_ajax'),
    path('tags/autocomplete/', views.tag_autocomplete, name='tag_autocomplete'),
]