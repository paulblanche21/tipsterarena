"""
Middleware Components for Tipster Arena.

This module contains custom middleware classes that handle various aspects of request
processing and access control in the Tipster Arena application. The middleware
components are responsible for enforcing business rules and managing user access
to different features of the platform.

Available Middleware:
1. PaywallMiddleware
   - Controls access to features based on user profile completion status
   - Enforces three levels of access control:
     * KYC (Know Your Customer) verification
     * Profile completion
     * Payment completion
   - Maintains a list of excluded paths that are always accessible
   - Redirects users to appropriate setup pages when required

Access Control Rules:
   - KYC Required For:
     * Posting tips
     * Following users
     * Liking content
     * Commenting
   - Profile Completion Required For:
     * Messaging
     * Following users
   - Payment Required For:
     * Premium features
     * Analytics access

Excluded Paths (Always Accessible):
   - Authentication: /signup/, /logout/
   - Setup: /kyc/, /profile-setup/, /payment/
   - Static: /static/, /media/
   - API: /api/current-user/
   - Core Features: /search/, /home/, /sport/, /profile/

Usage:
    Add the middleware to MIDDLEWARE setting in settings.py:
    
    MIDDLEWARE = [
        'core.middleware.PaywallMiddleware',
        # ... other middleware classes
    ]

Note:
    The middleware only applies to authenticated users. Unauthenticated users
    are not affected by these access controls.
"""

# middleware.py
from django.shortcuts import redirect


class PaywallMiddleware:
    """Middleware to control access to features based on user profile completion."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.user.userprofile
            
            # Basic paths that should always be accessible
            excluded_paths = [
                '/signup/', 
                '/kyc/', 
                '/profile-setup/', 
                '/profile-setup/skip/', 
                '/payment/', 
                '/payment/success/', 
                '/payment/skip/', 
                '/logout/',
                '/static/',
                '/media/',
                '/api/current-user/',  # Allow current user API
                '/search/',
                '/home/',
                '/sport/',  # Allow viewing sports
                '/profile/',  # Allow viewing profiles
            ]
            
            # Check if current path is excluded
            current_path = request.path.rstrip('/')
            if not any(current_path.startswith(path.rstrip('/')) for path in excluded_paths):
                # Only enforce KYC for posting and following actions
                if not profile.kyc_completed and request.method == 'POST':
                    if any(current_path.startswith(path) for path in ['/post/', '/follow/', '/like/', '/comment/']):
                        return redirect('kyc')
                
                # Only enforce profile completion for social features
                if not profile.profile_completed and any(current_path.startswith(path) for path in ['/messages/', '/follow/']):
                    return redirect('profile_setup')
                
                # Only enforce payment for premium features
                if not profile.payment_completed and any(current_path.startswith(path) for path in ['/premium/', '/analytics/']):
                    return redirect('payment')
                    
        return self.get_response(request)