"""Custom decorators for permission and rate limiting."""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.contrib.auth.decorators import login_required

def check_daily_tip_limit(view_func):
    """Decorator to enforce daily tip limit for basic users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Premium Users').exists():
            # Check how many tips user has created today
            today = timezone.now().date()
            tips_today = request.user.tip_set.filter(
                created_at__date=today
            ).count()
            
            if tips_today >= 5:
                raise PermissionDenied(
                    'Free users can only create 5 tips per day. '
                    'Upgrade to Premium to create unlimited tips!'
                )
        return view_func(request, *args, **kwargs)
    return wrapper

def check_follow_limit(view_func):
    """Decorator to enforce follow limit for basic users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Premium Users').exists():
            # Check how many users they are following
            following_count = request.user.following.count()
            
            if following_count >= 100:
                raise PermissionDenied(
                    'Free users can only follow up to 100 users. '
                    'Upgrade to Premium to follow unlimited users!'
                )
        return view_func(request, *args, **kwargs)
    return wrapper

def premium_required(view_func):
    """Decorator to restrict access to premium users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Premium Users').exists():
            raise PermissionDenied(
                'This feature is only available to Premium users. '
                'Upgrade now to access!'
            )
        return view_func(request, *args, **kwargs)
    return wrapper

def check_ownership(model_class):
    """Decorator factory to check if user owns the object they're trying to modify."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get object ID from request
            obj_id = kwargs.get('id') or request.POST.get('id')
            if not obj_id:
                raise PermissionDenied('Object ID not provided')
            
            # Get the object
            obj = model_class.objects.get(id=obj_id)
            
            # Check if user owns the object
            if obj.user != request.user:
                # Premium users might have additional permissions
                if not request.user.groups.filter(name='Premium Users').exists():
                    raise PermissionDenied('You do not have permission to modify this object')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator 