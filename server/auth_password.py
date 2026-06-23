from __future__ import annotations

import hashlib
import secrets

_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations_str, salt_hex, digest_hex = stored.split("$", 3)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(iterations_str),
    )
    return secrets.compare_digest(digest.hex(), digest_hex)
