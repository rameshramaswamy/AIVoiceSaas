import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class CryptoUtils:
    def __init__(self, secret_key: str):
        """
        secret_key: The master key from env vars (e.g., settings.SECRET_KEY)
        """
        # Derive a 32-byte url-safe base64-encoded key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'static_salt_for_simplicity', # In prod, store salt per record
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, raw_data: str) -> str:
        if not raw_data:
            return ""
        return self.fernet.encrypt(raw_data.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        if not encrypted_token:
            return ""
        return self.fernet.decrypt(encrypted_token.encode()).decode()