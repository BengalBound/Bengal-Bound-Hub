from django.contrib.auth.decorators import user_passes_test

def workspace_admin_required(function=None, redirect_field_name=None, login_url='/accounts/login/'):
    """
    Decorator for views that checks that the user is logged in and has an
    internal workspace role.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_superuser or getattr(u, 'is_workspace_user', False)),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
