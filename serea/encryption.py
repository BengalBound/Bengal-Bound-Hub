"""
serea/encryption.py
───────────────────
Fernet-based field encryption for sensitive platform credentials.

Key resolution order:
  1. SEREA_ENCRYPTION_KEY env var (provide a raw string — it is SHA-256 hashed)
  2. Django SECRET_KEY (derived the same way)

Values stored in the DB carry an 'enc:' prefix so legacy plaintext is
handled transparently — old rows are returned as-is; new writes are
always encrypted.
"""

import os
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.db import models

logger = logging.getLogger(__name__)

_fernet_instance = None
_ENC_PREFIX = 'enc:'


def _get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        from django.conf import settings

        raw = (
            os.getenv('SEREA_ENCRYPTION_KEY')
            or getattr(settings, 'SEREA_ENCRYPTION_KEY', None)
            or settings.SECRET_KEY
        )
        # Derive a 32-byte URL-safe base64 key via SHA-256
        key_bytes = base64.urlsafe_b64encode(
            hashlib.sha256(raw.encode()).digest()
        )
        _fernet_instance = Fernet(key_bytes)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    """Encrypt plaintext and return an 'enc:...' prefixed token."""
    if not plaintext:
        return plaintext
    token = _get_fernet().encrypt(plaintext.encode()).decode()
    return f"{_ENC_PREFIX}{token}"


def decrypt_value(value: str) -> str:
    """Decrypt an 'enc:...' token. Returns the value unchanged for legacy plaintext."""
    if not value or not value.startswith(_ENC_PREFIX):
        return value
    token = value[len(_ENC_PREFIX):]
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        logger.error(
            "EncryptedTextField: decryption failed — key mismatch or corrupted token. "
            "Returning raw value to avoid a crash."
        )
        return value


class EncryptedTextField(models.TextField):
    """
    A TextField that transparently encrypts on write and decrypts on read.

    - Stored value: 'enc:<fernet_token>'
    - Python value: plain string
    - Legacy plaintext rows (no 'enc:' prefix) are returned as-is so
      existing data does not break before a backfill migration is run.
    """

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        return decrypt_value(value)

    def get_prep_value(self, value):
        if not value:
            return value
        if isinstance(value, str) and not value.startswith(_ENC_PREFIX):
            return encrypt_value(value)
        return value  # already encrypted — pass through


class EncryptedJSONField(models.JSONField):
    """
    A JSONField whose serialised bytes are encrypted at rest.
    Python reads/writes dicts as normal; the DB column stores an encrypted string.
    """

    def from_db_value(self, value, expression, connection):
        if value is None:
            return {}
        decrypted = decrypt_value(value) if isinstance(value, str) else value
        if isinstance(decrypted, str):
            import json
            try:
                return json.loads(decrypted)
            except Exception:
                return {}
        return decrypted

    def get_prep_value(self, value):
        import json
        if value is None:
            return encrypt_value('{}')
        raw = json.dumps(value)
        return encrypt_value(raw) if not raw.startswith(_ENC_PREFIX) else raw
