import re
import unicodedata

from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _

max_username_length = settings.MAX_USERNAME_LENGTH
max_password_length = settings.MAX_PASSWORD_LENGTH
max_email_length = settings.MAX_EMAIL_LENGTH


class User(AbstractUser):
    username = models.CharField(
        verbose_name="Логин",
        max_length=max_username_length,
        unique=True,
        help_text=(f"Максимум {max_username_length} символов."),
    )
    password = models.CharField(
        verbose_name=_("Пароль"),
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
    active = models.BooleanField(
        verbose_name="Активирован",
        default=True,
    )
    USERNAME_FIELD = "username"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self) -> str:
        return f"{self.username}: {self.email}"

    @classmethod
    def normalize_email(cls, email: str) -> str:
        if not isinstance(email, str) or not re.match(
            r"[^@]+@[^@]+\.[^@]+", email
        ):
            raise ValueError(f"{email} is not a valid email address")
        email_name, domain_part = email.strip().rsplit("@", 1)
        return email_name.lower() + "@" + domain_part.lower()

    @classmethod
    def normalize_username(cls, username: str) -> str:
        return unicodedata.normalize("NFKC", username).capitalize()

    def __normalize_human_names(self, name: str) -> str:
        return " ".join([word.capitalize() for word in name.split()])

    def clean(self) -> None:
        self.first_name = self.__normalize_human_names(self.first_name)
        self.last_name = self.__normalize_human_names(self.last_name)
        super().clean()


class Subscribe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        related_name="subscribers",
        help_text="Выберите автора для подписки",
        on_delete=CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name="Подписчики",
        related_name="subscriptions",
        help_text="Выберите пользователя для подписки",
        on_delete=CASCADE,
    )
    date_added = models.DateTimeField(
        verbose_name="Дата создания подписки",
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.author.username}"
