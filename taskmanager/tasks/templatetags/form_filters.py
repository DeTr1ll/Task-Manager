"""Custom template filters for form rendering."""

from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Add a CSS class to a form field widget.

    Args:
        field (django.forms.BoundField): The form field to modify.
        css_class (str): The CSS class to add.

    Returns:
        django.forms.Widget: The form field rendered with the specified CSS class.
    """
    return field.as_widget(attrs={"class": css_class})
