"""
auth.py - Authentication utilities.

Provides password hashing/verification, JWT generation/verification,
and an auth_required decorator for protecting Flask routes.
"""

import jwt
import functools
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, g

from config import config


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash *plain* with PBKDF2-SHA256 via Werkzeug."""
    return generate_password_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* value."""
    return check_password_hash(hashed, plain)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def generate_token(user_id: int, username: str) -> str:
    """
    Create a signed JWT containing *user_id* and *username*.
    Token expires after JWT_EXPIRY_HOURS (default 24 h).
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=config.JWT_EXPIRY_HOURS),
        "iat": datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """
    Decode and validate *token*.
    Returns the payload dict on success, None on any failure.
    """
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _extract_token_from_request() -> str | None:
    """Pull the Bearer token from the Authorization header, if present."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------

def auth_required(fn):
    """
    Route decorator that verifies the JWT in the Authorization header.

    On success, stores the decoded payload in ``flask.g.current_user``
    (keys: ``user_id``, ``username``) so route handlers can access it
    without re-parsing the token.

    Returns 401 JSON on missing / invalid / expired tokens.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token_from_request()
        if not token:
            return jsonify({"error": "Authorization token required"}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.current_user = payload   # {"user_id": int, "username": str}
        return fn(*args, **kwargs)

    return wrapper
