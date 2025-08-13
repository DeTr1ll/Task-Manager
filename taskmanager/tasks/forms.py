from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Task


class TaskForm(forms.ModelForm):
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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(tag.name for tag in self.instance.tags.all())
