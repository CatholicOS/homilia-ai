"""
Hashing utilities for Homilia AI
Provides secure encryption and decryption of S3 keys for URL parameters.
"""

import base64
import os
from cryptography.fernet import Fernet
from typing import Optional

# Generate or use a secret key for encryption
SECRET_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())

def encrypt_s3_key(s3_key: str) -> str:
    """
    Encrypt an S3 key for use in URLs.
    
    Args:
        s3_key: The S3 key to encrypt
        
    Returns:
        Base64 encoded encrypted S3 key
    """
    try:
        # Ensure the key is bytes
        if isinstance(SECRET_KEY, str):
            key = SECRET_KEY.encode()
        else:
            key = SECRET_KEY
            
        f = Fernet(key)
        encrypted_bytes = f.encrypt(s3_key.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8').rstrip('=')
    except Exception as e:
        # Fallback to simple base64 encoding if encryption fails
        return base64.urlsafe_b64encode(s3_key.encode('utf-8')).decode('utf-8').rstrip('=')

def decrypt_s3_key(encrypted_key: str) -> Optional[str]:
    """
    Decrypt an S3 key from a URL parameter.
    
    Args:
        encrypted_key: The encrypted key from URL
        
    Returns:
        The original S3 key if decryption succeeds, None otherwise
    """
    try:
        # Ensure the key is bytes
        if isinstance(SECRET_KEY, str):
            key = SECRET_KEY.encode()
        else:
            key = SECRET_KEY
            
        f = Fernet(key)
        
        # Add padding if needed
        encrypted_key += '=' * (4 - len(encrypted_key) % 4)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode('utf-8'))
        
        decrypted_bytes = f.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Fallback to simple base64 decoding if decryption fails
        try:
            encrypted_key += '=' * (4 - len(encrypted_key) % 4)
            decrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return None
