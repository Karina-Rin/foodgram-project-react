from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin
from users.models import Subscribe, User


@register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "active",
    )
    fields = (
        ("active",),
        (
            "username",
            "email",
        ),
        (
            "first_name",
            "last_name",
        ),
    )
    fieldsets = []

    search_fields = (
        "username",
        "email",
    )
    list_filter = (
        "active",
        "first_name",
        "email",
    )
    save_on_top = True


@register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
