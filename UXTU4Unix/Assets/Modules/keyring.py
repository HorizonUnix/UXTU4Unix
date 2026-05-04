"""
keyring.py
"""
import keyring as _kr

SERVICE = "UXTU4Unix"
ACCOUNT = "sudo"


def backend_available() -> bool:
    try:
        name = type(_kr.get_keyring()).__name__.lower()
        return name not in {"failkeyring", "nullkeyring", "plaintextkeyring"}
    except Exception:
        return False


def _require_backend() -> None:
    if not backend_available():
        raise RuntimeError(
            "No secret service backend found.\n"
            "Install and unlock gnome-keyring or kwallet before running UXTU4Unix."
        )


def get_password() -> str | None:
    _require_backend()
    return _kr.get_password(SERVICE, ACCOUNT)


def save_password(password: str) -> None:
    _require_backend()
    _kr.set_password(SERVICE, ACCOUNT, password)


def delete_password() -> None:
    _require_backend()
    try:
        _kr.delete_password(SERVICE, ACCOUNT)
    except Exception:
        pass


def has_password() -> bool:
    try:
        return get_password() is not None
    except RuntimeError:
        return False