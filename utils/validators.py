"""
Input validation helpers (email, phone, app name).
"""
import re

# ---------------------------------------------------------------------------
# Email validation (RFC 5322 simplified)
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


# ---------------------------------------------------------------------------
# Phone number validation (E.164-like, flexible)
# ---------------------------------------------------------------------------
PHONE_RE = re.compile(
    r"^\+?[0-9]{7,15}$"
)


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone.strip().replace(" ", "").replace("-", "")))


# ---------------------------------------------------------------------------
# App name validation (safe for Android resources)
# ---------------------------------------------------------------------------
APP_NAME_RE = re.compile(
    r"^[A-Za-z0-9_\- ]{1,50}$"
)


def is_valid_app_name(name: str) -> bool:
    return bool(APP_NAME_RE.match(name.strip()))
