# middleware.py
from django.shortcuts import redirect
from django.urls import resolve

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