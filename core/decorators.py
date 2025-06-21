"""
Custom Decorators for Tipster Arena.

This module provides a collection of decorators that handle various aspects of
permission control, rate limiting, and access restrictions in the Tipster Arena
application. These decorators are used to enforce business rules and maintain
the integrity of the platform's features.

Available Decorators:
1. check_daily_tip_limit
   - All users have unlimited tips with the single pricing model
   - Raises PermissionDenied if user is not authenticated

2. check_follow_limit
   - All users can follow unlimited users with the single pricing model
   - Raises PermissionDenied if user is not authenticated

3. premium_required
   - All users have full access with the single pricing model
   - Verifies user is authenticated
   - Raises PermissionDenied for non-authenticated users

4. check_ownership
   - Factory decorator that verifies object ownership
   - Ensures users can only modify their own content
   - Supports both direct object access and POST requests
   - All users have the same permissions with the single pricing model

Usage Examples:
    @check_daily_tip_limit
    def create_tip(request):
        # Only executed if user is authenticated
        pass

    @premium_required
    def full_access_feature(request):
        # Only accessible to authenticated users
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
    """Decorator to check user authentication for posting tips."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied('Please log in to post tips.')
            
        # All users now have unlimited tips with the single pricing model
        return view_func(request, *args, **kwargs)
    return wrapper

def check_follow_limit(view_func):
    """Decorator to check user authentication for following users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied('Please log in to follow users.')
            
        # All users now have unlimited follows with the single pricing model
        return view_func(request, *args, **kwargs)
    return wrapper

def premium_required(view_func):
    """Decorator to check user authentication for full access features."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this feature.')
            return redirect('login')
            
        # All users now have full access with the single pricing model
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
                # All users now have the same permissions with the single pricing model
                raise PermissionDenied('You do not have permission to modify this object')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator 