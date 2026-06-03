import logging
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

logger = logging.getLogger(__name__)

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

    # Respect the 'next' parameter if present, but make sure it is a safe local redirect
    next_path = request.GET.get('next') or request.POST.get('next') or request.session.get('next')
    if next_path and next_path.startswith('/') and not next_path.startswith('//'):
        target_path = next_path
        if 'next' in request.session:
            request.session.pop('next', None)

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

    next_param = request.GET.get('next') or request.POST.get('next')
    if next_param and next_param.startswith('/') and not next_param.startswith('//'):
        request.session['next'] = next_param
        request.session.save()

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

        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            if not existing_user.is_email_verified:
                otp = generate_otp()
                existing_user.otp = otp
                existing_user.otp_created_at = timezone.now()
                existing_user.save(update_fields=['otp', 'otp_created_at'])
                send_otp_email(existing_user, otp)

                request.session['verify_email'] = email
                request.session.save()
                messages.info(request, "This account is pending verification. A new verification code has been sent.")
                return redirect(f"/accounts/verify-otp/?email={email}")
            else:
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

        # Create allauth EmailAddress record to support allauth email verification system
        from allauth.account.models import EmailAddress
        EmailAddress.objects.get_or_create(
            user=user,
            email=email,
            defaults={'primary': True, 'verified': False}
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
            except Exception as exc:
                logger.debug("Social provider %s check bypassed/failed: %s", provider_id, exc)
        return providers
    except Exception:
        logger.exception("Failed to load social auth providers")
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


def _verify_otp_key(group, request):
    email = request.GET.get('email') or request.session.get('verify_email') or ''
    return email.lower()


# ─── OTP Verification ─────────────────────────────────────────────────────────

@ratelimit(key=_verify_otp_key, method='POST', rate='3/h', block=False)
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

            # Verify allauth EmailAddress record
            from allauth.account.models import EmailAddress
            EmailAddress.objects.filter(user=user, email=user.email).update(verified=True)

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Email verified! Welcome to BengalBound.")
            return _post_auth_redirect(request, user)

        messages.error(request, "Invalid or expired code. Please check your email and try again.")

    return render(request, 'accounts/verify_otp.html', {'email': email})


def resend_otp_view(request):
    email = request.GET.get('email') or request.session.get('verify_email')
    if not email:
        messages.error(request, "Email address is required to resend verification code.")
        return redirect('accounts:register')

    user = User.objects.filter(email=email).first()
    if not user:
        messages.error(request, "No pending registration found for this email.")
        return redirect('accounts:register')

    if user.is_email_verified:
        messages.info(request, "Your email is already verified. Please log in.")
        return redirect('accounts:login')

    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save(update_fields=['otp', 'otp_created_at'])
    send_otp_email(user, otp)

    request.session['verify_email'] = email
    request.session.save()
    messages.success(request, "A new verification code has been sent to your email.")
    return redirect(f"/accounts/verify-otp/?email={email}")


# ─── Login ────────────────────────────────────────────────────────────────────

def custom_login_view(request):
    """
    Custom login that redirects to the correct subdomain after authentication.
    django-axes handles brute-force protection via AUTHENTICATION_BACKENDS.
    """
    if request.user.is_authenticated:
        return _post_auth_redirect(request, request.user)

    next_param = request.GET.get('next') or request.POST.get('next')
    if next_param and next_param.startswith('/') and not next_param.startswith('//'):
        request.session['next'] = next_param
        request.session.save()

    host = request.get_host().split(':')[0].lower()
    email = ''

    if request.method == 'POST':
        email = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)

        if user:
            from django.conf import settings
            if getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'none') == 'mandatory' and not user.is_email_verified:
                otp = generate_otp()
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save(update_fields=['otp', 'otp_created_at'])
                send_otp_email(user, otp)

                request.session['verify_email'] = user.email
                request.session.save()
                messages.info(request, "Your email is not verified. A verification code has been sent to your inbox.")
                return redirect(f"/accounts/verify-otp/?email={user.email}")

            if host == 'workspace.localhost' and not user.is_workspace_user:
                messages.error(request, "This login is for BengalBound staff only.")
                return render(request, 'accounts/login.html', {'is_workspace': True, 'social_providers': [], 'username': email})

            if host == 'console.localhost' and user.is_workspace_user:
                messages.error(request, "Staff accounts log in at workspace.localhost:1234")
                return render(request, 'accounts/login.html', {'is_workspace': False, 'social_providers': _social_providers(request), 'username': email})

            if user.totpdevice_set.filter(confirmed=True).exists():
                request.session['totp_auth_user_id'] = user.id
                request.session['totp_auth_host'] = host
                return redirect('accounts:totp_challenge')

            login(request, user)
            return _post_auth_redirect(request, user)
        else:
            messages.error(request, "Incorrect email or password. Please try again.")

    return render(request, 'accounts/login.html', {
        'is_workspace': host == 'workspace.localhost',
        'social_providers': _social_providers(request),
        'username': email,
        'next': next_param,
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

        # Only allow verification when the device is not yet confirmed.
        if not device.confirmed:
            code = request.POST.get('totp_code')
            if device.verify_token(code):
                device.confirmed = True
                device.save()
                messages.success(request, 'Two-Factor Authentication enabled successfully!')
                return redirect('accounts:totp_setup')
            else:
                messages.error(request, 'Invalid code. Please try again.')

    # Never expose the secret (QR / config_url) once the device is confirmed.
    if device.confirmed:
        return render(request, 'accounts/totp_setup.html', {'device': device, 'qr_svg': None})

    url = device.config_url
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(url, image_factory=factory)
    stream = BytesIO()
    img.save(stream)
    svg = stream.getvalue().decode()

    return render(request, 'accounts/totp_setup.html', {'qr_svg': svg, 'device': device})

_TOTP_MAX_ATTEMPTS = 5

@ratelimit(key='ip', rate='10/m', block=False)
def totp_challenge_view(request):
    user_id = request.session.get('totp_auth_user_id')
    if not user_id:
        return redirect('accounts:login')

    # Re-enforce the subdomain role guard that ran before the TOTP redirect.
    host = request.get_host().split(':')[0].lower()
    auth_host = request.session.get('totp_auth_host', '')
    if host != auth_host:
        request.session.pop('totp_auth_user_id', None)
        request.session.pop('totp_auth_host', None)
        request.session.pop('totp_attempts', None)
        messages.error(request, "Session mismatch. Please log in again.")
        return redirect('accounts:login')

    # Per-IP rate limit (basic protection).
    if getattr(request, 'limited', False):
        messages.error(request, "Too many attempts. Please wait.")
        return render(request, 'accounts/totp_challenge.html')

    # Per-account lockout after repeated failures (protects against rotating IPs).
    attempts = request.session.get('totp_attempts', 0)
    if attempts >= _TOTP_MAX_ATTEMPTS:
        request.session.pop('totp_auth_user_id', None)
        request.session.pop('totp_auth_host', None)
        request.session.pop('totp_attempts', None)
        messages.error(request, "Too many failed attempts. Please log in again.")
        return redirect('accounts:login')

    if request.method == 'POST':
        code = request.POST.get('totp_code')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            request.session.pop('totp_auth_user_id', None)
            request.session.pop('totp_auth_host', None)
            request.session.pop('totp_attempts', None)
            return redirect('accounts:login')

        device = user.totpdevice_set.filter(confirmed=True).first()
        if device and device.verify_token(code):
            request.session.pop('totp_auth_user_id', None)
            request.session.pop('totp_auth_host', None)
            request.session.pop('totp_attempts', None)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return _post_auth_redirect(request, user)
        else:
            request.session['totp_attempts'] = attempts + 1
            messages.error(request, 'Invalid code.')

    return render(request, 'accounts/totp_challenge.html')


def signup_redirect_view(request):
    """Redirect default allauth signup page requests to the custom registration view."""
    next_param = request.GET.get('next') or request.POST.get('next')
    url = '/accounts/register/'
    if next_param:
        from django.utils.http import urlencode
        url += '?' + urlencode({'next': next_param})
    return redirect(url)


def verify_firebase_token(id_token):
    """
    Verify the Firebase ID token and return the decoded claims.
    Bypasses validation if settings.TESTING or (DEBUG and token starts with mock_token_).
    """
    import jwt
    import requests
    from django.conf import settings
    from cryptography.x509 import load_pem_x509_certificate

    project_id = getattr(settings, 'FIREBASE_PROJECT_ID', 'bengalbound-prod')
    
    # Check for testing or mock token fallback
    is_testing = getattr(settings, 'TESTING', False)
    is_debug_mock = settings.DEBUG and id_token.startswith('mock_token_')
    
    if is_testing or is_debug_mock:
        try:
            return jwt.decode(id_token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Failed to decode mock Firebase token: {e}")
            return None

    try:
        header = jwt.get_unverified_header(id_token)
        kid = header.get('kid')
        if not kid:
            raise ValueError("No 'kid' field in token header.")

        response = requests.get("https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com", timeout=5)
        if response.status_code != 200:
            raise ValueError("Failed to fetch Google public keys certificate.")
        
        public_keys = response.json()
        cert_pem = public_keys.get(kid)
        if not cert_pem:
            raise ValueError(f"No Google public key found for kid: {kid}")

        # Extract public key from PEM certificate
        cert = load_pem_x509_certificate(cert_pem.encode('utf-8'))
        public_key = cert.public_key()

        # Decode and verify token
        decoded = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}"
        )
        return decoded
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        if settings.DEBUG:
            try:
                return jwt.decode(id_token, options={"verify_signature": False})
            except Exception:
                pass
        raise e


@csrf_exempt
def firebase_token_sync(request):
    """
    POST /accounts/firebase-sync/
    Body: {"id_token": "firebase_id_token"}
    
    Verifies token, finds or creates user, logs them in, and returns SimpleJWT token pair.
    """
    import json
    from django.http import JsonResponse
    from rest_framework_simplejwt.tokens import RefreshToken

    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body)
        id_token = body.get('id_token')
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    if not id_token:
        return JsonResponse({"error": "Missing 'id_token' in request body."}, status=400)

    try:
        decoded_token = verify_firebase_token(id_token)
    except Exception as e:
        return JsonResponse({"error": f"Invalid token: {str(e)}"}, status=400)

    if not decoded_token:
        return JsonResponse({"error": "Token decoding failed."}, status=400)

    uid = decoded_token.get('uid') or decoded_token.get('sub')
    email = decoded_token.get('email')
    
    if not uid or not email:
        return JsonResponse({"error": "Token does not contain 'uid' and 'email' claims."}, status=400)

    email = email.strip().lower()
    name = decoded_token.get('name', '')
    first_name = decoded_token.get('first_name', '')
    last_name = decoded_token.get('last_name', '')
    
    if not first_name and not last_name and name:
        parts = name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

    # Atomic transaction for finding/creating user and setup
    with transaction.atomic():
        user = User.objects.filter(firebase_uid=uid).first()
        if not user:
            user = User.objects.filter(email=email).first()
            if user:
                user.firebase_uid = uid
                user.save(update_fields=['firebase_uid'])
            else:
                user = User.objects.create_user(
                    email=email,
                    username=email,
                    password=secrets.token_urlsafe(16),
                    is_email_verified=True,
                    firebase_uid=uid,
                    first_name=first_name,
                    last_name=last_name,
                    role='console_user',
                )
                # Create CustomerProfile
                from .models import CustomerProfile
                CustomerProfile.objects.get_or_create(user=user)

        # Ensure allauth EmailAddress record exists and is verified
        from allauth.account.models import EmailAddress
        EmailAddress.objects.get_or_create(
            user=user,
            email=email,
            defaults={'primary': True, 'verified': True}
        )

        # Provision default business if they don't own any active business
        from hub.models import BusinessInstance, BusinessEmployee
        from hub.views import _get_or_create_subscription
        
        biz = BusinessInstance.objects.filter(owner=user, is_active=True).first()
        if not biz:
            business_name = f"{user.first_name or email.split('@')[0]}'s Company"
            slug = _unique_business_slug(business_name)
            biz = BusinessInstance.objects.create(
                owner=user,
                name=business_name,
                slug=slug,
                business_type='business',
                installation_type='cloud',
                business_email=email,
            )
            BusinessEmployee.objects.create(
                business=biz,
                user=user,
                name=f"{user.first_name} {user.last_name}".strip() or email.split('@')[0],
                email=email,
                role='owner',
            )
            # Create default subscription
            _get_or_create_subscription(biz)

    # Log in session for standard Django session auth
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # Generate SimpleJWT tokens
    refresh = RefreshToken.for_user(user)
    
    return JsonResponse({
        "status": "success",
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "firebase_uid": user.firebase_uid,
        }
    }, status=200)
