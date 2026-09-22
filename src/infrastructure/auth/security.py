"""
Cryptographic Security & JWT Token Management for Enterprise Authentication.
Implements OWASP-compliant PBKDF2-HMAC-SHA256 password hashing and PyJWT token signing.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# Environment Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "support-ticket-enterprise-secret-key-prod-2026-v1")
JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
PBKDF2_ITERATIONS = 100_000  # Fast, highly secure iteration count for PBKDF2


def hash_password(plain_password: str) -> str:
    """
    Hashes a password with a cryptographically secure 16-byte random salt
    using PBKDF2-HMAC-SHA256.
    Returns: 'pbkdf2:sha256:<iterations>$<salt_hex>$<hash_hex>'
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored PBKDF2 hash using
    constant-time comparison to prevent timing attacks.
    """
    try:
        header, salt, key_hex = hashed_password.split("$")
        _, iterations_str = header.split(":")[-2], header.split(":")[-1]
        iterations = int(iterations_str)

        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(computed_key.hex(), key_hex)
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generates a cryptographically signed JWT bearer token containing
    tenant_id, user_id, role, and expiration claims.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"iat": now, "exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies a JWT token. Raises ValueError if invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token signature: {str(e)}")
