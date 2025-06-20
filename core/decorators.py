"""
Custom Decorators for Tipster Arena.

This module provides a collection of decorators that handle various aspects of
permission control, rate limiting, and access restrictions in the Tipster Arena
application. These decorators are used to enforce business rules and maintain
the integrity of the platform's features.

Available Decorators:
1. check_daily_tip_limit
   - Enforces a daily limit of 2 tips for Free users
   - Premium users have unlimited tips
   - Raises PermissionDenied if limit is exceeded

2. check_follow_limit
   - Restricts Free users to following a maximum of 10 users
   - Premium users can follow unlimited users
   - Raises PermissionDenied if limit is exceeded

3. premium_required
   - Restricts access to premium-only features
   - Verifies user has Premium tier
   - Raises PermissionDenied for non-premium users

4. check_ownership
   - Factory decorator that verifies object ownership
   - Ensures users can only modify their own content
   - Supports both direct object access and POST requests
   - Premium users may have additional permissions

Usage Examples:
    @check_daily_tip_limit
    def create_tip(request):
        # Only executed if user hasn't exceeded daily tip limit
        pass

    @premium_required
    def premium_feature(request):
        # Only accessible to premium users
        pass

    @check_ownership(Tip)
    def edit_tip(request):
        # Only executed if user owns the tip
        pass
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages


def check_daily_tip_limit(view_func):
    """Decorator to enforce daily tip limit for Free users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied('Please log in to post tips.')
            
        profile = request.user.userprofile
        today = timezone.now().date()
        tips_today = request.user.tip_set.filter(created_at__date=today).count()
        
        if profile.tier == 'free':
            if tips_today >= 2:
                messages.warning(request, 'Free tier: Max 2 tips per day. Upgrade to Premium for unlimited tips!')
                return redirect('setup_tiers')
                
        return view_func(request, *args, **kwargs)
    return wrapper

def check_follow_limit(view_func):
    """Decorator to enforce follow limit for Free users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied('Please log in to follow users.')
            
        profile = request.user.userprofile
        following_count = request.user.following.count()
        
        if profile.tier == 'free':
            if following_count >= 20:
                messages.warning(request, 'Free tier: Max 20 follows. Upgrade to Premium for unlimited follows!')
                return redirect('setup_tiers')
                
        return view_func(request, *args, **kwargs)
    return wrapper

def premium_required(view_func):
    """Decorator to restrict access to premium users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this feature.')
            return redirect('login')
            
        if request.user.userprofile.tier != 'premium':
            messages.warning(request, 'This feature is only available to Premium users. Upgrade now to access!')
            return redirect('setup_tiers')
            
        return view_func(request, *args, **kwargs)
    return wrapper

def check_ownership(model_class):
    """Decorator factory to check if user owns the object they're trying to modify."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied('Please log in to perform this action.')
                
            # Get object ID from request
            obj_id = kwargs.get('id') or request.POST.get('id')
            if not obj_id:
                raise PermissionDenied('Object ID not provided')
            
            # Get the object
            obj = model_class.objects.get(id=obj_id)
            
            # Check if user owns the object
            if obj.user != request.user:
                # Premium users might have additional permissions
                if request.user.userprofile.tier != 'premium':
                    raise PermissionDenied('You do not have permission to modify this object')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator 