from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import bcrypt

def generate_key(master_password: str, salt: bytes) -> bytes:
    """Генерация ключа из мастер-пароля"""
    return bcrypt.kdf(
        password=master_password.encode(),
        salt=salt,
        desired_key_bytes=32,
        rounds=100
    )

def encrypt_password(key: bytes, password: str) -> (bytes, bytes):
    """Шифрование пароля AES-256"""
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    data = padder.update(password.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return iv, encryptor.update(data) + encryptor.finalize()

def decrypt_password(key: bytes, iv: bytes, encrypted_password: bytes) -> str:
    """Дешифрование пароля"""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_password) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(decrypted) + unpadder.finalize()).decode()