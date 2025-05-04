"""Custom validators for Tipster Arena."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def custom_username_validators():
    """Return a list of custom username validators."""
    return [
        {
            'NAME': 'core.validators.validate_username_length',
        },
        {
            'NAME': 'core.validators.validate_username_chars',
        },
    ]

def validate_username_length(value):
    """Validate username length."""
    if len(value) < 3:
        raise ValidationError(
            _('Username must be at least 3 characters long.'),
            code='username_too_short',
        )
    if len(value) > 30:
        raise ValidationError(
            _('Username must be at most 30 characters long.'),
            code='username_too_long',
        )

def validate_username_chars(value):
    """Validate username characters."""
    if not value.isalnum():
        raise ValidationError(
            _('Username can only contain letters and numbers.'),
            code='username_invalid_chars',
        ) 