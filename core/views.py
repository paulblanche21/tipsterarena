"""Core views for the Tipster Arena application.

This module contains all the view functions and classes that handle HTTP requests
and responses for the Tipster Arena application, including user interactions,
sports events, and social features.
"""

from datetime import datetime, timedelta
import json
import logging
import time

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, F, Q
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator


from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import api_view, permission_classes

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import bleach
import pytz
import stripe

from .models import (
    Tip, Like, Follow, Share, UserProfile, Comment, MessageThread, RaceMeeting, Message, TennisEvent,
    FootballLeague, FootballTeam, TeamStats, FootballEvent, KeyEvent, BettingOdds, DetailedStats,
    GolfCourse, GolfEvent, GolfPlayer, GolfTour, LeaderboardEntry, Notification
)
from .serializers import GolfEventSerializer, FootballEventSerializer
from .forms import UserProfileForm, CustomUserCreationForm, KYCForm
from .horse_racing_events import get_racecards_json

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

def landing(request):
    """Render the landing page for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/landing.html')

def signup_view(request):
    """Handle user registration and account creation."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
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

    
# View for user login
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

# View for the home page
@login_required
def home(request):
    """Render the home page with tips, trending content, and user suggestions."""
    tips = Tip.objects.all().order_by('-created_at')[:20]
    for tip in tips:
        if not hasattr(tip.user, 'userprofile'):
            UserProfile.objects.get_or_create(user=tip.user)

    trending_tips = Tip.objects.annotate(
        total_likes=Count('likes'),
        total_shares=Count('shares')
    ).annotate(
        total_engagement=F('total_likes') + F('total_shares')
    ).order_by('-total_engagement')[:4]

    for tip in trending_tips:
        if not hasattr(tip.user, 'userprofile'):
            UserProfile.objects.get_or_create(user=tip.user)

    current_user = request.user
    followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
    suggested_users = User.objects.filter(
        tip__isnull=False
    ).exclude(
        id__in=followed_users
    ).exclude(
        id=current_user.id
    ).distinct()[:2]

    suggested_tipsters = []
    for user in suggested_users:
        try:
            profile = user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            bio = profile.description or "No bio available"
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
            bio = "No bio available"
        suggested_tipsters.append({
            'username': user.username,
            'avatar': avatar_url,
            'bio': bio,
        })

    context = {
        'tips': tips,
        'trending_tips': trending_tips,
        'suggested_tipsters': suggested_tipsters,
    }
    return render(request, 'core/home.html', context)

# View for sport-specific pages
def sport_view(request, sport):
    """Render sport-specific page with relevant tips."""
    valid_sports = ['football', 'golf', 'tennis', 'horse_racing']
    if sport not in valid_sports:
        return render(request, 'core/404.html', status=404)

    tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]
    return render(request, 'core/sport.html', {
        'tips': tips,
        'sport': sport,
    })

# View for the explore page
def explore(request):
    """Render explore page with latest tips from all sports."""
    tips = Tip.objects.all().order_by('-created_at')[:20]
    for tip in tips:
        if not hasattr(tip.user, 'userprofile'):
            UserProfile.objects.get_or_create(user=tip.user)

    context = {
        'tips': tips,
    }
    return render(request, 'core/explore.html', context)

# View to handle following a user
@login_required
@require_POST
def follow_user(request):
    """Handle following/unfollowing a user."""
    username = request.POST.get('username')
    user_to_follow = get_object_or_404(User, username=username)
    profile = user_to_follow.profile
    if request.user == user_to_follow:
        return JsonResponse({'success': False, 'message': 'Cannot follow yourself'})
    if profile.followers.filter(id=request.user.id).exists():
        profile.followers.remove(request.user)
        return JsonResponse({'success': True, 'message': 'Unfollowed', 'is_following': False})
    else:
        profile.followers.add(request.user)
        return JsonResponse({'success': True, 'message': 'Followed', 'is_following': True})

@login_required
def profile(request, username):
    """Render user profile page with tips and statistics."""
    user = get_object_or_404(User, username=username)
    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.get_or_create(user=user)[0]

    # Filter user's own tips and retweeted tips
    user_tips = Tip.objects.filter(
        Q(user=user) | Q(shares__user=user)
    ).order_by('-created_at').select_related('user__userprofile').distinct()

    following_count = Follow.objects.filter(follower=user).count()
    followers_count = Follow.objects.filter(followed=user).count()

    is_owner = request.user == user
    form = UserProfileForm(instance=user_profile) if is_owner else None
    is_following = False if is_owner else Follow.objects.filter(follower=request.user, followed=user).exists()

    # Existing stats
    win_rate = user_profile.win_rate
    total_tips = user_profile.total_tips
    wins = user_profile.wins

    # Calculate average odds
    user_own_tips = Tip.objects.filter(user=user)
    average_odds = None
    print(f"User tips count: {user_own_tips.count()}")
    if user_own_tips.exists():
        total_odds = 0
        valid_tips = 0
        for tip in user_own_tips:
            print(f"Processing tip ID {tip.id}: Odds = {tip.odds}, Format = {tip.odds_format}")
            try:
                if tip.odds_format.lower() == 'decimal':
                    odds_value = float(tip.odds)
                elif tip.odds_format.lower() == 'fractional':
                    numerator, denominator = map(float, tip.odds.split('/'))
                    odds_value = (numerator / denominator) + 1
                else:
                    print(f"  Skipping tip ID {tip.id}: Invalid odds format '{tip.odds_format}'")
                    continue
                total_odds += odds_value
                valid_tips += 1
                print(f"  Valid tip ID {tip.id}: Odds value = {odds_value}, Running total = {total_odds}")
            except (ValueError, ZeroDivisionError) as e:
                print(f"  Skipping tip ID {tip.id}: Error parsing odds - {str(e)}")
                continue
        if valid_tips > 0:
            average_odds = total_odds / valid_tips
            print(f"Average odds calculated: {average_odds} (Total odds: {total_odds}, Valid tips: {valid_tips})")
        else:
            print("No valid tips for average odds calculation")
    else:
        print("No tips found for user")

    return render(request, 'core/profile.html', {
        'user': user,
        'user_profile': user_profile,
        'user_tips': user_tips,
        'following_count': following_count,
        'followers_count': followers_count,
        'form': form,
        'is_owner': is_owner,
        'is_following': is_following,
        'win_rate': win_rate,
        'total_tips': total_tips,
        'wins': wins,
        'average_odds': average_odds,
    })

# View to handle profile editing
@login_required
def profile_edit_view(request, username):
    """Handle user profile editing and updates."""
    user = get_object_or_404(User, username=username)
    if request.user.username != username:
        return redirect('profile', username=username)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user.userprofile)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid form data'})
    else:
        form = UserProfileForm(instance=user.userprofile)
    return render(request, 'core/profile.html', {'form': form, 'user_profile': user.userprofile})

# View to handle liking a tip
@login_required
@require_POST
def like_tip(request):
    """Handle liking and unliking tips."""
    tip_id = request.POST.get('tip_id')
    tip = get_object_or_404(Tip, id=tip_id)
    user = request.user

    like, created = Like.objects.get_or_create(user=user, tip=tip)
    if created:
        return JsonResponse({'success': True, 'message': 'Tip liked', 'like_count': tip.likes.count()})
    else:
        like.delete()
        return JsonResponse({'success': True, 'message': 'Like removed', 'like_count': tip.likes.count()})

# View to handle sharing a tip
@login_required
@require_POST
def share_tip(request):
    """Handle sharing and unsharing tips."""
    tip_id = request.POST.get('tip_id')
    tip = get_object_or_404(Tip, id=tip_id)
    user = request.user

    share, created = Share.objects.get_or_create(user=user, tip=tip)
    if created:
        return JsonResponse({'success': True, 'message': 'Tip shared', 'share_count': tip.shares.count()})
    else:
        share.delete()
        return JsonResponse({'success': True, 'message': 'Share removed', 'share_count': tip.shares.count()})

# View to handle commenting on a tip
@login_required
@require_POST
def comment_tip(request):
    """Handle adding comments to tips."""
    tip_id = request.POST.get('tip_id')
    comment_text = request.POST.get('comment_text', '')
    parent_id = request.POST.get('parent_id')
    gif_url = request.POST.get('gif', '')
    logger.info("Received comment_tip request: tip_id=%s, comment_text=%s, parent_id=%s", tip_id, comment_text, parent_id)

    if not tip_id:
        logger.error("Missing tip_id: tip_id=%s", tip_id)
        return JsonResponse({'success': False, 'error': 'Missing tip_id'}, status=400)

    try:
        tip = Tip.objects.get(id=tip_id)
        parent_comment = Comment.objects.get(id=parent_id) if parent_id else None
        comment = Comment.objects.create(
            user=request.user,
            tip=tip,
            content=comment_text,
            parent_comment=parent_comment,
            image=request.FILES.get('image'),
            gif_url=gif_url
        )
        logger.info("Comment created successfully for tip_id: %s, comment_id=%s", tip_id, comment.id)

        avatar_url = (request.user.userprofile.avatar.url
                      if hasattr(request.user, 'userprofile') and request.user.userprofile.avatar
                      else settings.STATIC_URL + 'img/default-avatar.png')
        comment_data = {
            'id': comment.id,
            'user__username': request.user.username,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'avatar_url': avatar_url,
            'parent_id': parent_id,
            'parent_username': parent_comment.user.username if parent_comment else None,
            'like_count': 0,
            'share_count': 0,
            'reply_count': 0,
            'image': comment.image.url if comment.image else None,
            'gif_url': comment.gif_url if comment.gif_url else None
        }
        return JsonResponse({
            'success': True,
            'message': 'Comment added',
            'comment_count': tip.comments.count(),
            'comment_id': comment.id,
            'data': comment_data
        })
    except Tip.DoesNotExist:
        logger.error("Tip not found: tip_id=%s", tip_id)
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)
    except Comment.DoesNotExist:
        logger.error("Parent comment not found: parent_id=%s", parent_id)
        return JsonResponse({'success': False, 'error': 'Parent comment not found'}, status=404)
    except Exception as e:
        logger.error("Error creating comment: %s", str(e))
        return JsonResponse({'success': False, 'error': 'An error occurred while commenting.'}, status=500)

# View to fetch comments for a tip
@login_required
def get_tip_comments(request, tip_id):
    logger.info("Fetching comments for tip_id: %s", tip_id)
    try:
        tip = Tip.objects.get(id=tip_id)
        comments = tip.comments.all().order_by('-created_at')
        comments_data = []
        for comment in comments:
            try:
                profile = comment.user.userprofile
                avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            except UserProfile.DoesNotExist:
                avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
            comments_data.append({
                'id': comment.id,
                'user__username': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'like_count': comment.likes.count(),
                'share_count': comment.shares.count(),
                'reply_count': comment.replies.count(),
                'avatar_url': avatar_url,
                'parent_id': comment.parent_comment.id if comment.parent_comment else None,
                'parent_username': comment.parent_comment.user.username if comment.parent_comment else None,
                'image': comment.image.url if comment.image else None,
                'gif_url': comment.gif_url if comment.gif_url else None
            })
        logger.info("Found %s comments (including replies)", len(comments_data))
        return JsonResponse({'success': True, 'comments': comments_data})
    except Tip.DoesNotExist:
        logger.error("Tip not found: tip_id=%s", tip_id)
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)

# View to handle liking a comment
@login_required
@require_POST
def like_comment(request):
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    like, created = Like.objects.get_or_create(user=user, comment=comment)
    if created:
        return JsonResponse({'success': True, 'message': 'Comment liked', 'like_count': comment.likes.count()})
    else:
        like.delete()
        return JsonResponse({'success': True, 'message': 'Like removed', 'like_count': comment.likes.count()})

# View to handle sharing a comment
@login_required
@require_POST
def share_comment(request):
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    share, created = Share.objects.get_or_create(user=user, comment=comment)
    if created:
        return JsonResponse({'success': True, 'message': 'Comment shared', 'share_count': comment.shares.count()})
    else:
        share.delete()
        return JsonResponse({'success': True, 'message': 'Share removed', 'share_count': comment.shares.count()})

# View for the bookmarks page
@login_required
def bookmarks(request):
    """Display all bookmarked tips for the current user.
    
    Args:
        request: HTTP request
        
    Returns:
        Rendered template with bookmarked tips
    """
    bookmarked_tips = Tip.objects.filter(bookmarks=request.user).select_related('user__userprofile')
    return render(request, 'core/bookmarks.html', {'tips': bookmarked_tips})

@login_required
def toggle_bookmark(request):
    """Toggle bookmark status for a tip.
    
    Args:
        request: HTTP request containing tip_id
        
    Returns:
        JsonResponse with bookmark status and count
    """
    if request.method == 'POST':
        tip_id = request.POST.get('tip_id')
        try:
            tip = Tip.objects.get(id=tip_id)
            if request.user in tip.bookmarks.all():
                tip.bookmarks.remove(request.user)
                bookmarked = False
            else:
                tip.bookmarks.add(request.user)
                bookmarked = True
            tip.save()
            return JsonResponse({
                'success': True,
                'bookmarked': bookmarked,
                'bookmark_count': tip.bookmarks.count()
            })
        except Tip.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Tip not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# View for the messages page
@login_required
def messages_view(request, thread_id=None):
    """Display message threads and individual thread messages.
    
    Args:
        request: HTTP request
        thread_id: Optional ID of a specific thread to display
        
    Returns:
        Rendered template with message threads and optional specific thread
    """
    user = request.user
    message_threads = (MessageThread.objects.filter(participants=user)
                      .order_by('-updated_at')[:20]
                      .prefetch_related('participants__userprofile'))

    threads_with_participants = []
    for thread in message_threads:
        other_participant = thread.participants.exclude(id=user.id).first()
        last_message = thread.messages.last()
        follower_count = other_participant.followers.count() if other_participant else 0
        followed_by = Follow.objects.filter(followed=other_participant).exclude(follower=user).order_by('?')[:3]
        followed_by_names = [f.follower.username for f in followed_by]
        threads_with_participants.append({
            'thread': thread,
            'other_participant': other_participant,
            'last_message': last_message,
            'follower_count': follower_count,
            'followed_by': followed_by_names,
        })

    selected_thread = None
    messages = []
    if thread_id:
        selected_thread = get_object_or_404(MessageThread, id=thread_id, participants=user)
        selected_thread.other_participant = selected_thread.participants.exclude(id=user.id).first()
        messages = selected_thread.messages.all().order_by('created_at')

    context = {
        'message_threads': threads_with_participants,
        'selected_thread': selected_thread,
        'messages': messages,
    }
    return render(request, 'core/messages.html', context)

@csrf_exempt
def send_message(request):
    """Handle sending a new message or creating a new message thread.
    
    Args:
        request: HTTP request containing thread_id (optional) and recipient_username (if new thread)
        
    Returns:
        JsonResponse with message details or error status
    """
    thread_id = request.POST.get('thread_id')
    recipient_username = request.POST.get('recipient_username')
    content = request.POST.get('content')
    image = request.FILES.get('image')
    gif_url = request.POST.get('gif_url')

    if not content and not image and not gif_url:
        return JsonResponse({'success': False, 'error': 'Message content, image, or GIF URL must be provided'}, status=400)

    if thread_id:
        thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    else:
        if not recipient_username:
            return JsonResponse({'success': False, 'error': 'Recipient username required'}, status=400)
        recipient = get_object_or_404(User, username=recipient_username)
        if recipient == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot message yourself'}, status=400)

        thread = MessageThread.objects.filter(participants=request.user).filter(participants=recipient).first()
        if not thread:
            thread = MessageThread.objects.create()
            thread.participants.add(request.user, recipient)

    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        content=content or '',
        image=image,
        gif_url=gif_url
    )

    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
        'sender': message.sender.username,
        'thread_id': thread.id,
        'image': message.image.url if message.image else None,
        'gif_url': message.gif_url if message.gif_url else None,
    })

# View to fetch messages for a thread
@login_required
def get_thread_messages(request, thread_id):
    thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    messages = thread.messages.all().order_by('created_at')
    messages_data = [
        {
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'created_at': msg.created_at.isoformat(),
        }
        for msg in messages
    ]
    return JsonResponse({'success': True, 'messages': messages_data})

# View for the notifications page
@login_required
def notifications(request):
    """Display notifications for likes, follows, and shares.
    
    Args:
        request: HTTP request
        
    Returns:
        Rendered template with notifications
    """
    user = request.user
    like_notifications = (Like.objects.filter(tip__user=user)
                         .order_by('-created_at')[:20]
                         .select_related('user', 'tip', 'user__userprofile'))
    follow_notifications = (Follow.objects.filter(followed=user)
                           .order_by('-created_at')[:20]
                           .select_related('follower', 'follower__userprofile'))
    share_notifications = (Share.objects.filter(tip__user=user)
                          .order_by('-created_at')[:20]
                          .select_related('user', 'tip', 'user__userprofile'))

    return render(request, 'core/notifications.html', {
        'like_notifications': like_notifications,
        'follow_notifications': follow_notifications,
        'share_notifications': share_notifications,
    })

# Policy page views
def terms_of_service(request):
    return render(request, 'core/terms_of_service.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def cookie_policy(request):
    return render(request, 'core/cookie_policy.html')

def accessibility(request):
    return render(request, 'core/accessibility.html')


def suggested_users_api(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        logger.info("Fetching suggested users for user: %s", request.user.username)
        current_user = request.user
        followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
        logger.debug("Followed users: %s", list(followed_users))
        suggested_users = User.objects.filter(
            tip__isnull=False
        ).exclude(
            id__in=followed_users
        ).exclude(
            id=current_user.id
        ).distinct()[:10]
        logger.debug("Suggested users count: %s", suggested_users.count())

        users_data = []
        for user in suggested_users:
            profile = getattr(user, 'userprofile', None)
            avatar_url = profile.avatar.url if profile and profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            bio = profile.description or "No bio available" if profile else "No bio available"
            users_data.append({
                'username': user.username,
                'avatar_url': avatar_url,
                'bio': bio,
                'profile_url': f"/profile/{user.username}/"
            })

        logger.info("Returning %s suggested users", len(users_data))
        return JsonResponse({'success': True, 'users': users_data})
    except Exception as e:
        logger.error("Error in suggested_users_api: %s", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

class TipSerializer(ModelSerializer):
    class Meta:
        model = Tip
        fields = [
            'id', 'user', 'sport', 'text', 'image', 'gif_url', 'gif_width', 'gif_height',
            'poll', 'emojis', 'location', 'scheduled_at', 'audience', 'created_at',
            'odds', 'odds_format', 'bet_type', 'each_way', 'confidence', 'status',
            'resolution_note', 'verified_at'
        ]

# Updated view to post a new tip
@csrf_exempt
def post_tip(request):
    if request.method == 'POST':
        try:
            text = request.POST.get('tip_text')
            audience = request.POST.get('audience', 'everyone')
            sport = request.POST.get('sport', 'golf')
            image = request.FILES.get('image')
            gif_url = request.POST.get('gif')
            location = request.POST.get('location')
            poll = request.POST.get('poll', '{}')
            emojis = request.POST.get('emojis', '{}')

            # New fields
            odds_type = request.POST.get('odds_type')
            bet_type = request.POST.get('bet_type')
            each_way = request.POST.get('each_way', 'no')
            confidence = request.POST.get('confidence')

            # Handle odds based on format
            if odds_type == 'decimal':
                odds = request.POST.get('odds-input-decimal')
            elif odds_type == 'fractional':
                numerator = request.POST.get('odds-numerator')
                denominator = request.POST.get('odds-denominator')
                if not numerator or not denominator:
                    return JsonResponse({'success': False, 'error': 'Both numerator and denominator are required for fractional odds'}, status=400)
                odds = f"{numerator}/{denominator}"
            else:
                return JsonResponse({'success': False, 'error': 'Invalid odds type'}, status=400)

            if not text:
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty'}, status=400)
            if not odds:
                return JsonResponse({'success': False, 'error': 'Odds are required'}, status=400)
            if not odds_type:
                return JsonResponse({'success': False, 'error': 'Odds format is required'}, status=400)
            if not bet_type:
                return JsonResponse({'success': False, 'error': 'Bet type is required'}, status=400)

            allowed_tags = ['b', 'i']
            sanitized_text = bleach.clean(text, tags=allowed_tags, strip=True)

            tip = Tip.objects.create(
                user=request.user,
                text=sanitized_text,
                audience=audience,
                sport=sport,
                image=image,
                gif_url=gif_url,
                location=location,
                poll=poll,
                emojis=emojis,
                odds=odds,
                odds_format=odds_type,
                bet_type=bet_type,
                each_way=each_way,
                confidence=int(confidence) if confidence else None
            )

            response_data = {
                'success': True,
                'message': 'Tip posted successfully!',
                'tip': {
                    'id': tip.id,
                    'text': tip.text,
                    'image': tip.image.url if tip.image else None,
                    'gif': tip.gif_url if tip.gif_url else None,
                    'created_at': tip.created_at.isoformat(),
                    'username': tip.user.username,
                    'handle': tip.user.userprofile.handle or f"@{tip.user.username}",
                    'avatar': tip.user.userprofile.avatar.url if tip.user.userprofile.avatar else settings.STATIC_URL + 'img/default-avatar.png',
                    'sport': tip.sport,
                    'odds': tip.odds,
                    'odds_format': tip.odds_format,
                    'bet_type': tip.bet_type,
                    'each_way': tip.each_way,
                    'confidence': tip.confidence,
                    'status': tip.status,
                }
            }
            return JsonResponse(response_data)
        except Exception as e:
            logger.error("Error posting tip: %s", str(e))
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyTipView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        print("VerifyTipView hit!")
        print(f"Request user: {request.user}, Is staff: {request.user.is_staff}")
        print(f"Request data: {request.data}")

        tip_id = request.data.get('tip_id')
        new_status = request.data.get('status')
        resolution_note = request.data.get('resolution_note', '')

        VALID_STATUSES = ['pending', 'win', 'loss', 'dead_heat', 'void_non_runner']
        if new_status not in VALID_STATUSES:
            return Response({'success': False, 'error': f'Invalid status: {new_status}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tip = Tip.objects.get(id=tip_id)
            if tip.status != 'pending':
                return Response({'success': False, 'error': 'Tip is already verified'}, status=status.HTTP_400_BAD_REQUEST)

            tip.status = new_status
            tip.resolution_note = resolution_note
            tip.verified_at = timezone.now()
            tip.save()

            user = tip.user
            user_tips = Tip.objects.filter(user=user, status__in=['win', 'loss', 'dead_heat', 'void_non_runner'])
            total_tips = user_tips.count()
            wins = user_tips.filter(status='win').count()
            win_rate = (wins / total_tips * 100) if total_tips > 0 else 0

            user.userprofile.win_rate = win_rate
            user.userprofile.total_tips = total_tips
            user.userprofile.wins = wins
            user.userprofile.save()

            return Response({'success': True, 'win_rate': win_rate}, status=status.HTTP_200_OK)
        except Tip.DoesNotExist:
            return Response({'success': False, 'error': 'Tip not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Serializer for RaceMeeting model
class RaceMeetingSerializer(ModelSerializer):
    class Meta:
        model = RaceMeeting
        fields = ['date', 'venue', 'url']

# API view for listing race meetings
class RaceMeetingList(generics.ListAPIView):
    queryset = RaceMeeting.objects.all()
    serializer_class = RaceMeetingSerializer

# View for horse racing fixtures
def horse_racing_fixtures(request):
    today = datetime.now().date()
    meetings = RaceMeeting.objects.filter(date__gte=today).order_by('date')

    fixtures = [
        {
            'venue': meeting.venue,
            'date': meeting.date.isoformat(),
            'displayDate': meeting.date.strftime('%b %d, %Y'),
            'url': meeting.url
        }
        for meeting in meetings
    ]

    return JsonResponse({'fixtures': fixtures})

# API view for trending tips
@login_required
def trending_tips_api(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        logger.info("Fetching trending tips for user: %s", request.user.username)
        trending_tips = Tip.objects.annotate(
            total_likes=Count('likes'),
            total_shares=Count('shares')
        ).annotate(
            total_engagement=F('total_likes') + F('total_shares')
        ).order_by('-total_engagement')[:4]
        logger.debug("Trending tips count: %s", trending_tips.count())

        tips_data = []
        for tip in trending_tips:
            profile = getattr(tip.user, 'userprofile', None)
            avatar_url = profile.avatar.url if profile and profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            handle = profile.handle.lstrip('@') if profile and profile.handle else tip.user.username
            tips_data.append({
                'username': tip.user.username,
                'handle': handle,
                'avatar_url': avatar_url,
                'text': tip.text[:50],
                'likes': tip.total_likes,
                'profile_url': f"/profile/{tip.user.username}/",
            })

        logger.info("Returning %s trending tips", len(tips_data))
        return JsonResponse({'success': True, 'trending_tips': tips_data})
    except Exception as e:
        logger.error("Error in trending_tips_api: %s", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# API view for current user info
def current_user_api(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        user = request.user
        profile = getattr(user, 'userprofile', None)
        avatar_url = profile.avatar.url if profile and profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
        handle = profile.handle or user.username if profile else user.username
        return JsonResponse({
            'success': True,
            'avatar_url': avatar_url,
            'handle': handle,
            'username': user.username,
            'is_admin': user.is_staff or user.is_superuser
        })
    except (ValueError, TypeError) as e:
        logger.error("Error in current_user_api: %s", str(e))
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)
    

# New API view to fetch tip details
@login_required
def tip_detail(request, tip_id):
    try:
        tip = Tip.objects.get(id=tip_id)
        return JsonResponse({
            'success': True,
            'tip': {
                'id': tip.id,
                'status': tip.status,
                'odds': tip.odds,
                'bet_type': tip.bet_type,
                'each_way': tip.each_way,
                'confidence': tip.confidence
            }
        })
    except Tip.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)

@csrf_exempt
def csp_report(request):
    """Handle Content Security Policy violation reports.
    
    Args:
        request: HTTP request containing CSP violation data
        
    Returns:
        HTTP response with appropriate status code
    """
    if request.method == "POST":
        report = json.loads(request.body.decode("utf-8"))
        print("CSP Violation:", report)
        return HttpResponse(status=204)
    return HttpResponse(status=400)

# View to render message settings
@login_required
def message_settings_view(request):
    """Render message notification settings page.
    
    Args:
        request: HTTP request
        
    Returns:
        Rendered template with message settings
    """
    user = request.user
    if not hasattr(user, 'userprofile'):
        UserProfile.objects.get_or_create(user=user)

    return HttpResponse(
        render_to_string('core/message_settings.html', {
            'user': user,
            'request': request,
        })
    )

# View for search functionality
@login_required
def search(request):
    """Search for users and tips based on query.
    
    Args:
        request: HTTP request containing search query
        
    Returns:
        JsonResponse with matching users and tips
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'success': False, 'error': 'Query parameter is required'}, status=400)

    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(userprofile__handle__icontains=query)
    ).distinct()[:5]

    tips = Tip.objects.filter(
        Q(text__icontains=query)
    ).order_by('-created_at')[:5]

    user_results = []
    for user in users:
        try:
            profile = user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            handle = profile.handle or user.username
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
            handle = user.username
        user_results.append({
            'username': user.username,
            'handle': handle,
            'avatar_url': avatar_url,
            'profile_url': f"/profile/{user.username}/",
        })

    tip_results = []
    for tip in tips:
        try:
            profile = tip.user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            handle = profile.handle or tip.user.username
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
            handle = tip.user.username
        tip_results.append({
            'id': tip.id,
            'text': tip.text[:100],
            'username': tip.user.username,
            'handle': handle,
            'avatar_url': avatar_url,
            'profile_url': f"/profile/{tip.user.username}/",
            'created_at': tip.created_at.isoformat(),
            'odds': tip.odds,
            'odds_format': tip.odds_format,
            'bet_type': tip.bet_type,
            'each_way': tip.each_way,
            'confidence': tip.confidence,
            'status': tip.status,
        })

    return JsonResponse({
        'success': True,
        'users': user_results,
        'tips': tip_results,
    })

def racecards_json_view(request):
    """Return JSON data for horse racing racecards."""
    try:
        logger.debug("Entering racecards_json_view")
        data = get_racecards_json()
        logger.info("Returning racecards data: %s meetings", len(data))
        logger.debug("Sample data: %s", data[0] if data else 'Empty')
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error("Error in racecards_json_view: %s", str(e), exc_info=True)
        return JsonResponse([], safe=False)
    

# Configuration for golf tours (mirrors config in golf-events.js)
GOLF_TOURS = [
    {"tour_id": "pga", "name": "PGA Tour", "icon": "🏌️‍♂️", "priority": 1},
    {"tour_id": "lpga", "name": "LPGA Tour", "icon": "🏌️‍♀️", "priority": 2},
]

# Helper function to fetch and store golf events
def fetch_and_store_golf_events():
    """Fetch and store golf events from ESPN API.
    
    This function fetches golf events from the ESPN API for the current week
    and stores them in the database. It handles both completed and upcoming
    events."""
    
    today = datetime.now().date()
    start_date = today - timedelta(days=7)  # 7 days past for results
    end_date = today + timedelta(days=7)  # 7 days future for fixtures
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    for tour_config in GOLF_TOURS:
        tour_id = tour_config['tour_id']
        url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{tour_id}/scoreboard?dates={start_date_str}-{end_date_str}"
        try:
            response = requests.get(url)
            if not response.ok:
                logger.error("Failed to fetch %s: %s", tour_config['name'], response.status_code)
                continue
            data = response.json()

            # Log the raw API response for debugging
            logger.info("API response for %s: %s", tour_config['name'], data)

            # Ensure tour exists in database
            tour, _ = GolfTour.objects.get_or_create(
                tour_id=tour_id,
                defaults={
                    'name': tour_config['name'],
                    'icon': tour_config['icon'],
                    'priority': tour_config['priority']
                }
            )

            for event in data.get('events', []):
                event_id = event.get('id')
                name = event.get('name', '')
                status = event.get('status', {})
                state = status.get('type', {}).get('state', 'unknown')

                # Initialize default values
                venue_name = 'Location TBD'
                city = 'Unknown'
                state_location = 'Unknown'
                course_name = 'Unknown Course'
                par = 'N/A'
                yardage = 'N/A'
                purse = 'N/A'
                broadcast = 'N/A'
                weather = event.get('weather', {})

                # Extract data from the scoreboard endpoint
                competitions = event.get('competitions', [{}])[0]
                venue = competitions.get('venue', {})
                venue_name = venue.get('fullName', 'Location TBD')
                venue_address = venue.get('address', {})
                city = venue_address.get('city', 'Unknown')
                state_location = venue_address.get('state', 'Unknown')

                course_details = competitions.get('course', {})
                course_name = course_details.get('name', 'Unknown Course')
                par = str(course_details.get('par', 'N/A'))
                yardage = str(course_details.get('yardage', 'N/A'))

                broadcasts = event.get('broadcasts', [])
                broadcast = 'N/A'
                if broadcasts and broadcasts[0].get('names'):
                    broadcast = ', '.join(broadcasts[0]['names'])
                purse = str(event.get('purse', 'N/A'))

                # Fallback for Zurich Classic of New Orleans
                if event_id == "401703507":
                    venue_name = "TPC Louisiana"
                    city = "Avondale"
                    state_location = "LA"
                    course_name = "TPC Louisiana"
                    par = "72"
                    yardage = "7425"
                    purse = "8800000"
                    broadcast = "Golf Channel"
                    logger.info("Using hardcoded values for event %s", event_id)

                # Log extracted data for debugging
                logger.info("Final extracted data for Event %s (ID: %s): venue=%s, city=%s, state=%s, course=%s, par=%s, yardage=%s, purse=%s, broadcast=%s", 
                    name, event_id, venue_name, city, state_location, course_name, par, yardage, purse, broadcast)

                # Create or update course
                course, created = GolfCourse.objects.get_or_create(
                    name=course_name,
                    defaults={
                        'par': par,
                        'yardage': yardage
                    }
                )
                if not created:
                    course.par = par
                    course.yardage = yardage
                    course.save()
                    logger.info("Updated course %s: par=%s, yardage=%s", course_name, par, yardage)

                # Log the course object after saving
                logger.info("Saved course for event %s: %s", event_id, course.__dict__)

                # Create or update event
                event_obj, created = GolfEvent.objects.get_or_create(
                    event_id=event_id,
                    defaults={
                        'name': name,
                        'short_name': event.get('shortName', name),
                        'date': datetime.strptime(event.get('date'), '%Y-%m-%dT%H:%MZ').replace(tzinfo=pytz.UTC),
                        'state': state,
                        'completed': status.get('type', {}).get('completed', False),
                        'venue': venue_name,
                        'city': city,
                        'state_location': state_location,
                        'tour': tour,
                        'course': course,
                        'purse': purse,
                        'broadcast': broadcast,
                        'current_round': status.get('period', 1),
                        'total_rounds': event.get('format', {}).get('rounds', 4),
                        'is_playoff': status.get('type', {}).get('playoff', False),
                        'weather_condition': weather.get('condition', 'N/A'),
                        'weather_temperature': weather.get('temperature', 'N/A'),
                        'last_updated': timezone.now()
                    }
                )
                if not created:
                    event_obj.name = name
                    event_obj.short_name = event.get('shortName', name)
                    event_obj.date = datetime.strptime(event.get('date'), '%Y-%m-%dT%H:%MZ').replace(tzinfo=pytz.UTC)
                    event_obj.state = state
                    event_obj.completed = status.get('type', {}).get('completed', False)
                    event_obj.venue = venue_name
                    event_obj.city = city
                    event_obj.state_location = state_location
                    event_obj.tour = tour
                    event_obj.course = course
                    event_obj.purse = purse
                    event_obj.broadcast = broadcast
                    event_obj.current_round = status.get('period', 1)
                    event_obj.total_rounds = event.get('format', {}).get('rounds', 4)
                    event_obj.is_playoff = status.get('type', {}).get('playoff', False)
                    event_obj.weather_condition = weather.get('condition', 'N/A')
                    event_obj.weather_temperature = weather.get('temperature', 'N/A')
                    event_obj.last_updated = timezone.now()
                    event_obj.save()
                    logger.info("Updated event %s with new details: %s", event_id, event_obj.__dict__)

                # Fetch and store leaderboard for in-progress or completed events
                if event_obj.state in ['in', 'post']:
                    detailed_url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{tour_id}/scoreboard/{event['id']}"
                    try:
                        detailed_response = requests.get(detailed_url)
                        if detailed_response.ok:
                            summary_data = detailed_response.json()
                            leaderboard_data = summary_data.get('competitions', [{}])[0].get('competitors', [])

                            # Clear existing leaderboard entries for this event
                            event_obj.leaderboard.all().delete()

                            for competitor in leaderboard_data:
                                player_name = competitor.get('athlete', {}).get('displayName', 'Unknown')
                                player, _ = GolfPlayer.objects.get_or_create(
                                    name=player_name,
                                    defaults={
                                        'world_ranking': competitor.get('athlete', {}).get('worldRanking', 'N/A')
                                    }
                                )

                                # Get position and score
                                position = competitor.get('position', {}).get('displayValue', 'N/A')
                                score = competitor.get('score', {}).get('displayValue', 'N/A')
                                
                                # Get round scores
                                rounds_stat = []
                                for round_data in competitor.get('linescores', []):
                                    value = round_data.get('value', 'N/A')
                                    if value != 'N/A':
                                        try:
                                            value = float(value)
                                        except (ValueError, TypeError):
                                            value = 'N/A'
                                    rounds_stat.append(value)
                                
                                # Pad rounds to 4 if needed
                                rounds_stat += ["N/A"] * (4 - len(rounds_stat))
                                
                                # Calculate total strokes
                                strokes = 'N/A'
                                if rounds_stat and all(r != "N/A" for r in rounds_stat[:len([r for r in rounds_stat if r != "N/A"])]):
                                    try:
                                        strokes = sum(float(r) for r in rounds_stat if r != "N/A")
                                    except (ValueError, TypeError):
                                        strokes = 'N/A'

                                # Get player status
                                status = competitor.get('status', {}).get('type', 'active')

                                # Create leaderboard entry
                                LeaderboardEntry.objects.create(
                                    event=event_obj,
                                    player=player,
                                    position=position,
                                    score=score,
                                    rounds=rounds_stat,
                                    strokes=str(strokes),
                                    status=status
                                )

                    except requests.RequestException as e:
                        logger.error("Error fetching leaderboard for event %s: %s", event['id'], str(e))

        except requests.RequestException as e:
            logger.error("Error fetching %s: %s", tour_config['name'], str(e))

# API view to trigger fetching and storing golf events
@method_decorator(csrf_exempt, name='dispatch')
class FetchGolfEventsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            fetch_and_store_golf_events()
            return Response({'success': True, 'message': 'Golf events fetched and stored'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error fetching golf events: %s", str(e))
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GolfEventsList(APIView):
    def get(self, request):
        # Get state and tour_id from query parameters
        state = request.query_params.get('state', 'pre')
        tour_id = request.query_params.get('tour_id')

        # Base queryset for filtering
        queryset = GolfEvent.objects.all().select_related(
            'tour', 'course'
        ).prefetch_related(
            'leaderboard', 'leaderboard__player'
        )

        # Apply tour filter if specified
        if tour_id:
            queryset = queryset.filter(tour__tour_id=tour_id)

        # Filter based on state
        if state == 'pre':
            queryset = queryset.filter(state='pre', completed=False)
        elif state == 'in':
            queryset = queryset.filter(state='in', completed=False)
        elif state == 'post':
            queryset = queryset.filter(completed=True)

        # Order by date
        queryset = queryset.order_by('-date')

        # Serialize the data
        serializer = GolfEventSerializer(queryset, many=True)
        return Response(serializer.data)

# Configuration for football leagues (mirrors SPORT_CONFIG in upcoming-events.js)


FOOTBALL_LEAGUES = [
    {"league_id": "eng.1", "name": "Premier League", "icon": "⚽", "priority": 1},
    {"league_id": "esp.1", "name": "La Liga", "icon": "⚽", "priority": 2},
    {"league_id": "ita.1", "name": "Serie A", "icon": "⚽", "priority": 3},
]

# Helper function to fetch and store football events
def fetch_and_store_football_events():
    today = datetime.now().date()
    start_date = today - timedelta(days=7)
    end_date = today + timedelta(days=7)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    logger.info("Fetching events for date range: %s-%s", start_date_str, end_date_str)

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    for league_config in FOOTBALL_LEAGUES:
        league_id = league_config['league_id']
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard?dates={start_date_str}-{end_date_str}"
        try:
            response = session.get(url)
            if not response.ok:
                logger.error("Failed to fetch %s: %s - %s", league_config['name'], response.status_code, response.text)
                continue
            data = response.json()
            logger.info("ESPN API response for %s: %s", league_config['name'], data)
            logger.debug("Scoreboard data for %s: %s", league_config['name'], data.keys())

            league, _ = FootballLeague.objects.get_or_create(
                league_id=league_id,
                defaults={
                    'name': league_config['name'],
                    'icon': league_config['icon'],
                    'priority': league_config['priority']
                }
            )

            for event in data.get('events', []):
                competitions = event.get('competitions', [{}])[0]
                competitors = competitions.get('competitors', [])
                home = next((c for c in competitors if c.get('homeAway', '').lower() == 'home'), competitors[0] if competitors else {})
                away = next((c for c in competitors if c.get('homeAway', '').lower() == 'away'), competitors[1] if competitors else {})

                home_team, _ = FootballTeam.objects.get_or_create(
                    name=home.get('team', {}).get('displayName', 'TBD'),
                    defaults={
                        'logo': home.get('team', {}).get('logo', ''),
                        'form': home.get('form', 'N/A'),
                        'record': home.get('records', [{}])[0].get('summary', 'N/A')
                    }
                )
                away_team, _ = FootballTeam.objects.get_or_create(
                    name=away.get('team', {}).get('displayName', 'TBD'),
                    defaults={
                        'logo': away.get('team', {}).get('logo', ''),
                        'form': away.get('form', 'N/A'),
                        'record': home.get('records', [{}])[0].get('summary', 'N/A')
                    }
                )

                def get_team_stats(team):
                    stats = team.get('statistics', [])
                    return TeamStats.objects.create(
                        possession=next((s['displayValue'] for s in stats if s['name'] == 'possessionPct'), 'N/A'),
                        shots=next((s['displayValue'] for s in stats if s['name'] == 'totalShots'), 'N/A'),
                        shots_on_target=next((s['displayValue'] for s in stats if s['name'] == 'shotsOnTarget'), 'N/A'),
                        corners=next((s['displayValue'] for s in stats if s['name'] == 'wonCorners'), 'N/A'),
                        fouls=next((s['displayValue'] for s in stats if s['name'] == 'foulsCommitted'), 'N/A')
                    )

                home_stats = get_team_stats(home)
                away_stats = get_team_stats(away)

                geo_broadcasts = competitions.get('geoBroadcasts', [])
                broadcast = geo_broadcasts[0].get('media', {}).get('shortName', 'N/A') if geo_broadcasts else 'N/A'

                event_obj, created = FootballEvent.objects.update_or_create(
                    event_id=event.get('id'),
                    defaults={
                        'name': event.get('shortName', event.get('name', '')),
                        'date': event.get('date'),
                        'state': event.get('status', {}).get('type', {}).get('state', 'pre'),
                        'status_description': event.get('status', {}).get('type', {}).get('description', 'Unknown'),
                        'status_detail': event.get('status', {}).get('type', {}).get('detail', 'N/A'),
                        'league': league,
                        'venue': competitions.get('venue', {}).get('fullName', 'Location TBD'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home.get('score', '0'),
                        'away_score': away.get('score', '0'),
                        'home_stats': home_stats,
                        'away_stats': away_stats,
                        'clock': event.get('status', {}).get('type', {}).get('clock', '0:00'),
                        'period': event.get('status', {}).get('type', {}).get('period', 0),
                        'broadcast': broadcast
                    }
                )

                detailed_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/summary?event={event['id']}"
                try:
                    detailed_response = session.get(detailed_url)
                    if detailed_response.ok:
                        summary_data = detailed_response.json()
                        logger.info("Event %s summary data: %s", event['id'], summary_data)
                        logger.debug("Event %s summary data keys: %s", event['id'], list(summary_data.keys()))
                        logger.debug("Event %s state: %s", event['id'], event.get('status', {}).get('type', {}).get('state', 'unknown'))

                        plays = summary_data.get('plays', [])
                        logger.debug("Event %s total plays: %s", event['id'], len(plays))
                        if not plays and event.get('status', {}).get('type', {}).get('state') == 'post':
                            logger.warning("Event %s has empty plays array despite being post-game", event['id'])
                        key_events = []
                        if event.get('status', {}).get('type', {}).get('state') == 'post':
                            for play in plays:
                                logger.debug("Event %s play: %s", event['id'], play)
                                is_goal = False
                                is_yellow_card = False
                                is_red_card = False
                                play_type = play.get('type', {}).get('text', '').lower()
                                play_type_id = str(play.get('type', {}).get('id', '')) 

                                if (play.get('scoringPlay', False) or
                                    'goal' in play_type or
                                    play_type_id in ['28', '29', '30'] or
                                    play_type in ['penalty goal', 'own goal', 'free kick goal', 'header goal'] or
                                    'goal' in play.get('text', '').lower()):
                                    is_goal = True
                                    logger.info("Event %s detected goal: %s", event['id'], play)

                                if (play.get('yellowCard', False) or
                                    play_type == 'yellow card' or
                                    play_type_id == '70' or
                                    'yellow card' in play.get('text', '').lower()):
                                    is_yellow_card = True
                                    logger.info("Event %s detected yellow card: %s", event['id'], play)
                                if (play.get('redCard', False) or
                                    play_type == 'red card' or
                                    play_type_id == '71' or
                                    'red card' in play.get('text', '').lower()):
                                    is_red_card = True
                                    logger.info("Event %s detected red card: %s", event['id'], play)

                                if is_goal or is_yellow_card or is_red_card:
                                    key_events.append({
                                        'type': play.get('type', {}).get('text', 'Unknown'),
                                        'time': play.get('clock', {}).get('displayValue', 'N/A'),
                                        'team': play.get('team', {}).get('displayName', 'Unknown'),
                                        'player': (play.get('participants', [{}])[0].get('athlete', {}).get('displayName', 'Unknown')
                                                  or play.get('athlete', {}).get('displayName', 'Unknown')),
                                        'is_goal': is_goal,
                                        'is_yellow_card': is_yellow_card,
                                        'is_red_card': is_red_card
                                    })

                        logger.debug("Event %s key events: %s", event['id'], key_events)
                        if key_events:
                            logger.info("Event %s saving %s key events", event['id'], len(key_events))
                            event_obj.key_events.all().delete()
                            for ke in key_events:
                                KeyEvent.objects.create(event=event_obj, **ke)
                        else:
                            logger.warning("No key events found for event %s - plays array: %s plays, state: %s", 
                                event['id'], len(plays), event.get('status', {}).get('type', {}).get('state'))

                        goals = [
                            {
                                'scorer': play.get('participants', [{}])[0].get('athlete', {}).get('displayName', 'Unknown'),
                                'team': play.get('team', {}).get('displayName', 'Unknown'),
                                'time': play.get('clock', {}).get('displayValue', 'N/A'),
                                'assist': play.get('participants', [{}])[1].get('athlete', {}).get('displayName', 'Unassisted') if len(play.get('participants', [])) > 1 else 'Unassisted'
                            }
                            for play in plays if (play.get('scoringPlay', False) or
                                                 'goal' in play.get('type', {}).get('text', '').lower() or
                                                 str(play.get('type', {}).get('id', '')) in ['28', '29', '30'] or
                                                 play.get('type', {}).get('text', '').lower() in ['penalty goal', 'own goal', 'free kick goal', 'header goal'])
                        ]
                        DetailedStats.objects.update_or_create(
                            event=event_obj,
                            defaults={
                                'possession': summary_data.get('header', {}).get('competitions', [{}])[0].get('possession', {}).get('text', f"{home_stats.possession} - {away_stats.possession}"),
                                'home_shots': next((s.get('displayValue', home_stats.shots) for s in summary_data.get('boxscore', {}).get('teams', [{}])[0].get('statistics', []) if s.get('name') == 'shots'), home_stats.shots),
                                'away_shots': next((s.get('displayValue', away_stats.shots) for s in summary_data.get('boxscore', {}).get('teams', [{}])[1].get('statistics', []) if s.get('name') == 'shots'), away_stats.shots),
                                'goals': goals
                            }
                        )

                        odds_data = summary_data.get('header', {}).get('competitions', [{}])[0].get('odds', [{}])[0]
                        logger.debug("Event %s odds data: %s", event['id'], odds_data)
                        if odds_data:
                            BettingOdds.objects.update_or_create(
                                event=event_obj,
                                defaults={
                                    'home_odds': odds_data.get('homeTeamOdds', {}).get('moneyLine', 'N/A'),
                                    'away_odds': odds_data.get('awayTeamOdds', {}).get('moneyLine', 'N/A'),
                                    'draw_odds': odds_data.get('drawOdds', {}).get('moneyLine', 'N/A'),
                                    'provider': odds_data.get('provider', {}).get('name', 'Unknown Provider')
                                }
                            )
                            logger.info("Event %s saved betting odds: home=%s, away=%s, draw=%s", 
                                event['id'],
                                odds_data.get('homeTeamOdds', {}).get('moneyLine', 'N/A'),
                                odds_data.get('awayTeamOdds', {}).get('moneyLine', 'N/A'),
                                odds_data.get('drawOdds', {}).get('moneyLine', 'N/A'))
                        else:
                            logger.warning("No betting odds found for event %s - state: %s", 
                                event['id'],
                                event.get('status', {}).get('type', {}).get('state'))

                    else:
                        logger.error("Failed to fetch summary for event %s: %s - Response: %s", 
                            event['id'], detailed_response.status_code, detailed_response.text)
                except requests.RequestException as e:
                    logger.error("Error fetching detailed data for event %s: %s", event['id'], str(e))
                time.sleep(2)

        except requests.RequestException as e:
            logger.error("Error fetching %s: %s", league_config['name'], str(e))

# API view to trigger fetching and storing events
@method_decorator(csrf_exempt, name='dispatch')
class FetchFootballEventsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        try:
            fetch_and_store_football_events()
            return Response({'success': True, 'message': 'Football events fetched and stored'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error fetching football events: %s", str(e))
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API view to retrieve football events
class FootballEventsList(generics.ListAPIView):
    serializer_class = FootballEventSerializer

    def get_queryset(self):
        category = self.request.query_params.get('category', 'fixtures')
        today = timezone.now()
        seven_days_ago = today - timedelta(days=7)
        seven_days_future = today + timedelta(days=7)

        queryset = FootballEvent.objects.all().select_related(
            'league', 'home_team', 'away_team', 'home_stats', 'away_stats'
        ).prefetch_related('key_events', 'odds', 'detailed_stats')

        if category == 'fixtures':
            return queryset.filter(state='pre', date__gt=today, date__lte=seven_days_future)
        elif category == 'inplay':
            return queryset.filter(state='in')
        elif category == 'results':
            return queryset.filter(state='post', date__gte=seven_days_ago, date__lte=today)
        return queryset

def tennis_events(request):
    category = request.GET.get('category', 'fixtures')
    current_time = datetime.now()
    seven_days_ago = current_time - timedelta(days=7)
    seven_days_future = current_time + timedelta(days=7)

    queryset = TennisEvent.objects.select_related('tournament', 'venue', 'player1', 'player2', 'tournament__league')

    if category == 'fixtures':
        events = queryset.filter(state='pre', date__gt=current_time, date__lte=seven_days_future)
    elif category == 'inplay':
        events = queryset.filter(state='in')
    elif category == 'results':
        events = queryset.filter(state='post', date__gte=seven_days_ago, date__lte=current_time)
    else:
        return JsonResponse({'error': 'Invalid category'}, status=400)

    events_data = [
        {
            'event_id': event.event_id,
            'tournament': {
                'id': event.tournament.tournament_id,
                'name': event.tournament.name,
                'league': {
                    'name': event.tournament.league.name,
                    'icon': event.tournament.league.icon,
                    'priority': event.tournament.league.priority,
                },
            },
            'date': event.date.isoformat(),
            'state': event.state,
            'completed': event.completed,
            'player1_name': event.player1.name,
            'player2_name': event.player2.name,
            'score': event.score,
            'sets': event.sets,
            'stats': event.stats,
            'clock': event.clock,
            'period': event.period,
            'round_name': event.round_name,
            'venue': {'name': event.venue.name, 'court': event.venue.court} if event.venue else None,
            'match_type': event.match_type,
            'player1_rank': event.player1_rank,
            'player2_rank': event.player2_rank,
        }
        for event in events
    ]

    return JsonResponse(events_data, safe=False)

def tennis_event_stats(request, event_id):
    try:
        event = TennisEvent.objects.get(event_id=event_id)
        return JsonResponse({
            'sets': event.sets or [],
            'stats': event.stats or {},
        })
    except TennisEvent.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

@login_required
def get_comments(request, tip_id):
    """Retrieve comments for a specific tip."""
    tip = get_object_or_404(Tip, id=tip_id)
    comments = Comment.objects.filter(tip=tip, parent=None).order_by('-created_at')
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'gif_url': comment.gif_url,
            'replies': [{
                'id': reply.id,
                'text': reply.text,
                'user': reply.user.username,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'gif_url': reply.gif_url
            } for reply in comment.replies.all()]
        })
    return JsonResponse({'comments': comments_data})

@login_required
@require_POST
def delete_comment(request):
    """Handle deletion of comments."""
    comment_id = request.POST.get('comment_id')
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    comment.delete()
    return JsonResponse({'success': True, 'message': 'Comment deleted'})

@login_required
@require_POST
def edit_comment(request):
    """Handle editing of comments."""
    comment_id = request.POST.get('comment_id')
    new_text = request.POST.get('new_text')
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    comment.text = new_text
    comment.save()
    return JsonResponse({'success': True, 'message': 'Comment updated'})

@login_required
@require_POST
def delete_tip(request):
    """Handle deletion of tips."""
    tip_id = request.POST.get('tip_id')
    tip = get_object_or_404(Tip, id=tip_id)
    if tip.user != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    tip.delete()
    return JsonResponse({'success': True, 'message': 'Tip deleted'})

@login_required
@require_POST
def edit_tip(request):
    """Handle editing of tips."""
    tip_id = request.POST.get('tip_id')
    new_text = request.POST.get('new_text')
    tip = get_object_or_404(Tip, id=tip_id)
    if tip.user != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    tip.text = new_text
    tip.save()
    return JsonResponse({'success': True, 'message': 'Tip updated'})

@login_required
def get_tip_details(request, tip_id):
    """Retrieve detailed information about a specific tip."""
    tip = get_object_or_404(Tip, id=tip_id)
    tip_data = {
        'id': tip.id,
        'text': tip.text,
        'user': tip.user.username,
        'created_at': tip.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'likes': tip.likes.count(),
        'shares': tip.shares.count(),
        'comments': tip.comments.count(),
        'is_liked': tip.likes.filter(id=request.user.id).exists(),
        'is_shared': tip.shares.filter(id=request.user.id).exists()
    }
    return JsonResponse({'tip': tip_data})

@login_required
def get_user_tips(request, username):
    """Retrieve all tips posted by a specific user."""
    user = get_object_or_404(User, username=username)
    tips = Tip.objects.filter(user=user).order_by('-created_at')
    tips_data = []
    for tip in tips:
        tips_data.append({
            'id': tip.id,
            'text': tip.text,
            'created_at': tip.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'likes': tip.likes.count(),
            'shares': tip.shares.count(),
            'comments': tip.comments.count(),
            'is_liked': tip.likes.filter(id=request.user.id).exists(),
            'is_shared': tip.shares.filter(id=request.user.id).exists()
        })
    return JsonResponse({'tips': tips_data})

@login_required
def get_user_profile(request, username):
    """Retrieve profile information for a specific user."""
    user = get_object_or_404(User, username=username)
    profile = user.profile
    profile_data = {
        'username': user.username,
        'bio': profile.bio,
        'location': profile.location,
        'website': profile.website,
        'followers': profile.followers.count(),
        'following': profile.following.count(),
        'is_following': profile.followers.filter(id=request.user.id).exists()
    }
    return JsonResponse({'profile': profile_data})

@login_required
def get_followers(request, username):
    """Retrieve all followers of a specific user."""
    user = get_object_or_404(User, username=username)
    followers = user.profile.followers.all()
    followers_data = [{'username': follower.username} for follower in followers]
    return JsonResponse({'followers': followers_data})

@login_required
def get_following(request, username):
    """Retrieve all users that a specific user is following."""
    user = get_object_or_404(User, username=username)
    following = user.profile.following.all()
    following_data = [{'username': following_user.username} for following_user in following]
    return JsonResponse({'following': following_data})

@login_required
def get_user_feed(request):
    """Retrieve a feed of tips from users that the current user is following."""
    following = request.user.profile.following.all()
    tips = Tip.objects.filter(user__in=following).order_by('-created_at')
    tips_data = []
    for tip in tips:
        tips_data.append({
            'id': tip.id,
            'text': tip.text,
            'user': tip.user.username,
            'created_at': tip.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'likes': tip.likes.count(),
            'shares': tip.shares.count(),
            'comments': tip.comments.count(),
            'is_liked': tip.likes.filter(id=request.user.id).exists(),
            'is_shared': tip.shares.filter(id=request.user.id).exists()
        })
    return JsonResponse({'tips': tips_data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_notifications(request):
    """Retrieve unread notifications for the authenticated user."""
    try:
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')
        
        data = [{
            'id': notification.id,
            'message': notification.message,
            'created_at': notification.created_at,
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'related_tip_id': notification.related_tip.id if notification.related_tip else None,
            'related_user_id': notification.related_user.id if notification.related_user else None
        } for notification in notifications]
        
        return Response(data)
    except (Notification.DoesNotExist, AttributeError) as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return Response([], status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_user_notifications: {str(e)}")
        return Response(
            {'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )