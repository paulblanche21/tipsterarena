"""Core views for the Tipster Arena application.

This module contains all the view functions and classes that handle HTTP requests
and responses for the Tipster Arena application, including user interactions,
sports events, and social features.
"""

from datetime import datetime, timedelta
import json
import logging

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
from rest_framework.decorators import api_view, permission_classes, authentication_classes


import requests
import bleach
import pytz
import stripe

from .models import (
    Tip, Like, Follow, Share, UserProfile, Comment, MessageThread, RaceMeeting, Message, TennisEvent,
    FootballLeague, FootballTeam, TeamStats, FootballEvent, KeyEvent, BettingOdds, DetailedStats,
    GolfCourse, GolfEvent, GolfPlayer, GolfTour, LeaderboardEntry, Notification,
    TennisLeague, TennisTournament, TennisPlayer, TennisVenue, TennisBettingOdds,
    HorseRacingMeeting, HorseRacingRace, HorseRacingResult
)

from .serializers import GolfEventSerializer, FootballEventSerializer, TennisEventSerializer, HorseRacingMeetingSerializer, HorseRacingRaceSerializer, HorseRacingResultSerializer
from .forms import UserProfileForm, CustomUserCreationForm, KYCForm
from .horse_racing_events import get_racecards_json
from .constants import FOOTBALL_LEAGUES, GOLF_TOURS, TENNIS_LEAGUES

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
                if tip.odds is None or tip.odds_format is None:
                    print(f"  Skipping tip ID {tip.id}: Odds or format is None")
                    continue
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
    """Fetch comments for a tip and return them as JSON."""
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
    """Handle liking a comment by creating or removing a like record."""
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
    """Handle sharing a comment by creating or removing a share record."""
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
    """Retrieve and return messages for a specific thread."""
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
            odds = None
            if odds_type == 'decimal':
                odds = request.POST.get('odds-input-decimal')
            elif odds_type == 'fractional':
                numerator = request.POST.get('odds-numerator')
                denominator = request.POST.get('odds-denominator')
                if numerator and denominator:
                    odds = f"{numerator}/{denominator}"

            if not text:
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty'}, status=400)

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
    
    This function fetches golf tournament events from the ESPN API for the current week
    and stores them in the database. It handles both completed and upcoming tournaments."""
    
    for tour_config in GOLF_TOURS:
        tour_id = tour_config['tour_id']
        url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{tour_id}/tournaments"
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

            for tournament in data.get('tournaments', []):
                event_id = tournament.get('id')
                name = tournament.get('name', '')
                status = tournament.get('status', {})
                state = status.get('type', {}).get('state', 'unknown')
                completed = status.get('type', {}).get('completed', False)

                # Get tournament details
                venue_name = tournament.get('venue', {}).get('name', 'Location TBD')
                city = tournament.get('venue', {}).get('address', {}).get('city', 'Unknown')
                state_location = tournament.get('venue', {}).get('address', {}).get('state', 'Unknown')
                
                course_details = tournament.get('course', {})
                course_name = course_details.get('name', 'Unknown Course')
                par = str(course_details.get('par', 'N/A'))
                yardage = str(course_details.get('yardage', 'N/A'))

                purse = str(tournament.get('purse', {}).get('amount', 'N/A'))
                broadcast = tournament.get('broadcast', {}).get('network', 'N/A')
                weather = tournament.get('weather', {})

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

                # Create or update event
                event_obj, created = GolfEvent.objects.get_or_create(
                    event_id=event_id,
                    defaults={
                        'name': name,
                        'short_name': tournament.get('shortName', name),
                        'date': datetime.strptime(tournament.get('startDate'), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC),
                        'state': state,
                        'completed': completed,
                        'venue': venue_name,
                        'city': city,
                        'state_location': state_location,
                        'tour': tour,
                        'course': course,
                        'purse': purse,
                        'broadcast': broadcast,
                        'current_round': status.get('round', 1),
                        'total_rounds': tournament.get('rounds', 4),
                        'is_playoff': status.get('playoff', False),
                        'weather_condition': weather.get('condition', 'N/A'),
                        'weather_temperature': weather.get('temperature', 'N/A'),
                        'last_updated': timezone.now()
                    }
                )
                if not created:
                    event_obj.name = name
                    event_obj.short_name = tournament.get('shortName', name)
                    event_obj.date = datetime.strptime(tournament.get('startDate'), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
                    event_obj.state = state
                    event_obj.completed = completed
                    event_obj.venue = venue_name
                    event_obj.city = city
                    event_obj.state_location = state_location
                    event_obj.tour = tour
                    event_obj.course = course
                    event_obj.purse = purse
                    event_obj.broadcast = broadcast
                    event_obj.current_round = status.get('round', 1)
                    event_obj.total_rounds = tournament.get('rounds', 4)
                    event_obj.is_playoff = status.get('playoff', False)
                    event_obj.weather_condition = weather.get('condition', 'N/A')
                    event_obj.weather_temperature = weather.get('temperature', 'N/A')
                    event_obj.last_updated = timezone.now()
                    event_obj.save()

                # Fetch and store leaderboard for in-progress or completed events
                if event_obj.state in ['in', 'post']:
                    leaderboard_url = f"https://site.api.espn.com/apis/site/v2/sports/golf/{tour_id}/tournaments/{event_id}/leaderboard"
                    try:
                        leaderboard_response = requests.get(leaderboard_url)
                        if leaderboard_response.ok:
                            leaderboard_data = leaderboard_response.json()
                            players = leaderboard_data.get('players', [])
                            
                            if not players:
                                logger.warning("No leaderboard data found for tournament %s", event_id)
                                continue

                            # Clear existing leaderboard entries for this event
                            event_obj.leaderboard.all().delete()

                            for player_data in players:
                                try:
                                    player_info = player_data.get('player', {})
                                    player_name = player_info.get('name', 'Unknown')
                                    if not player_name:
                                        continue

                                    player, _ = GolfPlayer.objects.get_or_create(
                                        name=player_name,
                                        defaults={
                                            'world_ranking': player_info.get('rank', 'N/A')
                                        }
                                    )

                                    # Get position and score
                                    position = str(player_data.get('position', 'N/A'))
                                    total_score = player_data.get('total', 'N/A')
                                    
                                    # Get round scores
                                    rounds = player_data.get('rounds', [])
                                    rounds_stat = []
                                    for round_info in rounds:
                                        score = round_info.get('score', 'N/A')
                                        if score != 'N/A':
                                            try:
                                                score = int(score)
                                            except (ValueError, TypeError):
                                                score = 'N/A'
                                        rounds_stat.append(score)
                                    
                                    # Pad rounds to 4 if needed
                                    rounds_stat += ['N/A'] * (4 - len(rounds_stat))
                                    
                                    # Calculate total strokes
                                    total_strokes = player_data.get('strokes', 'N/A')
                                    
                                    # Create leaderboard entry
                                    LeaderboardEntry.objects.create(
                                        event=event_obj,
                                        player=player,
                                        position=position,
                                        score=str(total_score),
                                        rounds=rounds_stat,
                                        strokes=str(total_strokes),
                                        status=player_data.get('status', 'active')
                                    )
                                except Exception as e:
                                    logger.error("Error processing player data for tournament %s: %s", event_id, str(e))
                                    continue
                    except requests.RequestException as e:
                        logger.error("Error fetching leaderboard for tournament %s: %s", event_id, str(e))
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
    authentication_classes = []  # Remove authentication requirement for GET requests
    permission_classes = []  # Remove permission requirement for GET requests

    def get(self, request):
        try:
            # Get state and tour_id from query parameters
            state = request.query_params.get('state', 'pre')
            tour_id = request.query_params.get('tour_id')

            # First, fetch and store the latest events
            try:
                fetch_and_store_golf_events()
            except Exception as e:
                logger.error(f"Error fetching golf events: {str(e)}")
                # Continue with existing data if fetch fails

            # Base queryset for filtering
            queryset = GolfEvent.objects.all().select_related(
                'tour', 'course'
            ).prefetch_related(
                'leaderboard', 'leaderboard__player'
            )

            # Apply tour filter if specified
            if tour_id:
                queryset = queryset.filter(tour__tour_id=tour_id)

            # Apply state filter
            if state == 'pre':
                queryset = queryset.filter(state='pre', date__gt=timezone.now())
            elif state == 'in':
                queryset = queryset.filter(state='in')
            elif state == 'post':
                queryset = queryset.filter(state='post', completed=True)

            # Order by date
            queryset = queryset.order_by('date')

            # Serialize the data
            serializer = GolfEventSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error in GolfEventsList view: {str(e)}")
            return Response(
                {'error': 'Internal server error', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def fetch_and_store_football_events():
    """Fetch football events from ESPN API and store them in the database."""
    logger.info("Starting to fetch football events")
    try:
        base_url = settings.ESPN_API_BASE_URL
        leagues = {
            'eng.1': {'name': 'Premier League', 'icon': '⚽', 'priority': 1},
            'esp.1': {'name': 'La Liga', 'icon': '⚽', 'priority': 2},
            'ger.1': {'name': 'Bundesliga', 'icon': '⚽', 'priority': 3},
            'ita.1': {'name': 'Serie A', 'icon': '⚽', 'priority': 4},
            'fra.1': {'name': 'Ligue 1', 'icon': '⚽', 'priority': 5},
        }
        
        for league_id, league_config in leagues.items():
            # Fetch events from API
            url = f"{base_url}/soccer/{league_id}/scoreboard"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            for event_data in data.get('events', []):
                event_id = event_data['id']
                name = event_data['name']
                date = datetime.fromisoformat(event_data['date'].replace('Z', '+00:00'))
                
                # Get teams
                competitions = event_data.get('competitions', [])
                if not competitions:
                    logger.warning(f"No competitions found in event {event_id}. Skipping.")
                    continue
                    
                competition = competitions[0]
                competitors = competition.get('competitors', [])
                logger.info(f"Competitors data: {json.dumps(competitors, indent=2)}")
                
                home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                
                logger.info(f"Home team data: {json.dumps(home_team_data, indent=2)}")
                logger.info(f"Away team data: {json.dumps(away_team_data, indent=2)}")
                
                # Create or update teams
                home_team_name = home_team_data.get('team', {}).get('displayName', '') or home_team_data.get('team', {}).get('name', '')
                away_team_name = away_team_data.get('team', {}).get('displayName', '') or away_team_data.get('team', {}).get('name', '')
                
                if not home_team_name or not away_team_name:
                    logger.warning(f"Missing team names in event {event_id}. Skipping.")
                    continue
                
                home_team, _ = FootballTeam.objects.get_or_create(
                    name=home_team_name,
                    defaults={
                        'logo': home_team_data.get('team', {}).get('logo', '') or home_team_data.get('team', {}).get('image', ''),
                        'form': home_team_data.get('form', ''),
                        'record': home_team_data.get('record', '')
                    }
                )
                
                away_team, _ = FootballTeam.objects.get_or_create(
                    name=away_team_name,
                    defaults={
                        'logo': away_team_data.get('team', {}).get('logo', '') or away_team_data.get('team', {}).get('image', ''),
                        'form': away_team_data.get('form', ''),
                        'record': away_team_data.get('record', '')
                    }
                )
                
                # Create or update team stats
                home_stats = TeamStats.objects.create(
                    possession=home_team_data.get('statistics', [{}])[0].get('possession', 'N/A') if home_team_data.get('statistics') else 'N/A',
                    shots=home_team_data.get('statistics', [{}])[0].get('shots', 'N/A') if home_team_data.get('statistics') else 'N/A',
                    shots_on_target=home_team_data.get('statistics', [{}])[0].get('shotsOnTarget', 'N/A') if home_team_data.get('statistics') else 'N/A',
                    corners=home_team_data.get('statistics', [{}])[0].get('corners', 'N/A') if home_team_data.get('statistics') else 'N/A',
                    fouls=home_team_data.get('statistics', [{}])[0].get('fouls', 'N/A') if home_team_data.get('statistics') else 'N/A'
                )
                
                away_stats = TeamStats.objects.create(
                    possession=away_team_data.get('statistics', [{}])[0].get('possession', 'N/A') if away_team_data.get('statistics') else 'N/A',
                    shots=away_team_data.get('statistics', [{}])[0].get('shots', 'N/A') if away_team_data.get('statistics') else 'N/A',
                    shots_on_target=away_team_data.get('statistics', [{}])[0].get('shotsOnTarget', 'N/A') if away_team_data.get('statistics') else 'N/A',
                    corners=away_team_data.get('statistics', [{}])[0].get('corners', 'N/A') if away_team_data.get('statistics') else 'N/A',
                    fouls=away_team_data.get('statistics', [{}])[0].get('fouls', 'N/A') if away_team_data.get('statistics') else 'N/A'
                )
                
                # Create or update event
                event_obj, created = FootballEvent.objects.get_or_create(
                    event_id=event_id,
                    defaults={
                        'name': name,
                        'date': date,
                        'state': event_data.get('status', {}).get('type', 'pre'),
                        'status_description': event_data.get('status', {}).get('type', {}).get('description', 'Unknown'),
                        'status_detail': event_data.get('status', {}).get('type', {}).get('detail', 'N/A'),
                        'league': league_config['name'],
                        'venue': event_data.get('competitions', [{}])[0].get('venue', {}).get('fullName', 'Location TBD'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home_team_data.get('score', '0'),
                        'away_score': away_team_data.get('score', '0'),
                        'home_stats': home_stats,
                        'away_stats': away_stats,
                        'clock': event_data.get('status', {}).get('clock', '0:00'),
                        'period': event_data.get('status', {}).get('period', 0),
                        'broadcast': event_data.get('competitions', [{}])[0].get('broadcasters', [{}])[0].get('name', 'N/A')
                    }
                )
                
                # Create key events
                for key_event in competition.get('keyEvents', []):
                    KeyEvent.objects.create(
                        event=event_obj,
                        type=key_event.get('type', 'Unknown'),
                        time=key_event.get('clock', 'N/A'),
                        team=key_event.get('team', 'Unknown'),
                        player=key_event.get('player', 'Unknown'),
                        is_goal=key_event.get('isGoal', False),
                        is_yellow_card=key_event.get('isYellowCard', False),
                        is_red_card=key_event.get('isRedCard', False)
                    )
                
                # Create betting odds
                odds_data = competition.get('odds', {})
                if odds_data:
                    BettingOdds.objects.create(
                        event=event_obj,
                        home_odds=odds_data.get('home', 'N/A'),
                        away_odds=odds_data.get('away', 'N/A'),
                        draw_odds=odds_data.get('draw', 'N/A'),
                        provider=odds_data.get('provider', 'Unknown Provider')
                    )
                
                # Create detailed stats
                stats_data = competition.get('statistics', {})
                if stats_data:
                    DetailedStats.objects.create(
                        event=event_obj,
                        possession=stats_data.get('possession', 'N/A'),
                        home_shots=stats_data.get('homeShots', 'N/A'),
                        away_shots=stats_data.get('awayShots', 'N/A'),
                        goals=stats_data.get('goals', [])
                    )
                
                logger.info(f"{'Created' if created else 'Updated'} football event: {name}")
        
        logger.info("Successfully fetched and stored football events")
    except Exception as e:
        logger.error(f"Error fetching football events: {str(e)}")
        raise

# API view to trigger fetching and storing football events
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

class FootballEventsList(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get category and league_id from query parameters
            category = request.query_params.get('category', 'fixtures')
            league_id = request.query_params.get('league_id')

            # Try to fetch fresh events if needed
            try:
                fetch_and_store_football_events()
            except Exception as e:
                logger.error(f"Error fetching football events: {str(e)}")
                # Continue with existing data if fetch fails

            # Base queryset for filtering
            queryset = FootballEvent.objects.all().select_related(
                'league', 'home_team', 'away_team', 'home_stats', 'away_stats'
            ).prefetch_related(
                'key_events', 'odds', 'detailed_stats'
            )

            # Apply league filter if specified
            if league_id:
                queryset = queryset.filter(league__league_id=league_id)

            # Apply category filter
            current_time = timezone.now()
            if category == 'fixtures':
                # Future matches that haven't started
                queryset = queryset.filter(state='pre', date__gt=current_time)
            elif category == 'inplay':
                # Currently ongoing matches
                queryset = queryset.filter(state='in')
            elif category == 'results':
                # Completed matches from the last 7 days
                seven_days_ago = current_time - timedelta(days=7)
                queryset = queryset.filter(
                    state='post',
                    date__lt=current_time,  # Only matches that have ended
                    date__gte=seven_days_ago
                )

            # Order by date (ascending for fixtures, descending for results)
            if category == 'fixtures':
                queryset = queryset.order_by('date')
            else:
                queryset = queryset.order_by('-date')

            # Serialize the data
            serializer = FootballEventSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in FootballEventsList: {str(e)}")
            return Response(
                {'error': 'An error occurred while fetching events'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['GET'])
# Remove authentication requirement for GET requests to allow public access to tennis events
def tennis_events(request):
    try:
        # Try to fetch and store the latest tennis events
        from core.management.commands.populate_tennis import Command
        logger.info("Attempting to fetch and store tennis events")
        Command().fetch_and_store_tennis_events()
        logger.info("Successfully fetched and stored tennis events")
    except Exception as e:
        logger.error(f"Error fetching tennis events: {str(e)}")
        logger.exception("Full traceback for tennis events error:")
        # Continue with existing data if fetch fails
    
    category = request.GET.get('category', 'fixtures')
    logger.info(f"Fetching tennis events for category: {category}")
    
    # Get current date
    current_date = timezone.now()
    
    # Base queryset
    events = TennisEvent.objects.all()
    logger.info(f"Total tennis events in database: {events.count()}")
    
    # Filter based on category
    if category == 'fixtures':
        events = events.filter(state='pre', date__gte=current_date)
    elif category == 'inplay':
        events = events.filter(state='in')
    elif category == 'results':
        seven_days_ago = current_date - timedelta(days=7)
        events = events.filter(state='post', date__gte=seven_days_ago)
    
    logger.info(f"Filtered tennis events for {category}: {events.count()}")
    
    # Order by date
    events = events.order_by('date')
    
    # Serialize and return data
    serializer = TennisEventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['GET'])
# Remove authentication requirement for GET requests to allow public access to tennis event stats
def tennis_event_stats(request, event_id):
    """
    Get detailed stats for a tennis event.
    """
    try:
        event = TennisEvent.objects.get(event_id=event_id)
        return Response(event.stats)
    except TennisEvent.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting tennis event stats: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def horse_racing_events(request):
    """
    API endpoint for horse racing events.
    Returns meetings, races, and results based on the category parameter.
    """
    category = request.GET.get('category', 'upcoming_meetings')
    today = timezone.now().date()
    
    try:
        if category == 'upcoming_meetings':
            # Get meetings for today and tomorrow
            end_date = today + timedelta(days=1)
            meetings = HorseRacingMeeting.objects.filter(
                date__range=[today, end_date]
            ).select_related('course').prefetch_related('races').order_by('date', 'course__name')
            serializer = HorseRacingMeetingSerializer(meetings, many=True)
            return Response(serializer.data)
            
        elif category == 'at_the_post':
            # Get races happening now (within the last 30 minutes and next 30 minutes)
            now = timezone.now()
            start_time = now - timedelta(minutes=30)
            end_time = now + timedelta(minutes=30)
            
            races = HorseRacingRace.objects.filter(
                meeting__date=today,
                off_time__range=[start_time.time(), end_time.time()]
            ).select_related('meeting', 'meeting__course').order_by('off_time')
            serializer = HorseRacingRaceSerializer(races, many=True)
            return Response(serializer.data)
            
        elif category == 'race_results':
            # Get results from the last 7 days
            start_date = today - timedelta(days=7)
            results = HorseRacingResult.objects.filter(
                race__meeting__date__range=[start_date, today]
            ).select_related(
                'race', 'race__meeting', 'race__meeting__course',
                'horse', 'trainer', 'jockey'
            ).order_by('-race__meeting__date', '-race__off_time')
            serializer = HorseRacingResultSerializer(results, many=True)
            return Response(serializer.data)
            
        else:
            return Response({'error': 'Invalid category'}, status=400)
            
    except Exception as e:
        return Response({'error': str(e)}, status=500)
