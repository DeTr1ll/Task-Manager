"""
Forms for the Task Manager application.

Includes TaskForm for creating and editing Task instances,
with support for a custom tags input field.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Task


class TaskForm(forms.ModelForm):
    """
    Form for creating and editing Task instances, including a custom
    field for entering tags as a comma-separated string.
    """

    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'tags-input',
            'class': 'form-control',
            'placeholder': _('e.g. work, urgent'),
            'autocomplete': 'off',
        }),
        label=_("Tags"),
    )

    class Meta:
        """
        Meta class for TaskForm.
        
        Attributes:
            model: The Task model associated with this form.
            fields: List of model fields included in the form.
            labels: Human-readable labels for the form fields.
            widgets: Custom widgets for rendering the form fields.
        """
        model = Task
        fields = ['title', 'description', 'status', 'due_date', 'due_time']
        labels = {
            'title': _('Task Title'),
            'description': _('Description'),
            'status': _('Status'),
            'due_date': _('Due Date'),
            'due_time': _('Due Time'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'due_time': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time'}
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and optionally set the initial value for
        the tags_input field if editing an existing Task instance.

        Args:
            user: The currently authenticated user (optional, passed via kwargs).
            *args: Variable length argument list for parent form.
            **kwargs: Arbitrary keyword arguments for parent form.
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )
