"""
Core — Utility functions (encryption, helpers).
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_fernet():
    """Get a Fernet instance for encrypting/decrypting credentials."""
    from cryptography.fernet import Fernet

    key = settings.CREDENTIAL_ENCRYPTION_KEY
    if not key:
        raise ValueError(
            "CREDENTIAL_ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    fernet = get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    fernet = get_fernet()
    return fernet.decrypt(ciphertext.encode()).decode()
