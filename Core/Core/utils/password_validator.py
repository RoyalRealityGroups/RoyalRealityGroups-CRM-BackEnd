"""
Password validation utility.

Rules:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
"""
import re
from rest_framework import serializers


PASSWORD_MIN_LENGTH = 8

PASSWORD_RULES = [
    (r'[A-Z]', 'at least one uppercase letter'),
    (r'[a-z]', 'at least one lowercase letter'),
    (r'[0-9]', 'at least one number'),
    (r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', 'at least one special character'),
]


def validate_password_strength(password: str) -> list:
    """
    Validate password strength. Returns list of error messages.
    Empty list means password is valid.
    """
    errors = []

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f'Password must be at least {PASSWORD_MIN_LENGTH} characters')

    for pattern, message in PASSWORD_RULES:
        if not re.search(pattern, password):
            errors.append(f'Password must contain {message}')

    return errors


def validate_password_field(value: str) -> str:
    """DRF serializer field validator for password."""
    errors = validate_password_strength(value)
    if errors:
        raise serializers.ValidationError(errors)
    return value
