"""
secure_password.py - Keyring-backed sudo password storage.
Falls back to an in-memory cache when no suitable keyring backend is found.
"""

import keyring

SERVICE  = "UXTU4Unix"
ACCOUNT  = "sudo"
_cache: str | None = None


def _backend_ok() -> bool:
    try:
        name = type(keyring.get_keyring()).__name__.lower()
        return name not in {"failkeyring", "nullkeyring", "plaintextkeyring"}
    except Exception:
        return False


def get_password() -> str | None:
    global _cache
    if _cache:
        return _cache
    if _backend_ok():
        try:
            stored = keyring.get_password(SERVICE, ACCOUNT)
            if stored:
                _cache = stored
                return _cache
        except Exception:
            pass
    return None


def save_password(password: str) -> None:
    global _cache
    _cache = password
    if _backend_ok():
        try:
            keyring.set_password(SERVICE, ACCOUNT, password)
        except Exception:
            pass


def delete_password() -> None:
    global _cache
    _cache = None
    if _backend_ok():
        try:
            keyring.delete_password(SERVICE, ACCOUNT)
        except Exception:
            pass


def has_password() -> bool:
    if _cache:
        return True
    if _backend_ok():
        try:
            return keyring.get_password(SERVICE, ACCOUNT) is not None
        except Exception:
            pass
    return False