"""Views for managing tipster subscriptions."""

import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.exceptions import PermissionDenied

from ..models import TipsterTier, TipsterSubscription, UserProfile
from ..decorators import premium_required

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
@premium_required
def become_tipster(request):
    """Handle requests to become a tipster."""
    profile = request.user.userprofile
    
    if request.method == 'POST':
        profile.is_tipster = True
        profile.tipster_description = request.POST.get('description', '')
        profile.tipster_rules = request.POST.get('rules', '')
        profile.minimum_tier_price = request.POST.get('min_price', 5.00)
        profile.maximum_tier_price = request.POST.get('max_price', 100.00)
        profile.save()
        
        return redirect('tipster_dashboard')
        
    return render(request, 'core/become_tipster.html', {
        'profile': profile
    })

@login_required
def tipster_dashboard(request):
    """Dashboard for tipsters to manage their tiers and subscribers."""
    if not request.user.userprofile.is_tipster:
        raise PermissionDenied("You must be a tipster to access this page")
        
    tiers = TipsterTier.objects.filter(tipster=request.user)
    subscriptions = TipsterSubscription.objects.filter(
        tier__tipster=request.user,
        status='active'
    )
    
    return render(request, 'core/tipster_dashboard.html', {
        'tiers': tiers,
        'subscriptions': subscriptions,
        'total_subscribers': request.user.userprofile.total_subscribers,
        'total_revenue': request.user.userprofile.subscription_revenue
    })

@login_required
def manage_tiers(request):
    """Handle CRUD operations for subscription tiers."""
    if not request.user.userprofile.is_tipster:
        raise PermissionDenied("You must be a tipster to manage tiers")
        
    if request.method == 'POST':
        tier_id = request.POST.get('tier_id')
        action = request.POST.get('action')
        
        if action == 'create':
            tier = TipsterTier.objects.create(
                tipster=request.user,
                name=request.POST.get('name'),
                price=request.POST.get('price'),
                description=request.POST.get('description'),
                features=request.POST.getlist('features'),
                max_subscribers=request.POST.get('max_subscribers')
            )
            return JsonResponse({'success': True, 'tier_id': tier.id})
            
        elif action == 'update':
            tier = get_object_or_404(TipsterTier, id=tier_id, tipster=request.user)
            tier.name = request.POST.get('name')
            tier.price = request.POST.get('price')
            tier.description = request.POST.get('description')
            tier.features = request.POST.getlist('features')
            tier.max_subscribers = request.POST.get('max_subscribers')
            tier.save()
            return JsonResponse({'success': True})
            
        elif action == 'delete':
            tier = get_object_or_404(TipsterTier, id=tier_id, tipster=request.user)
            tier.is_active = False
            tier.save()
            return JsonResponse({'success': True})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def subscribe_to_tipster(request, username, tier_id):
    """Handle subscription to a tipster's tier."""
    tier = get_object_or_404(TipsterTier, id=tier_id, is_active=True)
    
    # Check if user already has an active subscription to this tipster
    existing_sub = TipsterSubscription.objects.filter(
        subscriber=request.user,
        tier__tipster=tier.tipster,
        status='active'
    ).first()
    
    if existing_sub:
        return JsonResponse({
            'success': False,
            'error': 'You already have an active subscription to this tipster'
        })
    
    try:
        # Create Stripe subscription
        stripe_subscription = stripe.Subscription.create(
            customer=request.user.userprofile.stripe_customer_id,
            items=[{'price': tier.stripe_price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )
        
        # Create subscription record
        with transaction.atomic():
            subscription = TipsterSubscription.objects.create(
                subscriber=request.user,
                tier=tier,
                end_date=timezone.now() + timezone.timedelta(days=30),
                stripe_subscription_id=stripe_subscription.id
            )
            
            # Update tipster stats
            profile = tier.tipster.userprofile
            profile.total_subscribers += 1
            profile.subscription_revenue += tier.price
            profile.save()
            
        return JsonResponse({
            'success': True,
            'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def cancel_subscription(request, subscription_id):
    """Handle subscription cancellation."""
    subscription = get_object_or_404(
        TipsterSubscription,
        id=subscription_id,
        subscriber=request.user,
        status='active'
    )
    
    try:
        # Cancel Stripe subscription
        stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update subscription record
        subscription.status = 'cancelled'
        subscription.save()
        
        # Update tipster stats
        profile = subscription.tier.tipster.userprofile
        profile.total_subscribers -= 1
        profile.subscription_revenue -= subscription.tier.price
        profile.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 