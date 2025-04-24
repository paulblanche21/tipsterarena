# core/pipeline.py
from core.models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):
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