from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import BusinessInstance, BusinessEmployee, TenantModule


def business_required(owner_only=False):
    """
    Decorator for hub views that need a valid business accessible to the user.

    Sets request.current_business if not already set by middleware.
    If owner_only=True, only the business owner is allowed.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, slug, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect('/accounts/login/')

            try:
                biz = BusinessInstance.objects.get(slug=slug, is_active=True)
            except BusinessInstance.DoesNotExist:
                return HttpResponseForbidden("Business not found.")

            is_owner = biz.owner == request.user
            is_employee = BusinessEmployee.objects.filter(
                business=biz, user=request.user, is_active=True
            ).exists()

            if not (is_owner or is_employee):
                return HttpResponseForbidden("You do not have access to this business.")

            if owner_only and not is_owner:
                return HttpResponseForbidden("Only the business owner can perform this action.")

            request.current_business = biz
            request.is_business_owner = is_owner
            return view_func(request, slug, *args, **kwargs)
        return wrapper
    return decorator


def module_required(module_id):
    """
    Decorator for module-specific views.
    Ensures the business has the given module active.
    Must be used after @business_required (relies on request.current_business).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, slug, *args, **kwargs):
            biz = getattr(request, 'current_business', None)
            if not biz:
                return HttpResponseForbidden("Business context missing.")

            has_module = TenantModule.objects.filter(
                business=biz,
                module__module_id=module_id,
                is_active=True,
            ).exists()

            if not has_module:
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.warning(
                    request,
                    f"The '{module_id}' module is not active for this business. "
                    "Activate it from the Module Store."
                )
                return redirect('hub:hub_module_store', slug=slug)

            return view_func(request, slug, *args, **kwargs)
        return wrapper
    return decorator
