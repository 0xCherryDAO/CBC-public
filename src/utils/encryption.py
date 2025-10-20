import base64
import os

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_data(data: str, password: str) -> tuple[bytes, bytes]:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return salt, encrypted


def decrypt_data(encrypted_data: bytes, password: str, salt: bytes) -> str:
    key = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()
