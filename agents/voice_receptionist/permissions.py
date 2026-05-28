"""
voice_receptionist/permissions.py
----------------------------------
DRF custom permission classes using Firebase role from UserProfile.
"""

from rest_framework.permissions import BasePermission


def _get_role(request):
    """Safely retrieve the user's role from their UserProfile."""
    try:
        return request.user.voice_profile.role
    except AttributeError:
        return None


class IsFirebaseAdmin(BasePermission):
    """Grants access only to users with role='admin'."""
    message = "Admin role required."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and _get_role(request) == "admin"


class IsFirebaseAdminOrManager(BasePermission):
    """Grants access to admin or manager roles."""
    message = "Admin or Manager role required."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and _get_role(request) in ("admin", "manager")


class IsFirebaseAuthenticated(BasePermission):
    """Grants access to any authenticated Firebase user (any role)."""
    message = "Authentication required."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
