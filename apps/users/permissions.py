from rest_framework import permissions


def is_admin_user(user):
    return bool(
        user
        and user.is_authenticated
        and (user.role == 'admin' or user.is_staff or user.is_superuser)
    )


def can_access_user(request_user, target_user):
    return is_admin_user(request_user) or request_user == target_user


class IsAdminUserRole(permissions.BasePermission):
    message = 'Admin privileges are required for this action.'

    def has_permission(self, request, view):
        return is_admin_user(request.user)
