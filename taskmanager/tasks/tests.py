from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from tasks.models import Task, Tag
from tasks.forms import TaskForm
from django.urls import reverse


# ------------------------------
# Model tests
# ------------------------------
class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.tag = Tag.objects.create(name='tag1', user=self.user)
        self.task = Task.objects.create(
            title='Test Task', description='Test description', user=self.user
        )
        self.task.tags.add(self.tag)

    def test_task_str(self):
        self.assertEqual(str(self.task), 'Test Task')

    def test_tag_str(self):
        self.assertEqual(str(self.tag), 'tag1')

    def test_task_tag_relationship(self):
        self.assertIn(self.tag, self.task.tags.all())


# ------------------------------
# Form tests
# ------------------------------
class TaskFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        self.tag1 = Tag.objects.create(name='tag1', user=self.user)
        self.tag2 = Tag.objects.create(name='tag2', user=self.user)

    def test_task_form_valid(self):
        form_data = {
            'title': 'Task Form Test',
            'description': 'desc',
            'tags_input': 'tag1, tag2',
            'due_date': '2025-08-20',
            'status': 'pending',
        }
        form = TaskForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())


# ------------------------------
# HTML view tests
# ------------------------------
class TaskViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        self.client = Client()
        self.client.login(username='user', password='pass')
        self.task = Task.objects.create(title='Test Task', description='desc', user=self.user)
        self.lang_prefix = '/en'  # язык по умолчанию

    def test_task_list_view(self):
        response = self.client.get(f'{self.lang_prefix}/')
        self.assertEqual(response.status_code, 200)

    def test_task_create_view(self):
        data = {'title': 'Created Task', 'description': 'desc', 'tags_input': '', 'status': 'pending'}
        response = self.client.post(f'{self.lang_prefix}/create/', data)
        self.assertTrue(Task.objects.filter(title='Created Task', user=self.user).exists())

    def test_task_edit_view(self):
        data = {'title': 'Updated Task', 'description': 'desc', 'tags_input': '', 'status': 'pending'}
        response = self.client.post(f'{self.lang_prefix}/edit/{self.task.id}/', data)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')


# ------------------------------
# API tests
# ------------------------------
class TaskAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.tag = Tag.objects.create(name='tag1', user=self.user)
        self.task = Task.objects.create(title='API Task', description='desc', user=self.user)
        self.task.tags.add(self.tag)
        self.lang_prefix = '/en'  # язык по умолчанию

    def test_api_list_tasks(self):
        response = self.client.get(f'{self.lang_prefix}/api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_create_task(self):
        data = {'title': 'New API Task', 'description': 'desc', 'tags': [self.tag.id]}
        response = self.client.post(f'{self.lang_prefix}/api/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Task.objects.filter(title='New API Task', user=self.user).exists())

    def test_api_update_task(self):
        data = {'title': 'Updated API Task'}
        response = self.client.patch(f'{self.lang_prefix}/api/{self.task.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated API Task')

    def test_api_delete_task(self):
        response = self.client.delete(f'{self.lang_prefix}/api/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
