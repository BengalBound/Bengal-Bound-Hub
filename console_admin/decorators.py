from django.contrib.auth.decorators import user_passes_test

def console_user_required(function=None, redirect_field_name=None, login_url='/accounts/login/'):
    """
    Decorator for Console views that checks the user is authenticated and has
    the 'console_user' role. Workspace Admins and other roles will be redirected
    to the Console login — enforcing strict separation between subdomains.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role in ('console_user', 'affiliate'),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
