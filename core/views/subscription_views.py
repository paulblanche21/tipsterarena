"""Views for managing tipster subscriptions."""

import stripe
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import F, Count, Q, Avg
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

from ..models import TipsterTier, TipsterSubscription, UserProfile, User, Follow

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Set up logging
logger = logging.getLogger(__name__)

class CSRFExemptMixin:
    """Mixin to exempt a view from CSRF verification."""
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class StripeWebhookView(CSRFExemptMixin, View):
    """Handle Stripe webhook events."""
    
    def post(self, request):
        """Process incoming webhook events."""
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
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

class BecomeTipsterView(LoginRequiredMixin, View):
    """Handle step 1 of becoming a pro tipster."""
    
    def get(self, request):
        profile = request.user.userprofile
        return render(request, 'core/become_tipster.html', {
            'profile': profile
        })
    
    def post(self, request):
        profile = request.user.userprofile
        
        # Check if already a tipster
        if profile.is_tipster:
            messages.info(request, "You are already a pro tipster!")
            return redirect('tipster_dashboard')
        
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
                messages.success(request, "Profile updated successfully! You're now a pro tipster.")
                return redirect('home')
                
        except Exception:
            logger.error("Error in become_tipster")
            messages.error(request, "An error occurred. Please try again.")
            return render(request, 'core/become_tipster.html', {'profile': profile})

class SetupTiersView(LoginRequiredMixin, View):
    """Onboarding: Handle subscription activation for €7/month or €70/year."""
    
    def get(self, request):
        return render(request, 'core/tier_setup.html')
    
    def post(self, request):
        user_profile = request.user.userprofile
        plan = request.POST.get('plan', 'monthly')
        
        # All users now get premium access with the single pricing model
        user_profile.tier = 'premium'
        user_profile.tier_expiry = None  # Set by payment logic
        user_profile.save()
        
        if plan == 'yearly':
            messages.success(request, "Welcome to Tipster Arena! You've selected the yearly plan (€70/year) and now have full access to all features.")
        else:
            messages.success(request, "Welcome to Tipster Arena! You've selected the monthly plan (€7/month) and now have full access to all features.")
        
        return redirect('home')

class TipsterDashboardView(LoginRequiredMixin, View):
    """Dashboard for tipsters to manage their tiers and subscribers."""
    
    def get(self, request):
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
        except Exception:
            logger.error("Error in tipster_dashboard")
            messages.error(request, "An error occurred while loading the dashboard.")
            return redirect('home')

class ManageTiersView(LoginRequiredMixin, View):
    """Handle CRUD operations for subscription tiers."""
    
    def get(self, request):
        if not request.user.userprofile.is_tipster:
            return JsonResponse({
                'success': False,
                'error': "You must be a tipster to manage tiers"
            }, status=403)
        return render(request, 'core/manage_tiers.html')
    
    def post(self, request):
        if not request.user.userprofile.is_tipster:
            return JsonResponse({
                'success': False,
                'error': "You must be a tipster to manage tiers"
            }, status=403)
            
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
                tier.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Tier created successfully',
                    'tier': {
                        'id': tier.id,
                        'name': tier.name,
                        'price': tier.price,
                        'description': tier.description,
                        'features': tier.features,
                        'max_subscribers': tier.max_subscribers
                    }
                })
            
            elif action == 'update':
                tier = get_object_or_404(TipsterTier, id=tier_id, tipster=request.user)
                # Update tier fields
                tier.name = data.get('name', tier.name)
                tier.description = data.get('description', tier.description)
                tier.features = data.get('features', tier.features)
                tier.max_subscribers = data.get('max_subscribers', tier.max_subscribers)
                
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
                
                tier.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Tier updated successfully'
                })
            
            elif action == 'delete':
                tier = get_object_or_404(TipsterTier, id=tier_id, tipster=request.user)
                tier.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Tier deleted successfully'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': "Invalid action"
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error in manage_tiers: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': "An error occurred while processing your request"
            }, status=500)

class SubscribeToTipsterView(LoginRequiredMixin, View):
    """Handle subscribing to a tipster's tier."""
    
    def post(self, request, username, tier_id):
        try:
            tipster = get_object_or_404(User, username=username)
            tier = get_object_or_404(TipsterTier, id=tier_id, tipster=tipster)
            
            # Check if already subscribed
            existing_sub = TipsterSubscription.objects.filter(
                subscriber=request.user,
                tier=tier,
                status='active'
            ).first()
            
            if existing_sub:
                return JsonResponse({
                    'success': False,
                    'error': "You are already subscribed to this tier"
                })
            
            # Check if tier has reached max subscribers
            if tier.max_subscribers and tier.subscriptions.filter(status='active').count() >= tier.max_subscribers:
                return JsonResponse({
                    'success': False,
                    'error': "This tier has reached its maximum number of subscribers"
                })
            
            # Create subscription
            subscription = TipsterSubscription.objects.create(
                subscriber=request.user,
                tier=tier,
                status='active',
                start_date=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Successfully subscribed to tipster',
                'subscription': {
                    'id': subscription.id,
                    'tier_name': tier.name,
                    'price': tier.price,
                    'start_date': subscription.start_date.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error in subscribe_to_tipster: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': "An error occurred while processing your subscription"
            }, status=500)

class CancelSubscriptionView(LoginRequiredMixin, View):
    """Handle cancellation of a subscription."""
    
    def post(self, request):
        try:
            subscription_id = request.POST.get('subscription_id')
            if not subscription_id:
                return JsonResponse({
                    'success': False,
                    'error': "Subscription ID is required"
                }, status=400)
            
            subscription = get_object_or_404(
                TipsterSubscription,
                id=subscription_id,
                subscriber=request.user
            )
            
            # Update subscription status
            subscription.status = 'cancelled'
            subscription.end_date = timezone.now()
            subscription.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Subscription cancelled successfully'
            })
            
        except Exception as e:
            logger.error(f"Error in cancel_subscription: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': "An error occurred while cancelling your subscription"
            }, status=500)

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
            user.userprofile.tier = 'premium'  # Keep premium since there's no free tier
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
        user.userprofile.tier = 'premium'  # Keep premium since there's no free tier
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
        user.userprofile.tier = 'premium'  # Keep premium since there's no free tier
        user.userprofile.tier_expiry = None
        user.userprofile.save()
    except User.DoesNotExist:
        pass

class TopTipstersLeaderboardView(LoginRequiredMixin, View):
    """Display the top tipsters leaderboard with comprehensive scoring and revenue sharing."""
    
    def get(self, request):
        try:
            # Get all tipsters with minimum activity - simplified approach
            tipsters = User.objects.filter(
                userprofile__is_tipster=True
            ).prefetch_related('tip', 'followers', 'tip__likes', 'tip__comments', 'tip__shares')
            
            # Calculate comprehensive scores for each tipster
            tipsters_data = []
            for tipster in tipsters:
                profile = tipster.userprofile
                
                # Get tip statistics
                tips = tipster.tip.all()
                total_tips = tips.count()
                
                if total_tips < 5:  # Skip tipsters with less than 5 tips
                    continue
                
                # Calculate win/loss statistics
                wins = tips.filter(status='win').count()
                losses = tips.filter(status='loss').count()
                dead_heats = tips.filter(status='dead_heat').count()
                void_tips = tips.filter(status='void_non_runner').count()
                total_verified = tips.filter(status__in=['win', 'loss', 'dead_heat', 'void_non_runner']).count()
                
                # Calculate win rate
                win_rate = (wins / total_verified * 100) if total_verified > 0 else 0
                
                # Get engagement statistics
                total_likes = sum(tip.likes.count() for tip in tips)
                total_comments = sum(tip.comments.count() for tip in tips)
                total_shares = sum(tip.shares.count() for tip in tips)
                engagement_score = (total_likes * 1) + (total_comments * 2) + (total_shares * 3)
                
                # Calculate consistency score (recent activity)
                thirty_days_ago = timezone.now() - timedelta(days=30)
                recent_tips = tips.filter(created_at__gte=thirty_days_ago).count()
                consistency_score = min(recent_tips * 10, 100)  # Max 100 points for recent activity
                
                # Calculate confidence score
                confidence_tips = tips.exclude(confidence__isnull=True)
                avg_confidence = confidence_tips.aggregate(Avg('confidence'))['confidence__avg'] or 0
                confidence_score = (avg_confidence / 5) * 50  # Max 50 points for confidence
                
                # Calculate comprehensive score
                base_score = win_rate * 2  # Win rate is most important (0-200 points)
                volume_score = min(total_tips * 2, 100)  # Volume bonus (0-100 points)
                engagement_bonus = min(engagement_score / 10, 50)  # Engagement bonus (0-50 points)
                
                total_score = base_score + volume_score + engagement_bonus + consistency_score + confidence_score
                
                tipsters_data.append({
                    'username': tipster.username,
                    'handle': profile.handle or tipster.username,
                    'avatar_url': profile.avatar.url if profile.avatar else None,
                    'total_tips': total_tips,
                    'wins': wins,
                    'losses': losses,
                    'dead_heats': dead_heats,
                    'void_tips': void_tips,
                    'win_rate': round(win_rate, 1),
                    'total_verified': total_verified,
                    'followers_count': tipster.followers.count(),
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'avg_confidence': round(avg_confidence, 1) if avg_confidence else 0,
                    'recent_tips': recent_tips,
                    'total_score': round(total_score, 0),
                    'is_top_tipster': profile.is_top_tipster,
                    'top_tipster_since': profile.top_tipster_since,
                    'total_earnings': profile.total_earnings,
                    'monthly_earnings': profile.monthly_earnings,
                    'revenue_share_percentage': profile.revenue_share_percentage,
                    'is_current_user': tipster == request.user
                })
            
            # Sort by total score (highest first)
            tipsters_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Add ranking and top 20 status
            for i, tipster in enumerate(tipsters_data):
                tipster['rank'] = i + 1
                tipster['is_top_20'] = i < 20
                
                # Calculate estimated monthly revenue for top 20
                if i < 20:
                    # Simple revenue sharing calculation (20% of monthly revenue split among top 20)
                    # This is a placeholder - you'd implement actual revenue calculation
                    base_revenue = 1000  # Example monthly revenue
                    tipster['estimated_monthly_revenue'] = round((base_revenue * 0.2) / 20, 2)
                else:
                    tipster['estimated_monthly_revenue'] = 0
            
            # Get current user's position
            current_user_position = None
            current_user_data = None
            for tipster in tipsters_data:
                if tipster['is_current_user']:
                    current_user_position = tipster['rank']
                    current_user_data = tipster
                    break
            
            # Calculate leaderboard statistics
            total_tipsters = len(tipsters_data)
            active_tipsters = len([t for t in tipsters_data if t['recent_tips'] > 0])
            avg_win_rate = sum(t['win_rate'] for t in tipsters_data) / len(tipsters_data) if tipsters_data else 0
            
            return render(request, 'core/top_tipsters.html', {
                'tipsters': tipsters_data[:50],  # Show top 50
                'current_user_position': current_user_position,
                'current_user_data': current_user_data,
                'total_tipsters': total_tipsters,
                'active_tipsters': active_tipsters,
                'avg_win_rate': round(avg_win_rate, 1),
                'revenue_pool': 1000,  # Example monthly revenue pool
                'revenue_share_percentage': 20,  # 20% shared among top 20
            })
            
        except Exception as e:
            logger.error(f"Error in top_tipsters_leaderboard: {str(e)}")
            messages.error(request, "An error occurred while loading the leaderboard.")
            return redirect('home') 