"""Custom template filters for language URL handling."""

import re
from django import template

register = template.Library()


@register.filter
def replace_language_prefix(path, lang_code):
    """
    Replace or add the language prefix in a given URL path.

    Args:
        path (str): Original URL path.
        lang_code (str): Language code to insert (e.g., 'en', 'uk', 'ru').

    Returns:
        str: Updated URL path with the specified language prefix.
    """
    pattern = r'^/(en|uk|ru)(/|$)'

    if re.match(pattern, path):
        return re.sub(pattern, f'/{lang_code}/', path)
    else:
        if path == '/':
            return f'/{lang_code}/'
        return f'/{lang_code}{path}'
