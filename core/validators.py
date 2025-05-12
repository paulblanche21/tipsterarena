"""
Custom Validators for Tipster Arena.

This module provides custom validation functions for user input in the Tipster Arena
application. It includes validators for usernames and other user-related data to ensure
data integrity and maintain consistent formatting across the platform.

Available Validators:
1. Username Validators:
   - validate_username_length: Ensures usernames are between 3 and 30 characters
   - validate_username_chars: Ensures usernames only contain alphanumeric characters

Usage:
    The validators can be used in Django models and forms:
    
    from django import models
    from core.validators import custom_username_validators
    
    class User(models.Model):
        username = models.CharField(
            max_length=30,
            validators=custom_username_validators()
        )

Validation Rules:
    Username Requirements:
    - Minimum length: 3 characters
    - Maximum length: 30 characters
    - Allowed characters: Letters (a-z, A-Z) and numbers (0-9)
    - No special characters or spaces allowed

Error Messages:
    - username_too_short: "Username must be at least 3 characters long."
    - username_too_long: "Username must be at most 30 characters long."
    - username_invalid_chars: "Username can only contain letters and numbers."

Note:
    All error messages are translatable using Django's translation system.
"""

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