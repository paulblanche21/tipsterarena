"""Views for managing tipster subscriptions."""

import stripe
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import F, Sum
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import timedelta

from ..models import TipsterTier, TipsterSubscription, UserProfile, User

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def become_tipster(request):
    """Handle step 1 of becoming a pro tipster."""
    profile = request.user.userprofile
    
    # Check if already a tipster
    if profile.is_tipster:
        messages.info(request, "You are already a pro tipster!")
        return redirect('tipster_dashboard')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                profile.is_tipster = True
                profile.tipster_description = request.POST.get('description', '').strip()
                profile.tipster_rules = request.POST.get('rules', '').strip()
                
                # Validate inputs
                if not profile.tipster_description:
                    messages.error(request, "Please provide a description of your tipster service.")
                    return render(request, 'core/become_tipster.html', {'profile': profile})
                
                profile.save()
                
                # Store step 1 completion in session
                request.session['pro_setup_step1_complete'] = True
                messages.success(request, "Profile updated successfully! Let's set up your subscription tiers.")
                return redirect('setup_tiers')
                
        except Exception as e:
            logger.error(f"Error in become_tipster: {str(e)}")
            messages.error(request, "An error occurred. Please try again.")
            
    return render(request, 'core/become_tipster.html', {
        'profile': profile
    })

@login_required
def setup_tiers(request):
    """Onboarding: Handle tier selection (Free, Basic, Premium) and trial activation."""
    user_profile = request.user.userprofile
    if request.method == 'POST':
        selected_tier = request.POST.get('tier')
        if selected_tier not in ['free', 'basic', 'premium']:
            messages.error(request, "Invalid tier selection.")
            return render(request, 'core/tier_setup.html')

        # Handle Basic trial
        if selected_tier == 'basic':
            if user_profile.trial_used:
                messages.error(request, "You have already used your Basic trial.")
                return render(request, 'core/tier_setup.html')
            user_profile.tier = 'basic'
            user_profile.tier_expiry = timezone.now() + timezone.timedelta(days=30)
            user_profile.trial_used = True
            user_profile.save()
            messages.success(request, "Your 1-month Basic trial is now active!")
            return redirect('home')
        elif selected_tier == 'premium':
            # In a real app, redirect to payment/upgrade flow
            user_profile.tier = 'premium'
            user_profile.tier_expiry = None  # Set by payment logic
            user_profile.save()
            messages.success(request, "You are now a Premium member!")
            return redirect('home')
        else:
            # Free tier
            user_profile.tier = 'free'
            user_profile.tier_expiry = None
            user_profile.save()
            messages.success(request, "You are now on the Free plan.")
            return redirect('home')

    return render(request, 'core/tier_setup.html')

@login_required
def tier_setup(request):
    """Display the tier setup page with Free and Premium options."""
    return render(request, 'core/tier_setup.html')

@login_required
def tipster_dashboard(request):
    """Dashboard for tipsters to manage their tiers and subscribers."""
    if not request.user.userprofile.is_tipster:
        messages.error(request, "You must be a tipster to access this page")
        return redirect('become_tipster')
        
    try:
        tiers = TipsterTier.objects.filter(tipster=request.user)
        subscriptions = TipsterSubscription.objects.filter(
            tier__tipster=request.user,
            status='active'
        ).select_related('subscriber', 'tier')
        
        # Calculate statistics
        total_subscribers = request.user.userprofile.total_subscribers
        total_revenue = request.user.userprofile.subscription_revenue
        
        return render(request, 'core/tipster_dashboard.html', {
            'tiers': tiers,
            'subscriptions': subscriptions,
            'total_subscribers': total_subscribers,
            'total_revenue': total_revenue,
            'subscription_stats': {
                'active': subscriptions.count(),
                'cancelled': TipsterSubscription.objects.filter(
                    tier__tipster=request.user,
                    status='cancelled'
                ).count(),
                'expired': TipsterSubscription.objects.filter(
                    tier__tipster=request.user,
                    status='expired'
                ).count()
            }
        })
    except Exception as e:
        logger.error(f"Error in tipster_dashboard: {str(e)}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect('home')

@login_required
def manage_tiers(request):
    """Handle CRUD operations for subscription tiers."""
    if not request.user.userprofile.is_tipster:
        return JsonResponse({
            'success': False,
            'error': "You must be a tipster to manage tiers"
        }, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            tier_id = data.get('tier_id')
            action = data.get('action')
            
            if action == 'create':
                # Validate inputs
                name = data.get('name')
                price = data.get('price')
                description = data.get('description')
                features = data.get('features', [])
                max_subscribers = data.get('max_subscribers')
                
                if not all([name, price, description]):
                    return JsonResponse({
                        'success': False,
                        'error': "Please provide all required fields"
                    })
                
                try:
                    price = float(price)
                    if price <= 0:
                        raise ValueError
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': "Invalid price value"
                    })
                
                # Validate features is a list
                if not isinstance(features, list):
                    return JsonResponse({
                        'success': False,
                        'error': "Features must be a list"
                    })
                
                tier = TipsterTier(
                    tipster=request.user,
                    name=name,
                    price=price,
                    description=description,
                    features=features,
                    max_subscribers=max_subscribers
                )
                
                # Validate the model
                try:
                    tier.full_clean()
                    tier.save()
                except ValidationError as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                
                return JsonResponse({
                    'success': True,
                    'tier_id': tier.id
                })
                
            elif action == 'update':
                tier = get_object_or_404(TipsterTier, id=tier_id, tipster=request.user)
                
                # Update fields if provided
                if 'name' in data:
                    tier.name = data['name']
                if 'price' in data:
                    try:
                        price = float(data['price'])
                        if price <= 0:
                            raise ValueError
                        tier.price = price
                    except ValueError:
                        return JsonResponse({
                            'success': False,
                            'error': "Invalid price value"
                        })
                if 'description' in data:
                    tier.description = data['description']
                if 'features' in data:
                    tier.features = data['features']
                if 'max_subscribers' in data:
                    tier.max_subscribers = data['max_subscribers']
                
                tier.save()
                return JsonResponse({'success': True})
                
            elif action == 'delete':
                tier = get_object_or_404(TipsterTier, id=tier_id, tipster=request.user)
                
                # Check if tier has active subscriptions
                if tier.subscriptions.filter(status='active').exists():
                    return JsonResponse({
                        'success': False,
                        'error': "Cannot delete tier with active subscriptions"
                    })
                
                tier.is_active = False
                tier.save()
                return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Error in manage_tiers: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': "An error occurred while managing tiers"
            })
            
    return JsonResponse({
        'success': False,
        'error': "Invalid request method"
    })

@login_required
def subscribe_to_tipster(request, username, tier_id):
    """Handle subscription to a tipster's tier."""
    try:
        tipster = get_object_or_404(User, username=username)
        tier = get_object_or_404(TipsterTier, id=tier_id, tipster=tipster, is_active=True)
        
        # Check if user is trying to subscribe to themselves
        if request.user == tipster:
            return JsonResponse({
                'success': False,
                'error': "You cannot subscribe to your own tier"
            })
        
        # Check if tier is full
        if tier.is_full():
            return JsonResponse({
                'success': False,
                'error': "This tier has reached its subscriber limit"
            })
        
        # Check for existing subscription
        existing_sub = TipsterSubscription.objects.filter(
            subscriber=request.user,
            tier__tipster=tipster,
            status='active'
        ).first()
        
        if existing_sub:
            return JsonResponse({
                'success': False,
                'error': "You already have an active subscription to this tipster"
            })
        
        try:
            # Create or get Stripe customer
            if not request.user.userprofile.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    metadata={
                        'user_id': request.user.id,
                        'username': request.user.username
                    }
                )
                request.user.userprofile.stripe_customer_id = customer.id
                request.user.userprofile.save()
            else:
                customer = stripe.Customer.retrieve(request.user.userprofile.stripe_customer_id)
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': tier.stripe_price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'tier_id': tier.id,
                    'tipster_username': tipster.username
                }
            )
            
            # Create subscription record
            with transaction.atomic():
                # Check again within transaction to prevent race conditions
                if TipsterSubscription.objects.filter(
                    subscriber=request.user,
                    tier__tipster=tipster,
                    status='active'
                ).exists():
                    return JsonResponse({
                        'success': False,
                        'error': "You already have an active subscription to this tipster"
                    })

                # Verify tier is still available
                if TipsterTier.objects.filter(
                    id=tier.id,
                    is_active=True
                ).exclude(
                    max_subscribers__isnull=False,
                    subscriptions__status='active',
                    subscriptions__count__gte=F('max_subscribers')
                ).exists():
                    subscription = TipsterSubscription.objects.create(
                        subscriber=request.user,
                        tier=tier,
                        status='incomplete',
                        end_date=timezone.now() + timezone.timedelta(days=30),
                        stripe_subscription_id=stripe_subscription.id,
                        stripe_customer_id=customer.id
                    )
                    return JsonResponse({
                        'success': True,
                        'subscription_id': subscription.id,
                        'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret
                    })
                else:
                    # Cancel the Stripe subscription since we couldn't create the local subscription
                    stripe.Subscription.delete(stripe_subscription.id)
                    return JsonResponse({
                        'success': False,
                        'error': "This tier is no longer available"
                    })
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error in subscribe_to_tipster: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': "Payment processing error. Please try again."
            })
            
    except Exception as e:
        logger.error(f"Error in subscribe_to_tipster: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': "An error occurred while processing your subscription"
        })

@login_required
def cancel_subscription(request):
    """Cancel Premium subscription."""
    if request.method == 'POST':
        try:
            # Get active subscription
            subscriptions = stripe.Subscription.list(
                customer=request.user.userprofile.stripe_customer_id,
                status='active'
            )
            
            if subscriptions.data:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscriptions.data[0].id,
                    cancel_at_period_end=True
                )
                messages.success(request, 'Your subscription will be cancelled at the end of the billing period.')
            else:
                messages.error(request, 'No active subscription found.')
                
        except Exception as e:
            messages.error(request, f'Error cancelling subscription: {str(e)}')
            
    return redirect('profile', username=request.user.username)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    if event.type == 'customer.subscription.created':
        handle_subscription_created(event.data.object)
    elif event.type == 'customer.subscription.updated':
        handle_subscription_updated(event.data.object)
    elif event.type == 'customer.subscription.deleted':
        handle_subscription_deleted(event.data.object)
    elif event.type == 'invoice.payment_succeeded':
        handle_payment_succeeded(event.data.object)
    elif event.type == 'invoice.payment_failed':
        handle_payment_failed(event.data.object)

    return JsonResponse({'status': 'success'})

def handle_subscription_created(subscription):
    """Handle new subscription creation."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(userprofile__stripe_customer_id=subscription.customer)
        user.userprofile.tier = 'premium'
        user.userprofile.tier_expiry = timezone.now() + timedelta(days=30)
        user.userprofile.save()
    except User.DoesNotExist:
        pass

def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(userprofile__stripe_customer_id=subscription.customer)
        if subscription.status == 'active':
            user.userprofile.tier = 'premium'
            user.userprofile.tier_expiry = timezone.now() + timedelta(days=30)
        elif subscription.status == 'canceled':
            user.userprofile.tier = 'free'
            user.userprofile.tier_expiry = None
        user.userprofile.save()
    except User.DoesNotExist:
        pass

def handle_subscription_deleted(subscription):
    """Handle subscription deletion."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(userprofile__stripe_customer_id=subscription.customer)
        user.userprofile.tier = 'free'
        user.userprofile.tier_expiry = None
        user.userprofile.save()
    except User.DoesNotExist:
        pass

def handle_payment_succeeded(invoice):
    """Handle successful payment."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(userprofile__stripe_customer_id=invoice.customer)
        user.userprofile.tier = 'premium'
        user.userprofile.tier_expiry = timezone.now() + timedelta(days=30)
        user.userprofile.save()
    except User.DoesNotExist:
        pass

def handle_payment_failed(invoice):
    """Handle failed payment."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(userprofile__stripe_customer_id=invoice.customer)
        user.userprofile.tier = 'free'
        user.userprofile.tier_expiry = None
        user.userprofile.save()
    except User.DoesNotExist:
        pass

@login_required
def top_tipsters_leaderboard(request):
    """Display the top tipsters leaderboard."""
    if not request.user.userprofile.tier == 'premium':
        messages.warning(request, 'Premium subscription required to view Top Tipsters.')
        return redirect('tier_setup')
        
    top_tipsters = UserProfile.objects.filter(
        is_tipster=True,
        is_top_tipster=True
    ).order_by('-win_rate', '-total_tips')[:10]
    
    return render(request, 'core/top_tipsters_leaderboard.html', {
        'top_tipsters': top_tipsters
    }) 