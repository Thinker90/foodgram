import re

from django.core.exceptions import ValidationError

REGEX_FOR_USERNAME = r'^[\w.@+-]+\Z'


def validate_username_not_me(value):
    if value == 'me':
        raise ValidationError(f'Недопустимое имя пользователя {value}')


def validate_username_symbols(value):
    invalid_chars = [char for char in value
                     if not re.search(REGEX_FOR_USERNAME, char)]
    if invalid_chars:
        raise ValidationError('Имя пользователя может содержать только буквы, '
                              'цифры и знаки @ / . / + / - / _, некорректные '
                              f'символы: {invalid_chars}')
