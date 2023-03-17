from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

max_username_length = settings.MAX_USERNAME_LENGTH
max_password_length = settings.MAX_PASSWORD_LENGTH
max_email_length = settings.MAX_EMAIL_LENGTH


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Логин",
        max_length=max_username_length,
        unique=True,
        db_index=True,
        help_text=(f"Максимум {max_username_length} символов."),
    )
    password = models.CharField(
        verbose_name="Пароль",
        max_length=max_password_length,
        help_text=(f"Максимум {max_password_length} символов."),
    )
    email = models.EmailField(
        verbose_name="Адрес электронной почты",
        max_length=max_email_length,
        unique=True,
        db_index=True,
        help_text=(f"Максимум {max_email_length} символов."),
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=max_username_length,
        help_text=(f"Максимум {max_username_length} символов."),
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=max_username_length,
        help_text=(f"Максимум {max_username_length} символов."),
    )

    USERNAME_FIELD = "username"

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
        return self.username
