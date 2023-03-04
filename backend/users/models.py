from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint

USERNAME_FIELD = "username"


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Логин",
        max_length=settings.MAX_USERNAME_LENGTH,
        unique=True,
        db_index=True,
        help_text="Обязательное поле. f'Максимум {MAX_USERNAME_LENGTH} символов.'",
    )
    password = models.CharField(
        verbose_name="Пароль",
        max_length=settings.MAX_PASSWORD_LENGTH,
        help_text="Обязательное поле. f'Максимум {MAX_PASSWORD_LENGTH} символов.'",
    )
    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True,
        db_index=True,
        help_text="Обязательное поле. f'Максимум {MAX_EMAIL_LENGTH} символов.'",
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=settings.MAX_USERNAME_LENGTH,
        help_text="Обязательное поле. f'Максимум {MAX_USERNAME_LENGTH} символов.'",
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=settings.MAX_USERNAME_LENGTH,
        help_text="Обязательное поле. f'Максимум {MAX_USERNAME_LENGTH} символов.'",
    )

    class Meta:
        ordering = ("username",)
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [
            models.UniqueConstraint(
                fields=("username", "email"), name="unique_username_email"
            )
        ]

    def __str__(self):
        return f"{self.username}, {self.email}"


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
        help_text="Выберите пользователя для подписки",
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
        help_text="Выберите автора для подписки",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            UniqueConstraint(
                fields=["user", "following"], name="follow_unique"
            )
        ]

    def __str__(self):
        return self.user.username
