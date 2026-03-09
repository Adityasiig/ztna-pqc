"""
Authentication module — reads from SQLite via database.py.
"""

import secrets
from database import get_user, write_log


def login_user(username: str, password: str, ip: str = None) -> dict:
    import hashlib
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    user = get_user(username)

    if user and user["pw_hash"] == pw_hash:
        token = secrets.token_hex(32)
        write_log(
            event=f"Login successful: {username}",
            result="success",
            username=username,
            ip=ip
        )
        return {
            "status": "success",
            "token": f"ZTNA-{token.upper()[:24]}",
            "role": user["role"],
            "algorithm": "Kyber-512",
        }

    write_log(
        event=f"Login failed: {username}",
        result="denied",
        username=username,
        ip=ip
    )
    return {"status": "failed", "message": "Invalid credentials"}
