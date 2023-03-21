import re
import unicodedata

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db.models import (CASCADE, BooleanField, CharField,
                              CheckConstraint, DateTimeField, EmailField, F,
                              ForeignKey, Model, Q, UniqueConstraint)
from django.db.models.functions import Length
from django.utils.translation import gettext_lazy as _

CharField.register_lookup(Length)

max_username_length = settings.MAX_USERNAME_LENGTH
max_password_length = settings.MAX_PASSWORD_LENGTH
max_email_length = settings.MAX_EMAIL_LENGTH


class User(AbstractUser):
    username = CharField(
        verbose_name="Логин",
        max_length=max_username_length,
        unique=True,
        db_index=True,
        help_text=(f"Максимум {max_username_length} символов."),
        validators=(
            MinLengthValidator(
                min_len=max_username_length,
                field="username",
            ),
            RegexValidator(field="username"),
        ),
    )
    password = CharField(
        verbose_name=_("Пароль"),
        max_length=max_password_length,
        help_text=(f"Максимум {max_password_length} символов."),
    )
    email = EmailField(
        verbose_name="Адрес электронной почты",
        max_length=max_email_length,
        unique=True,
        db_index=True,
        help_text=(f"Максимум {max_email_length} символов."),
    )
    first_name = CharField(
        verbose_name="Имя",
        max_length=max_username_length,
        help_text=(f"Максимум {max_username_length} символов."),
        validators=(
            RegexValidator(
                first_regex="[^а-яёА-ЯЁ -]+",
                second_regex="[^a-zA-Z -]+",
                field="Имя",
            ),
        ),
    )
    last_name = CharField(
        verbose_name="Фамилия",
        max_length=max_username_length,
        help_text=(f"Максимум {max_username_length} символов."),
        validators=(
            RegexValidator(
                first_regex="[^а-яёА-ЯЁ -]+",
                second_regex="[^a-zA-Z -]+",
                field="Фамилия",
            ),
        ),
    )
    active = BooleanField(
        verbose_name="Активирован",
        default=True,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)
        constraints = (
            CheckConstraint(
                check=Q(username__length__gte=max_username_length),
                name="\nИмя пользователя слишком короткое\n",
            ),
        )

    def __str__(self) -> str:
        return f"{self.username}: {self.email}"

    @classmethod
    def normalize_email(cls, email: str) -> str:
        if not isinstance(email, str) or not re.match(
            r"[^@]+@[^@]+\.[^@]+", email
        ):
            raise ValueError(
                f"{email} это недопустимый адрес электронной почты"
            )
        email_name, domain_part = email.strip().rsplit("@", 1)
        return email_name.lower() + "@" + domain_part

    @classmethod
    def normalize_username(cls, username: str) -> str:
        if not username:
            return ""
        normalized = unicodedata.normalize("NFKC", username)
        return cls.capitalize(normalized)

    def __normalize_human_names(self, name: str) -> str:
        return " ".join([word.capitalize() for word in name.split()])

    def clean(self) -> None:
        self.first_name = self.__normalize_human_names(self.first_name)
        self.last_name = self.__normalize_human_names(self.last_name)
        super().clean()


class Subscribe(Model):
    author = ForeignKey(
        verbose_name="Автор рецепта",
        related_name="subscribers",
        help_text="Выберите автора для подписки",
        to=User,
        on_delete=CASCADE,
    )
    user = ForeignKey(
        verbose_name="Подписчики",
        related_name="subscriptions",
        help_text="Выберите пользователя для подписки",
        to=User,
        on_delete=CASCADE,
    )
    date_added = DateTimeField(
        verbose_name="Дата создания подписки",
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            UniqueConstraint(
                fields=("author", "user"),
                name="\nПовторная подписка\n",
            ),
            CheckConstraint(
                check=~Q(author=F("user")),
                name="\nНельзя подписаться на самого себя\n",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.author.username}"
