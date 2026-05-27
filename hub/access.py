from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from .models import BusinessEmployee, ACCESS_LEVEL_MAP


def get_member(biz, user):
    return BusinessEmployee.objects.filter(business=biz, user=user, is_active=True).first()


def get_access_level(biz, user):
    if biz.owner == user:
        return 10
    member = get_member(biz, user)
    if not member:
        return 0
    if member.role == 'custom' and member.custom_position_id:
        return member.custom_position.access_level
    return ACCESS_LEVEL_MAP.get(member.role, 2)


def get_member_context(biz, user):
    """Return (member_or_None, access_level, is_owner) for template context."""
    is_owner = biz.owner == user
    member = get_member(biz, user)
    if is_owner:
        level = 10
    elif member:
        if member.role == 'custom' and member.custom_position_id:
            level = member.custom_position.access_level
        else:
            level = ACCESS_LEVEL_MAP.get(member.role, 2)
    else:
        level = 0
    return member, level, is_owner


def require_access(min_level):
    """Decorator factory: denies access if user's level < min_level."""
    def decorator(view_func):
        @login_required(login_url='/accounts/login/')
        @wraps(view_func)
        def wrapper(request, slug, *args, **kwargs):
            from hub.views import _get_business_for_user
            biz = _get_business_for_user(slug, request.user)
            if not biz:
                return HttpResponseForbidden()
            level = get_access_level(biz, request.user)
            if level < min_level:
                return HttpResponseForbidden("You don't have permission to access this area.")
            return view_func(request, slug, *args, **kwargs)
        return wrapper
    return decorator


# Shorthand decorators
require_employee = require_access(2)      # any staff member
require_manager = require_access(6)       # manager and above
require_audit_manager = require_access(7) # audit_manager and above
require_executive = require_access(9)     # CEO/owner only
