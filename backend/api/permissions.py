from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAdminUser, IsAuthenticated)


class OwnerUserOrReadOnly(BasePermission):
    pass


class IsAuthorOrReadOnly(BasePermission):
    message = "Только автору разрешено вносить изменения."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsOwnerOrReadOnly(BasePermission):
    message = "Только владельцу разрешено вносить изменения."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user


class AdminOrReadOnly(BasePermission):
    message = "Только администраторам разрешено вносить изменения."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsAdminUser().has_permission(request, view)


class AuthorStaffOrReadOnly(BasePermission):
    message = "Только персоналу разрешено вносить изменения."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsAuthenticatedOrReadOnly(BasePermission):
    message = (
        "Только аутентифицированным пользователям разрешено вносить изменения."
    )

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsAuthenticated().has_permission(request, view)
