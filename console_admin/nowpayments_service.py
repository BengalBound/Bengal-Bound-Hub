"""
NowPayments payment gateway service.
Accepts crypto + credit/debit cards globally. Works from Bangladesh.

Setup:
  1. Sign up at https://nowpayments.io (sandbox: https://sandbox.nowpayments.io)
  2. Get API key from dashboard
  3. Set IPN Secret in Business Settings → IPN Settings
  4. Register webhook: https://app.bengalbound.com/nowpayments/webhook/
  5. Set NOWPAYMENTS_API_KEY + NOWPAYMENTS_IPN_SECRET + NOWPAYMENTS_API_URL in .env
"""
import json
import hmac
import hashlib
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _api_url() -> str:
    return getattr(settings, 'NOWPAYMENTS_API_URL', 'https://api-sandbox.nowpayments.io/v1')

def _api_key() -> str:
    return getattr(settings, 'NOWPAYMENTS_API_KEY', '')

def _ipn_secret() -> str:
    return getattr(settings, 'NOWPAYMENTS_IPN_SECRET', '')


def create_invoice(
    price_amount: float,
    price_currency: str,
    order_id: str,
    order_description: str,
    success_url: str,
    cancel_url: str,
) -> dict | None:
    """
    Creates a NowPayments invoice. Returns the response dict with 'invoice_url' and 'id',
    or None on failure.
    """
    if not _api_key():
        logger.error("NOWPAYMENTS_API_KEY is not set — cannot create invoice.")
        return None

    payload = {
        "price_amount": price_amount,
        "price_currency": price_currency,
        "order_id": order_id,
        "order_description": order_description,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "is_fee_paid_by_user": True,
    }
    try:
        resp = requests.post(
            f"{_api_url()}/invoice",
            headers={"x-api-key": _api_key(), "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error("NowPayments invoice creation failed: %s", exc)
        if getattr(exc, 'response', None) is not None:
            logger.error("Response: %s", exc.response.text)
        return None


def verify_ipn_signature(request_data: dict, signature: str) -> bool:
    """
    Verifies the x-nowpayments-sig HMAC-SHA512 header from a webhook POST.
    NowPayments requires keys sorted alphabetically before hashing.
    """
    if not _ipn_secret():
        logger.warning("NOWPAYMENTS_IPN_SECRET not set — cannot verify webhook signature.")
        return False

    sorted_data = dict(sorted(request_data.items()))
    payload_str = json.dumps(sorted_data, separators=(',', ':'))
    expected = hmac.new(
        _ipn_secret().encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
