from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.settings import (ADMIN, MODERATOR, MAX_LENGTH_ROLE,
                                MAX_LENGTH_USER)
#from .validators import validate_username_not_me, validate_username_symbols


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        ADMIN = 'admin', 'Администратор'
        MODERATOR = 'moderator', 'Модератор'

    role = models.CharField(
        verbose_name='Роль',
        choices=Role.choices,
        default=Role.USER,
        max_length=MAX_LENGTH_ROLE,
        blank=True
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_USER,
        validators=[], #[validate_username_not_me, validate_username_symbols],
        unique=True
    )
    bio = models.TextField(verbose_name='Биография', blank=True)
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_USER,
        blank=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_USER,
        blank=True
    )

    @property
    def is_admin(self):
        return (self.role == ADMIN
                or self.is_staff or self.is_superuser)

    @property
    def is_moderator(self):
        return (self.role == MODERATOR
                or self.is_staff or self.is_superuser)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username
