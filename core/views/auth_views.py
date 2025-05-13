"""Authentication related views for Tipster Arena."""

import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import Group

from ..forms import CustomUserCreationForm, KYCForm, UserProfileForm

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def login_view(request):
    """Handle user authentication and login."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def signup_view(request):
    """Handle user registration and account creation."""
    if request.method == 'POST':
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
                
                # Add user to basic permissions group
                basic_group, _ = Group.objects.get_or_create(name='Basic Users')
                user.groups.add(basic_group)
                
                # Log user in
                login(request, user)
                return redirect('kyc')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def kyc_view(request):
    """Handle KYC (Know Your Customer) verification process."""
    if request.user.userprofile.kyc_completed:
        return redirect('profile_setup')
    if request.method == 'POST':
        form = KYCForm(request.POST)
        if form.is_valid():
            profile = request.user.userprofile
            profile.full_name = form.cleaned_data['full_name']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.location = form.cleaned_data['address']
            profile.kyc_completed = True
            profile.save()
            return redirect('profile_setup')
    else:
        form = KYCForm()
    return render(request, 'core/kyc.html', {'form': form})

@login_required
def profile_setup_view(request):
    """Handle user profile setup and customization."""
    if request.user.userprofile.profile_completed:
        return redirect('payment')
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            request.user.userprofile.profile_completed = True
            request.user.userprofile.save()
            return redirect('payment')
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    return render(request, 'core/profile_setup.html', {'form': form})

@login_required
def skip_profile_setup(request):
    """Allow users to skip profile setup and proceed to payment."""
    if not request.user.userprofile.profile_completed:
        request.user.userprofile.profile_completed = True
        request.user.userprofile.save()
    return redirect('payment')

@login_required
def payment_view(request):
    """Handle payment processing and subscription setup."""
    if request.user.userprofile.payment_completed:
        return redirect('home')
    return render(request, 'core/payment.html', {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })

@login_required
def create_checkout_session(request):
    """Create a Stripe checkout session for subscription payment."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    data = json.loads(request.body)
    plan = data.get('plan')
    payment_method_id = data.get('payment_method_id')

    if not plan or not payment_method_id:
        return JsonResponse({'error': 'Missing plan or payment method'}, status=400)

    try:
        if not request.user.userprofile.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                payment_method=payment_method_id,
                invoice_settings={'default_payment_method': payment_method_id},
            )
            request.user.userprofile.stripe_customer_id = customer.id
            request.user.userprofile.save()
        else:
            customer = stripe.Customer.retrieve(request.user.userprofile.stripe_customer_id)

        price_id = settings.STRIPE_MONTHLY_PRICE_ID if plan == 'monthly' else settings.STRIPE_YEARLY_PRICE_ID
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            subscription_data={
                'items': [{'price': price_id}],
            },
            mode='subscription',
            success_url=request.build_absolute_uri('/payment/success/'),
            cancel_url=request.build_absolute_uri('/payment/'),
        )
        return JsonResponse({'session_id': session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def payment_success(request):
    """Handle successful payment completion."""
    request.user.userprofile.payment_completed = True
    request.user.userprofile.save()
    return redirect('home')

@login_required
def skip_payment(request):
    """Allow users to skip payment and proceed to home page."""
    if not request.user.userprofile.payment_completed:
        request.user.userprofile.payment_completed = True
        request.user.userprofile.save()
    return redirect('home') 