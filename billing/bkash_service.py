import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class BKashService:
    """bKash Tokenized Checkout Payment Gateway Integration"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'BKASH_BASE_URL', 'https://tokenized.pay.bka.sh/v1.2.0-beta')
        self.app_key = getattr(settings, 'BKASH_APP_KEY', '')
        self.app_secret = getattr(settings, 'BKASH_APP_SECRET', '')
        self.username = getattr(settings, 'BKASH_USERNAME', '')
        self.password = getattr(settings, 'BKASH_PASSWORD', '')

    def _get_token(self):
        """Fetch the authentication token from bKash."""
        if not all([self.app_key, self.app_secret, self.username, self.password]):
            logger.warning("bKash credentials missing in settings.")
            return None

        url = f"{self.base_url}/tokenized/checkout/token/grant"
        headers = {
            "username": self.username,
            "password": self.password,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if 'id_token' in data:
                return data['id_token']
        
        logger.error(f"Failed to fetch bKash token: {response.text}")
        return None

    def create_payment(self, amount: float, invoice_id: str, callback_url: str) -> dict:
        """Create a bKash payment request."""
        token = self._get_token()
        if not token:
            return {"statusMessage": "Failed to authenticate with bKash"}

        url = f"{self.base_url}/tokenized/checkout/create"
        headers = {
            "Authorization": token,
            "X-APP-Key": self.app_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "mode": "0011",
            "payerReference": invoice_id,
            "callbackURL": callback_url,
            "amount": str(amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": invoice_id,
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
            
        logger.error(f"Failed to create bKash payment: {response.text}")
        return {"statusMessage": "Failed to create payment with bKash"}

    def execute_payment(self, payment_id: str) -> dict:
        """Execute a payment after user confirmation."""
        token = self._get_token()
        if not token:
            return {"statusMessage": "Failed to authenticate with bKash"}

        url = f"{self.base_url}/tokenized/checkout/execute"
        headers = {
            "Authorization": token,
            "X-APP-Key": self.app_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "paymentID": payment_id
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
            
        logger.error(f"Failed to execute bKash payment: {response.text}")
        return {"statusMessage": "Failed to execute payment with bKash"}
