from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    email = models.EmailField(
        'email address',
        max_length=254,
        unique=True,
    )
    avatar = models.ImageField(
        upload_to='user_avatar/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique follow',
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Вы не можете подписываться на самого себя')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
