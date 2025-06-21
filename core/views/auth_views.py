"""Authentication related views for Tipster Arena."""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
import logging
from django.contrib import messages
import json

from ..forms import CustomUserCreationForm, KYCForm, UserProfileForm
from ..models import EmailVerificationToken

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Set up logging
logger = logging.getLogger(__name__)

class LoginView(View):
    """Handle user authentication and login."""
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = AuthenticationForm()
        return render(request, 'core/login.html', {'form': form})
    
    def post(self, request):
        # Rate limiting
        ip = request.META.get('REMOTE_ADDR')
        cache_key = f'login_attempts_{ip}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 5:  # Maximum 5 attempts
            return JsonResponse({
                'error': 'Too many login attempts. Please try again later.'
            }, status=429)
        
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Reset attempts on successful login
                cache.delete(cache_key)
                return redirect('home')
            else:
                # Increment failed attempts
                cache.set(cache_key, attempts + 1, 300)  # Store for 5 minutes
        return render(request, 'core/login.html', {'form': form})

class SignupView(View):
    """Handle user registration and account creation."""
    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, 'core/signup.html', {'form': form})
    
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create user
                user = form.save()
                
                # Update user profile handle (profile should be created by signal)
                handle = form.cleaned_data.get('handle')
                if not handle.startswith('@'):
                    handle = f"@{handle}"
                profile = user.userprofile  # Should exist due to signal
                profile.handle = handle
                profile.save()
                
                # Add user to premium permissions group
                premium_group, _ = Group.objects.get_or_create(name='Premium Users')
                user.groups.add(premium_group)
                
                # Create and send verification email
                token = get_random_string(length=32)
                EmailVerificationToken.objects.create(user=user, token=token)
                
                verification_url = request.build_absolute_uri(
                    f'/verify-email/{token}/'
                )
                
                # Send verification email
                subject = 'Verify your Tipster Arena account'
                html_message = render_to_string('core/email/verify_email.html', {
                    'user': user,
                    'verification_url': verification_url,
                })
                plain_message = f'Please verify your account by clicking this link: {verification_url}'
                
                try:
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    logger.info(f"Verification email sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
                    messages.warning(request, "Account created but verification email could not be sent. Please contact support.")
                
                # Log user in
                login(request, user)
                messages.info(request, "Please check your email to verify your account.")
                return redirect('kyc')
        return render(request, 'core/signup.html', {'form': form})

class EmailVerificationView(View):
    """Handle email verification."""
    def get(self, request, token):
        try:
            verification = EmailVerificationToken.objects.get(
                token=token,
                is_used=False
            )
            
            # Mark token as used
            verification.is_used = True
            verification.save()
            
            # Update user profile
            user = verification.user
            user.userprofile.email_verified = True
            user.userprofile.save()
            
            messages.success(request, "Your email has been verified successfully!")
            logger.info(f"Email verified for user {user.username}")
            
            if request.user.is_authenticated:
                return redirect('home')
            else:
                return redirect('login')
                
        except EmailVerificationToken.DoesNotExist:
            messages.error(request, "Invalid or expired verification link.")
            logger.warning(f"Invalid verification attempt with token: {token}")
            return redirect('login')
        except Exception as e:
            messages.error(request, "An error occurred during verification.")
            logger.error(f"Error during email verification: {str(e)}")
            return redirect('login')

class KYCView(LoginRequiredMixin, View):
    """Handle KYC (Know Your Customer) verification process."""
    def get(self, request):
        if request.user.userprofile.kyc_completed:
            return redirect('profile_setup')
        form = KYCForm()
        return render(request, 'core/kyc.html', {'form': form})
    
    def post(self, request):
        if request.user.userprofile.kyc_completed:
            return redirect('profile_setup')
        form = KYCForm(request.POST)
        if form.is_valid():
            profile = request.user.userprofile
            profile.full_name = form.cleaned_data['full_name']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.location = form.cleaned_data['address']
            profile.kyc_completed = True
            profile.save()
            return redirect('profile_setup')
        return render(request, 'core/kyc.html', {'form': form})

class ProfileSetupView(LoginRequiredMixin, View):
    """Handle user profile setup after KYC."""
    def get(self, request):
        if not request.user.userprofile.kyc_completed:
            return redirect('kyc')
        if request.user.userprofile.profile_completed:
            return redirect('payment')
        form = UserProfileForm()
        return render(request, 'core/profile_setup.html', {'form': form})
    
    def post(self, request):
        if not request.user.userprofile.kyc_completed:
            return redirect('kyc')
        if request.user.userprofile.profile_completed:
            return redirect('payment')
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = request.user.userprofile
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            if 'banner' in request.FILES:
                profile.banner = request.FILES['banner']
            profile.profile_completed = True
            profile.save()
            return redirect('payment')
        return render(request, 'core/profile_setup.html', {'form': form})

class SkipProfileSetupView(LoginRequiredMixin, View):
    """Allow users to skip profile setup."""
    def get(self, request):
        if not request.user.userprofile.kyc_completed:
            return redirect('kyc')
        profile = request.user.userprofile
        profile.profile_completed = True
        profile.save()
        return redirect('payment')
    
    def post(self, request):
        if not request.user.userprofile.kyc_completed:
            return redirect('kyc')
        profile = request.user.userprofile
        profile.profile_completed = True
        profile.save()
        return redirect('payment')

class PaymentView(LoginRequiredMixin, View):
    """Handle payment page display."""
    def get(self, request):
        if not request.user.userprofile.profile_completed:
            return redirect('profile_setup')
        if request.user.userprofile.payment_completed:
            return redirect('home')
        return render(request, 'core/payment.html', {
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        })

class CreateCheckoutSessionView(LoginRequiredMixin, View):
    """Create a Stripe checkout session."""
    def post(self, request):
        if not request.user.userprofile.profile_completed:
            return redirect('profile_setup')
        if request.user.userprofile.payment_completed:
            return redirect('home')
        
        try:
            data = json.loads(request.body) if request.body else request.POST
            plan = data.get('plan', 'monthly')
            
            logger.info(f"Creating checkout session for user {request.user.username} with plan: {plan}")
            
            # Select the appropriate price ID based on plan
            if plan == 'yearly':
                price_id = settings.STRIPE_YEARLY_PRICE_ID
            else:
                price_id = settings.STRIPE_MONTHLY_PRICE_ID
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri('/payment/success/'),
                cancel_url=request.build_absolute_uri('/payment/'),
                client_reference_id=str(request.user.id),
            )
            logger.info(f"Checkout session created successfully: {checkout_session.id}")
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

class PaymentSuccessView(LoginRequiredMixin, View):
    """Handle successful payment completion."""
    def get(self, request):
        if not request.user.userprofile.profile_completed:
            return redirect('profile_setup')
        try:
            logger.info(f"Processing payment success for user {request.user.username}")
            profile = request.user.userprofile
            profile.payment_completed = True
            profile.tier = 'premium'
            profile.save()
            logger.info(f"Payment completed successfully for user {request.user.username}")
            return redirect('home')
        except Exception as e:
            logger.error(f"Error processing payment success: {str(e)}")
            return redirect('payment')

class SkipPaymentView(LoginRequiredMixin, View):
    """Allow users to skip payment (for testing)."""
    def get(self, request):
        profile = request.user.userprofile
        if profile.profile_completed:
            profile.payment_completed = True
            profile.tier = 'premium'
            profile.save()
            return redirect('home')
        return redirect('payment')

    def post(self, request):
        profile = request.user.userprofile
        if profile.profile_completed:
            profile.payment_completed = True
            profile.tier = 'premium'
            profile.save()
            return redirect('home')
        return redirect('payment') 