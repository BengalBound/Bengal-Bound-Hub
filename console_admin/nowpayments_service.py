import requests
import json
import os
import hmac
import hashlib
from django.conf import settings

# Usually these come from settings.py or environment variables.
# We default to sandbox URL. Change to api.nowpayments.io for production.
NOWPAYMENTS_API_URL = os.getenv('NOWPAYMENTS_API_URL', 'https://api-sandbox.nowpayments.io/v1')
NOWPAYMENTS_API_KEY = os.getenv('NOWPAYMENTS_API_KEY', '')  # Add your Sandbox key here
NOWPAYMENTS_IPN_SECRET = os.getenv('NOWPAYMENTS_IPN_SECRET', '') # Used for webhook signature verification

def create_invoice(price_amount: float, price_currency: str, order_id: str, order_description: str, success_url: str, cancel_url: str) -> dict:
    """
    Creates an invoice on NowPayments.
    Returns the parsed JSON response dict (containing 'invoice_url', 'id', etc).
    """
    url = f"{NOWPAYMENTS_API_URL}/invoice"
    
    payload = {
        "price_amount": price_amount,
        "price_currency": price_currency,
        "order_id": order_id,
        "order_description": order_description,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "is_fee_paid_by_user": True
    }
    
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating NowPayments invoice: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response body: {e.response.text}")
        return None

def verify_ipn_signature(request_data: dict, signature: str) -> bool:
    """
    Verifies the x-nowpayments-sig header from a webhook POST request.
    Sorts dictionary keys as required by NowPayments documentation.
    """
    # NowPayments requires keys sorted alphabetically for the HMAC signature
    sorted_dict = dict(sorted(request_data.items()))
    request_str = json.dumps(sorted_dict, separators=(',', ':'))
    
    hmac_obj = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode('utf-8'),
        request_str.encode('utf-8'),
        hashlib.sha512
    )
    expected_signature = hmac_obj.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
