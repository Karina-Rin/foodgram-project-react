from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "pk",
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "last_login",
        "is_staff",
        "is_superuser",
    )
    list_display_links = ("username", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "first_name", "email")
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    empty_value_display = "-пусто-"
