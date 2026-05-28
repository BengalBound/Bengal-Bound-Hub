import hmac
import hashlib

class WebhookReceiver:
    @staticmethod
    def verify_hmac(secret: str, payload: bytes, signature: str) -> bool:
        if not secret:
            return True
        mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
        expected_signature = mac.hexdigest()
        return hmac.compare_digest(expected_signature, signature)
