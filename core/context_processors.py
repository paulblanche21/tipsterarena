# core/context_processors.py
from django.contrib.auth.models import User
from .models import UserProfile, Follow


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