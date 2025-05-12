# core/context_processors.py
"""
Context Processors for Tipster Arena.

This module provides context processors that inject additional data into the template
context for all views in the Tipster Arena application. These processors ensure that
common data is available throughout the application without needing to be explicitly
passed in each view.

Available Processors:
1. suggested_tipsters
   - Provides a list of suggested tipsters for the sidebar
   - Only shows active tipsters (users who have posted tips)
   - Excludes users that the current user already follows
   - Limited to 3 suggestions for sidebar display
   - Returns empty list for unauthenticated users
   - Each suggestion includes:
     * username
     * bio (falls back to default if none exists)
     * avatar (falls back to default avatar if none exists)

Usage:
    The context processors are automatically loaded for all templates when
    added to the TEMPLATES setting in settings.py:

    TEMPLATES = [
        {
            'OPTIONS': {
                'context_processors': [
                    'core.context_processors.suggested_tipsters',
                    # ... other context processors
                ],
            },
        },
    ]

    In templates, the data is available directly:
    {% for tipster in suggested_tipsters %}
        {{ tipster.username }}
        {{ tipster.bio }}
        <img src="{{ tipster.avatar }}" alt="{{ tipster.username }}'s avatar">
    {% endfor %}
"""

from django.contrib.auth.models import User
from .models import  Follow


def suggested_tipsters(request):
    if not request.user.is_authenticated:
        return {'suggested_tipsters': []}
    current_user = request.user
    followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
    suggested_users = User.objects.filter(
        tip__isnull=False
    ).exclude(
        id__in=followed_users
    ).exclude(
        id=current_user.id
    ).distinct()[:3]  # Limit to 3 for sidebar
    suggested_tipsters = [
        {
            'username': user.username,
            'bio': getattr(user.userprofile, 'description', '') or f"{user.username}'s bio",
            'avatar': getattr(user.userprofile, 'avatar', None).url if hasattr(user.userprofile, 'avatar') and user.userprofile.avatar else '/static/images/default-avatar.png'
        }
        for user in suggested_users
    ]
    return {'suggested_tipsters': suggested_tipsters}