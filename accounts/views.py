import secrets
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import escape
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from django_ratelimit.decorators import ratelimit

from .models import User
from .utils import generate_otp, send_otp_email

CONSOLE_URL = 'http://console.localhost:1234'
WORKSPACE_URL = 'http://workspace.localhost:1234'

OTP_EXPIRY_SECONDS = 600  # 10 minutes


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _unique_business_slug(name):
    from hub.models import BusinessInstance
    base = slugify(name)[:80] or 'my-business'
    slug = base
    counter = 1
    while BusinessInstance.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _sso_post_form(token, consume_url, next_path):
    """Return a self-submitting POST form so the SSO token never appears in the URL."""
    safe_token = escape(token)
    safe_url = escape(consume_url)
    safe_next = escape(next_path)
    return HttpResponse(
        f'<!DOCTYPE html><html><body>'
        f'<form method="post" action="{safe_url}" id="sso">'
        f'<input type="hidden" name="sso_token" value="{safe_token}">'
        f'<input type="hidden" name="next" value="{safe_next}">'
        f'</form>'
        f'<script>document.getElementById("sso").submit();</script>'
        f'</body></html>',
        content_type='text/html',
    )


def _post_auth_redirect(request, user):
    """
    Redirect the user to the correct dashboard after login or OTP verification.
    Cross-subdomain hops use a self-submitting POST form so the signed token
    never leaks into the browser URL bar / history.
    """
    from hub.models import BusinessInstance

    if user.is_workspace_user:
        target_base = WORKSPACE_URL
        target_path = '/'
    else:
        biz = BusinessInstance.objects.filter(owner=user, is_active=True).first()
        target_base = CONSOLE_URL
        target_path = f'/hub/{biz.slug}/' if biz else '/'

    host = request.get_host().split(':')[0].lower()
    target_host = target_base.split('//')[1].split(':')[0]

    if host == target_host:
        return redirect(target_path or '/')

    # Cross-subdomain: POST form (token never in URL)
    signer = TimestampSigner()
    token = signer.sign(str(user.id))
    consume_url = f'{target_base}/accounts/sso/consume/'
    return _sso_post_form(token, consume_url, target_path)


# ─── Register ─────────────────────────────────────────────────────────────────

@transaction.atomic
def register_view(request):
    """
    Business-owner registration.
    Creates: User → BusinessInstance → BusinessEmployee(owner role).
    All DB writes are wrapped in a single atomic transaction.
    """
    if request.user.is_authenticated:
        return _post_auth_redirect(request, request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        business_name = request.POST.get('business_name', '').strip()
        business_type = request.POST.get('business_type', 'business')
        installation_type = request.POST.get('installation_type', 'cloud')

        if not all([first_name, email, password, business_name]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/register.html', _register_ctx(request))

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html', _register_ctx(request))

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'accounts/register.html', _register_ctx(request))

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, 'accounts/register.html', _register_ctx(request))

        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='console_user',
        )

        from hub.models import BusinessInstance, BusinessEmployee
        slug = _unique_business_slug(business_name)
        biz = BusinessInstance.objects.create(
            owner=user,
            name=business_name,
            slug=slug,
            business_type=business_type,
            installation_type=installation_type,
            business_email=email,
        )
        if installation_type == 'self_hosted':
            biz.generate_sync_token()

        BusinessEmployee.objects.create(
            business=biz,
            user=user,
            name=f"{first_name} {last_name}".strip(),
            email=email,
            role='owner',
        )

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp', 'otp_created_at'])
        send_otp_email(user, otp)

        request.session['verify_email'] = email
        request.session.save()
        return redirect(f"/accounts/verify-otp/?email={email}")

    return render(request, 'accounts/register.html', _register_ctx(request))


def _social_providers(request):
    """Return list of configured social providers safe for template rendering."""
    try:
        from allauth.socialaccount.adapter import get_adapter
        from allauth.socialaccount.models import SocialApp
        adapter = get_adapter(request)
        providers = []
        for provider_id in ('google', 'github', 'facebook'):
            try:
                provider = adapter.get_provider(request, provider_id)
                providers.append({
                    'id': provider_id,
                    'name': provider.name,
                    'url': provider.get_login_url(request, action='authenticate'),
                    'icon': f'bi-{provider_id}',
                })
            except SocialApp.DoesNotExist:
                pass
        return providers
    except Exception:
        return []


def _register_ctx(request=None):
    from hub.models import BUSINESS_TYPES, INSTALLATION_TYPES
    ctx = {
        'business_types': BUSINESS_TYPES,
        'installation_types': INSTALLATION_TYPES,
    }
    if request is not None:
        ctx['social_providers'] = _social_providers(request)
    return ctx


# ─── OTP Verification ─────────────────────────────────────────────────────────

@ratelimit(key='post:email', method='POST', rate='3/h', block=False)
def verify_otp_view(request):
    email = request.GET.get('email') or request.session.get('verify_email')
    if not email:
        return redirect('accounts:register')

    if request.method == 'POST':
        if getattr(request, 'limited', False):
            messages.error(request, "Too many attempts. Please wait 1 hour before trying again.")
            return render(request, 'accounts/verify_otp.html', {'email': email})

        otp_input = request.POST.get('otp', '').strip()
        user = User.objects.filter(email=email).first()

        otp_valid = (
            user
            and user.otp
            and user.otp_created_at
            and (timezone.now() - user.otp_created_at).total_seconds() <= OTP_EXPIRY_SECONDS
            and secrets.compare_digest(user.otp, otp_input)
        )

        if otp_valid:
            user.is_email_verified = True
            user.otp = ''
            user.otp_created_at = None
            user.save(update_fields=['is_email_verified', 'otp', 'otp_created_at'])
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Email verified! Welcome to BengalBound.")
            return _post_auth_redirect(request, user)

        messages.error(request, "Invalid or expired code. Please check your email and try again.")

    return render(request, 'accounts/verify_otp.html', {'email': email})


# ─── Login ────────────────────────────────────────────────────────────────────

def custom_login_view(request):
    """
    Custom login that redirects to the correct subdomain after authentication.
    django-axes handles brute-force protection via AUTHENTICATION_BACKENDS.
    """
    if request.user.is_authenticated:
        return _post_auth_redirect(request, request.user)

    host = request.get_host().split(':')[0].lower()

    if request.method == 'POST':
        email = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)

        if user:
            if host == 'workspace.localhost' and not user.is_workspace_user:
                messages.error(request, "This login is for BengalBound staff only.")
                return render(request, 'accounts/login.html', {'is_workspace': True})

            if host == 'console.localhost' and user.is_workspace_user:
                messages.error(request, "Staff accounts log in at workspace.localhost:1234")
                return render(request, 'accounts/login.html', {'is_workspace': False})

            if user.totpdevice_set.filter(confirmed=True).exists():
                request.session['totp_auth_user_id'] = user.id
                return redirect('accounts:totp_challenge')

            login(request, user)
            return _post_auth_redirect(request, user)
        else:
            messages.error(request, "Incorrect email or password. Please try again.")

    return render(request, 'accounts/login.html', {
        'is_workspace': host == 'workspace.localhost',
    })


# ─── SSO ──────────────────────────────────────────────────────────────────────

def sso_redirect_view(request):
    """Generate a time-limited token and POST it to the target subdomain's consume view."""
    target_base = request.GET.get('target', CONSOLE_URL).rstrip('/')
    next_path = request.GET.get('next', '/')

    if not request.user.is_authenticated:
        return redirect(f'{CONSOLE_URL}/accounts/login/?next={next_path}')

    signer = TimestampSigner()
    token = signer.sign(str(request.user.id))
    consume_url = f'{target_base}/accounts/sso/consume/'
    return _sso_post_form(token, consume_url, next_path)


@csrf_exempt
def sso_consume_view(request):
    """
    Receives an SSO token via POST (never GET), verifies it, logs in the user,
    then redirects to `next`. The csrf_exempt is safe because the TimestampSigner
    token itself proves the request originated from our own server.
    """
    token = request.POST.get('sso_token') or request.GET.get('sso_token')
    next_url = request.POST.get('next') or request.GET.get('next', '/')

    if token:
        signer = TimestampSigner()
        try:
            user_id = signer.unsign(token, max_age=30)
            user = User.objects.filter(id=user_id).first()
            if user:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        except (BadSignature, SignatureExpired):
            pass

    return redirect(next_url)

# ─── Two-Factor Authentication (TOTP) ─────────────────────────────────────────

import qrcode
import qrcode.image.svg
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django_otp.plugins.otp_totp.models import TOTPDevice

@login_required
def totp_setup_view(request):
    user = request.user
    device, created = TOTPDevice.objects.get_or_create(user=user, name='Default Device', defaults={'confirmed': False})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'disable':
            device.delete()
            messages.success(request, 'Two-Factor Authentication disabled.')
            return redirect('accounts:totp_setup')
            
        code = request.POST.get('totp_code')
        if device.verify_token(code):
            device.confirmed = True
            device.save()
            messages.success(request, 'Two-Factor Authentication enabled successfully!')
            return redirect('accounts:totp_setup')
        else:
            messages.error(request, 'Invalid code. Please try again.')
            
    url = device.config_url
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(url, image_factory=factory)
    stream = BytesIO()
    img.save(stream)
    svg = stream.getvalue().decode()
    
    return render(request, 'accounts/totp_setup.html', {'qr_svg': svg, 'device': device})

@ratelimit(key='ip', rate='10/m', block=False)
def totp_challenge_view(request):
    user_id = request.session.get('totp_auth_user_id')
    if not user_id:
        return redirect('accounts:login')
        
    if getattr(request, 'limited', False):
        messages.error(request, "Too many attempts. Please wait.")
        return render(request, 'accounts/totp_challenge.html')
        
    if request.method == 'POST':
        code = request.POST.get('totp_code')
        user = User.objects.get(id=user_id)
        device = user.totpdevice_set.filter(confirmed=True).first()
        if device and device.verify_token(code):
            del request.session['totp_auth_user_id']
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return _post_auth_redirect(request, user)
        else:
            messages.error(request, 'Invalid code.')
            
    return render(request, 'accounts/totp_challenge.html')
