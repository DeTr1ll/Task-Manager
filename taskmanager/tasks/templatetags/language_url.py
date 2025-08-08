from django import template
import re

register = template.Library()

@register.filter
def replace_language_prefix(path, lang_code):
    # Паттерн для языкового префикса: /en/, /uk/, /ru/
    pattern = r'^/(en|uk|ru)(/|$)'

    # Если путь начинается с языкового префикса — заменяем на новый
    if re.match(pattern, path):
        return re.sub(pattern, f'/{lang_code}/', path)
    else:
        # Иначе добавляем префикс (если это не корень)
        if path == '/':
            return f'/{lang_code}/'
        else:
            return f'/{lang_code}{path}'
