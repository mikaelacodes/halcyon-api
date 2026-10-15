from rest_framework import permissions


def is_admin(user):
    if not (user and user.is_authenticated):
        return False
    profile = getattr(user, "profile", None)
    return bool(user.is_staff or (profile and profile.is_admin))


class IsAdminOrReadOnly(permissions.BasePermission):
    """Any authenticated user can read; only admins can write."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user)


class IsAdminOrCreateOnly(permissions.BasePermission):
    """Any authenticated user can read or create; only admins can update/delete."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS or request.method == "POST":
            return True
        return is_admin(request.user)
