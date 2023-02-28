from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Follow, User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "pk",
        "id",
        "username",
        "password",
        "email",
        "first_name",
        "last_name",
    )
    list_display_links = ("username", "first_name", "last_name")
    list_filter = ("first_name", "email")
    search_fields = (
        "username",
        "email",
    )
    empty_value_display = "-пусто-"
