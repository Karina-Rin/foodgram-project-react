from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


class UserAdmin(UserAdmin):
    list_display = (
        "pk",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "last_login",
    )
    list_editable = ("is_active",)
    search_fields = ("username", "email")
    empty_value_display = "-пусто-"


admin.site.register(User, UserAdmin)
