from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin
from users.models import User


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
