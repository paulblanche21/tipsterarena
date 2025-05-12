# core/pipeline.py
"""
Social Authentication Pipeline for Tipster Arena.

This module contains pipeline functions that are executed during the social authentication process.
It handles the creation and setup of user profiles when users sign in through social providers
like Twitter, Google, and Facebook.

The pipeline ensures that:
1. Each user has an associated UserProfile
2. Social handles are properly formatted and unique
3. Profile information is synchronized with social provider data
"""

from core.models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Create or update a user profile during social authentication.
    
    This function is called during the social authentication pipeline to ensure
    each user has an associated UserProfile. It handles the creation of new
    profiles and sets up appropriate handles based on the social provider.
    
    Args:
        backend: The social authentication backend being used (e.g., Twitter, Google)
        user: The Django User instance being authenticated
        response: The response data from the social provider
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments
    
    Returns:
        None
    
    Note:
        - For Twitter, uses the screen_name as the handle
        - For Google and Facebook, uses the username with @ prefix
        - Ensures handle uniqueness by appending numbers if needed
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created:
        if backend.name == 'twitter':
            handle = f"@{response.get('screen_name')}"
        elif backend.name == 'google-oauth2':
            handle = f"@{user.username}"
        elif backend.name == 'facebook':
            handle = f"@{user.username}"
        # Ensure handle is unique
        base_handle = handle
        counter = 1
        while UserProfile.objects.filter(handle=handle).exists():
            handle = f"{base_handle}{counter}"
            counter += 1
        profile.handle = handle
        profile.save()