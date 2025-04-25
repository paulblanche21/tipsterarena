# middleware.py
from django.shortcuts import redirect

class PaywallMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.user.userprofile
            excluded_paths = ['/signup/', '/kyc/', '/profile-setup/', '/profile-setup/skip/', '/payment/', '/payment/success/', '/payment/skip/', '/logout/']
            if not any(request.path.startswith(path) for path in excluded_paths):
                if not profile.kyc_completed:
                    return redirect('kyc')
                if not profile.profile_completed:
                    return redirect('profile_setup')
                if not profile.payment_completed:
                    return redirect('payment')
        return self.get_response(request)