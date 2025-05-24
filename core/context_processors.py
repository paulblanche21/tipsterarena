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
from .models import  Follow, Tip
from django.db.models import Q, Count


def suggested_tipsters(request):
    """Add suggested tipsters to the context."""
    if not request.user.is_authenticated:
        return {'suggested_tipsters': []}

    # Get users that the current user is not following
    following = Follow.objects.filter(follower=request.user).values_list('followed', flat=True)
    suggested_users = User.objects.exclude(
        Q(id__in=following) | Q(id=request.user.id)
    ).select_related('userprofile')[:3]

    tipsters = []
    for user in suggested_users:
        try:
            profile = user.userprofile
            tipsters.append({
                'username': user.username,
                'handle': profile.handle or user.username,
                'bio': profile.description or '',
                'avatar_url': profile.avatar.url if profile.avatar else None,
                'profile_url': f'/profile/{user.username}/'
            })
        except Exception:
            # Skip users with invalid profiles
            continue

    return {'suggested_tipsters': tipsters}

def trending_tips(request):
    """Add trending tips to the context."""
    # Get top 3 tips based on likes count
    trending_tips = Tip.objects.annotate(
        likes_count=Count('likes')
    ).order_by('-likes_count')[:3]

    tips_data = []
    for tip in trending_tips:
        tips_data.append({
            'id': tip.id,
            'text': tip.text,
            'user': {
                'username': tip.user.username,
            },
            'likes_count': tip.likes_count
        })

    return {'trending_tips': tips_data}