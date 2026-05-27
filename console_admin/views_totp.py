"""
console_admin/views_totp.py
Two-factor authentication (TOTP) setup, verify, and disable views.
Uses django-otp's built-in TOTPDevice model.
"""
import io
import base64

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from .decorators import console_user_required


def _get_or_create_device(user):
    """Return the user's TOTP device (unconfirmed until verified)."""
    from django_otp.plugins.otp_totp.models import TOTPDevice
    device, _ = TOTPDevice.objects.get_or_create(
        user=user,
        name='authenticator',
        defaults={'confirmed': False},
    )
    return device


def _device_qr_base64(device, user):
    """Return a base64-encoded PNG of the TOTP QR code."""
    import qrcode
    label = f"BengalBound:{user.email}"
    uri = device.config_url  # otpauth://totp/...
    # Replace default label with ours
    if '?' in uri:
        path, params = uri.split('?', 1)
        # Replace label in path
        uri = f"otpauth://totp/{label}?{params}"
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


@console_user_required(login_url='/accounts/login/')
def totp_setup(request):
    """Show QR code for the user to scan with their authenticator app."""
    from django_otp.plugins.otp_totp.models import TOTPDevice

    # Already confirmed — go to management view
    existing = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if existing:
        messages.info(request, "Two-factor authentication is already enabled.")
        return redirect('console_admin:totp_verify')

    device = _get_or_create_device(request.user)
    qr_b64 = _device_qr_base64(device, request.user)

    return render(request, 'console_admin/totp_setup.html', {
        'qr_b64': qr_b64,
        'secret_key': device.bin_key.hex() if hasattr(device, 'bin_key') else '',
    })


@console_user_required(login_url='/accounts/login/')
def totp_verify(request):
    """
    Verify the TOTP token entered by the user.
    On GET: show status / confirm form.
    On POST: validate code, mark device confirmed.
    """
    from django_otp.plugins.otp_totp.models import TOTPDevice

    confirmed = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()

    if request.method == 'POST':
        token = request.POST.get('token', '').strip().replace(' ', '')
        device = TOTPDevice.objects.filter(user=request.user).first()
        if device and device.verify_token(token):
            if not device.confirmed:
                device.confirmed = True
                device.save(update_fields=['confirmed'])
            messages.success(request, "Two-factor authentication enabled successfully.")
            return redirect('console_admin:dashboard')
        messages.error(request, "Invalid code — please try again.")

    return render(request, 'console_admin/totp_verify.html', {
        'is_confirmed': confirmed is not None,
    })


@console_user_required(login_url='/accounts/login/')
@require_POST
def totp_disable(request):
    """Remove all TOTP devices for the user (disables 2FA)."""
    from django_otp.plugins.otp_totp.models import TOTPDevice

    token = request.POST.get('token', '').strip()
    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()

    if not device:
        messages.error(request, "No active 2FA device found.")
        return redirect('console_admin:totp_verify')

    if not device.verify_token(token):
        messages.error(request, "Invalid code. 2FA was not disabled.")
        return redirect('console_admin:totp_verify')

    TOTPDevice.objects.filter(user=request.user).delete()
    messages.success(request, "Two-factor authentication disabled.")
    return redirect('console_admin:dashboard')
