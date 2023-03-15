from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        "pk",
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "custom_field",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    def custom_field(self, obj):
        return obj.profile.custom_field

    custom_field.short_description = "Пользовательское поле"
