from django.contrib.auth.models import User
from core.models import UserProfile

for user in User.objects.all():
    profile, created = UserProfile.objects.get_or_create(user=user)
    if not profile.handle:
        profile.handle = f"@{user.username}"
        profile.save()