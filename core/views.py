from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, F, Q
from .models import Tip, Like, Follow, Share, UserProfile, Comment, MessageThread, RaceMeeting, Message, TennisEvent
from .models import FootballLeague, FootballTeam, TeamStats, FootballEvent, KeyEvent, BettingOdds, DetailedStats, GolfCourse, GolfEvent,GolfPlayer, GolfTour, LeaderboardEntry
from .serializers import  GolfEventSerializer, FootballEventSerializer
from .forms import UserProfileForm, CustomUserCreationForm, KYCForm, ProfileSetupForm  
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.serializers import ModelSerializer
from datetime import datetime, timedelta
from .horse_racing_events import get_racecards_json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import json
import requests
import logging
import bleach
import pytz 
import time
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator



logger = logging.getLogger(__name__)

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/landing.html')

def signup_view(request):
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
    """Handle manual KYC form submission."""
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
    if request.user.userprofile.profile_completed:
        return redirect('payment')
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            request.user.userprofile.profile_completed = True
            request.user.userprofile.save()
            return redirect('payment')
    else:
        form = ProfileSetupForm(instance=request.user.userprofile)
    return render(request, 'core/profile_setup.html', {'form': form})

@login_required
def skip_profile_setup(request):
    if not request.user.userprofile.profile_completed:
        request.user.userprofile.profile_completed = True
        request.user.userprofile.save()
    return redirect('payment')
    
# View for user login
def login_view(request):
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
    follower = request.user
    followed_username = request.POST.get('username')
    if not followed_username:
        return JsonResponse({'success': False, 'error': 'No username provided'}, status=400)

    followed = get_object_or_404(User, username=followed_username)
    if follower == followed:
        return JsonResponse({'success': False, 'error': 'Cannot follow yourself'}, status=400)

    follow, created = Follow.objects.get_or_create(follower=follower, followed=followed)
    if created:
        return JsonResponse({'success': True, 'message': f'Now following {followed_username}'})
    return JsonResponse({'success': True, 'message': f'Already following {followed_username}'})

@login_required
def profile(request, username):
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
        'average_odds': average_odds,  # New stat
    })

# View to handle profile editing
@login_required
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    user_profile = user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid form data'})
    else:
        form = UserProfileForm(instance=user_profile)
        return render(request, 'core/profile.html', {'form': form, 'user_profile': user_profile})

# View to handle liking a tip
@login_required
@require_POST
def like_tip(request):
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
    tip_id = request.POST.get('tip_id')
    comment_text = request.POST.get('comment_text', '')
    parent_id = request.POST.get('parent_id')
    gif_url = request.POST.get('gif', '')
    logger.info(f"Received comment_tip request: tip_id={tip_id}, comment_text={comment_text}, parent_id={parent_id}")

    if not tip_id:
        logger.error(f"Missing tip_id: tip_id={tip_id}")
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
        logger.info(f"Comment created successfully for tip_id: {tip_id}, comment_id: {comment.id}")

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
        logger.error(f"Tip not found: tip_id={tip_id}")
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)
    except Comment.DoesNotExist:
        logger.error(f"Parent comment not found: parent_id={parent_id}")
        return JsonResponse({'success': False, 'error': 'Parent comment not found'}, status=404)
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while commenting.'}, status=500)

# View to fetch comments for a tip
@login_required
def get_tip_comments(request, tip_id):
    logger.info(f"Fetching comments for tip_id: {tip_id}")
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
        logger.info(f"Found {len(comments_data)} comments (including replies)")
        return JsonResponse({'success': True, 'comments': comments_data})
    except Tip.DoesNotExist:
        logger.error(f"Tip not found: tip_id={tip_id}")
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
    bookmarked_tips = Tip.objects.filter(bookmarks=request.user).select_related('user__userprofile')
    return render(request, 'core/bookmarks.html', {'tips': bookmarked_tips})

# View to toggle bookmark status on a tip
@login_required
def toggle_bookmark(request):
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

# View to send a new message
@login_required
@require_POST
@csrf_exempt
def send_message(request):
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
        logger.info(f"Fetching suggested users for user: {request.user.username}")
        current_user = request.user
        followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
        logger.debug(f"Followed users: {list(followed_users)}")
        suggested_users = User.objects.filter(
            tip__isnull=False
        ).exclude(
            id__in=followed_users
        ).exclude(
            id=current_user.id
        ).distinct()[:10]
        logger.debug(f"Suggested users count: {suggested_users.count()}")

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

        logger.info(f"Returning {len(users_data)} suggested users")
        return JsonResponse({'success': True, 'users': users_data})
    except Exception as e:
        logger.error(f"Error in suggested_users_api: {str(e)}")
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
            logger.error(f"Error posting tip: {str(e)}")
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
        logger.info(f"Fetching trending tips for user: {request.user.username}")
        trending_tips = Tip.objects.annotate(
            total_likes=Count('likes'),
            total_shares=Count('shares')
        ).annotate(
            total_engagement=F('total_likes') + F('total_shares')
        ).order_by('-total_engagement')[:4]
        logger.debug(f"Trending tips count: {trending_tips.count()}")

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

        logger.info(f"Returning {len(tips_data)} trending tips")
        return JsonResponse({'success': True, 'trending_tips': tips_data})
    except Exception as e:
        logger.error(f"Error in trending_tips_api: {str(e)}")
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
    except Exception as e:
        logger.error(f"Error in current_user_api: {str(e)}")
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

# View to handle CSP violation reports
@csrf_exempt
def csp_report(request):
    if request.method == "POST":
        report = json.loads(request.body.decode("utf-8"))
        print("CSP Violation:", report)
        return HttpResponse(status=204)
    return HttpResponse(status=400)

# View to render message settings
@login_required
def message_settings_view(request):
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
        logger.info(f"Returning racecards data: {len(data)} meetings")
        logger.debug(f"Sample data: {data[0] if data else 'Empty'}")
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Error in racecards_json_view: {str(e)}", exc_info=True)
        return JsonResponse([], safe=False)
    

# Configuration for golf tours (mirrors config in golf-events.js)
GOLF_TOURS = [
    {"tour_id": "pga", "name": "PGA Tour", "icon": "🏌️‍♂️", "priority": 1},
    {"tour_id": "lpga", "name": "LPGA Tour", "icon": "🏌️‍♀️", "priority": 2},
]

# Helper function to fetch and store golf events
def fetch_and_store_golf_events():
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
                logger.error(f"Failed to fetch {tour_config['name']}: {response.status_code}")
                continue
            data = response.json()

            # Log the raw API response for debugging
            logger.info(f"API response for {tour_config['name']}: {data}")

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
                broadcast = broadcasts[0].get('media', 'N/A') if broadcasts else 'N/A'
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
                    logger.info(f"Using hardcoded values for event {event_id}")

                # Log extracted data for debugging
                logger.info(f"Final extracted data for Event {name} (ID: {event_id}): venue={venue_name}, city={city}, state={state_location}, course={course_name}, par={par}, yardage={yardage}, purse={purse}, broadcast={broadcast}")

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
                    logger.info(f"Updated course {course_name}: par={par}, yardage={yardage}")

                # Log the course object after saving
                logger.info(f"Saved course for event {event_id}: {course.__dict__}")

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
                    logger.info(f"Updated event {event_id} with new details: {event_obj.__dict__}")

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

                                rounds_stat = [round.get('value', 'N/A') for round in competitor.get('linescores', [])]
                                rounds_stat += ["N/A"] * (4 - len(rounds_stat))  # Pad rounds to 4
                                strokes = competitor.get('strokes', 'N/A')
                                if rounds_stat and all(r != "N/A" for r in rounds_stat[:len([r for r in rounds_stat if r != "N/A"])]):
                                    try:
                                        strokes = sum(float(r) for r in rounds_stat if r != "N/A")
                                    except (ValueError, TypeError):
                                        strokes = 'N/A'

                                LeaderboardEntry.objects.create(
                                    event=event_obj,
                                    player=player,
                                    position=competitor.get('position', 'N/A'),
                                    score=competitor.get('score', 'N/A'),
                                    rounds=rounds_stat,
                                    strokes=str(strokes),
                                    status=competitor.get('status', 'active')
                                )

                    except requests.RequestException as e:
                        logger.error(f"Error fetching leaderboard for event {event['id']}: {str(e)}")

        except requests.RequestException as e:
            logger.error(f"Error fetching {tour_config['name']}: {str(e)}")

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
            logger.error(f"Error fetching golf events: {str(e)}")
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GolfEventsList(generics.ListAPIView):
    serializer_class = GolfEventSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        category = self.request.query_params.get('category', 'fixtures')
        today = timezone.now()
        seven_days_ago = today - timedelta(days=7)
        seven_days_future = today + timedelta(days=7)

        queryset = GolfEvent.objects.all().select_related(
            'tour', 'course'
        ).prefetch_related('leaderboard__player')

        if category == 'fixtures':
            return queryset.filter(state='pre', date__gt=today, date__lte=seven_days_future)
        elif category == 'inplay':
            return queryset.filter(state='in')
        elif category == 'results':
            return queryset.filter(state='post', date__gte=seven_days_ago, date__lte=today)
        return queryset
    
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
    logger.info(f"Fetching events for date range: {start_date_str}-{end_date_str}")

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    for league_config in FOOTBALL_LEAGUES:
        league_id = league_config['league_id']
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard?dates={start_date_str}-{end_date_str}"
        try:
            response = session.get(url)
            if not response.ok:
                logger.error(f"Failed to fetch {league_config['name']}: {response.status_code} - {response.text}")
                continue
            data = response.json()
            logger.info(f"ESPN API response for {league_config['name']}: {data}")
            logger.debug(f"Scoreboard data for {league_config['name']}: {data.keys()}")

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
                        logger.info(f"Event {event['id']} summary data: {summary_data}")
                        logger.debug(f"Event {event['id']} summary data keys: {list(summary_data.keys())}")
                        logger.debug(f"Event {event['id']} state: {event.get('status', {}).get('type', {}).get('state', 'unknown')}")

                        plays = summary_data.get('plays', [])
                        logger.debug(f"Event {event['id']} total plays: {len(plays)}")
                        if not plays and event.get('status', {}).get('type', {}).get('state') == 'post':
                            logger.warning(f"Event {event['id']} has empty plays array despite being post-game")
                        key_events = []
                        if event.get('status', {}).get('type', {}).get('state') == 'post':
                            for play in plays:
                                logger.debug(f"Event {event['id']} play: {play}")
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
                                    logger.info(f"Event {event['id']} detected goal: {play}")

                                if (play.get('yellowCard', False) or
                                    play_type == 'yellow card' or
                                    play_type_id == '70' or
                                    'yellow card' in play.get('text', '').lower()):
                                    is_yellow_card = True
                                    logger.info(f"Event {event['id']} detected yellow card: {play}")
                                if (play.get('redCard', False) or
                                    play_type == 'red card' or
                                    play_type_id == '71' or
                                    'red card' in play.get('text', '').lower()):
                                    is_red_card = True
                                    logger.info(f"Event {event['id']} detected red card: {play}")

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

                        logger.debug(f"Event {event['id']} key events: {key_events}")
                        if key_events:
                            logger.info(f"Event {event['id']} saving {len(key_events)} key events")
                            event_obj.key_events.all().delete()
                            for ke in key_events:
                                KeyEvent.objects.create(event=event_obj, **ke)
                        else:
                            logger.warning(f"No key events found for event {event['id']} - plays array: {len(plays)} plays, state: {event.get('status', {}).get('type', {}).get('state')}")

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
                        logger.debug(f"Event {event['id']} odds data: {odds_data}")
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
                            logger.info(f"Event {event['id']} saved betting odds: home={odds_data.get('homeTeamOdds', {}).get('moneyLine', 'N/A')}, away={odds_data.get('awayTeamOdds', {}).get('moneyLine', 'N/A')}, draw={odds_data.get('drawOdds', {}).get('moneyLine', 'N/A')}")
                        else:
                            logger.warning(f"No betting odds found for event {event['id']} - state: {event.get('status', {}).get('type', {}).get('state')}")

                    else:
                        logger.error(f"Failed to fetch summary for event {event['id']}: {detailed_response.status_code} - Response: {detailed_response.text}")
                except requests.RequestException as e:
                    logger.error(f"Error fetching detailed data for event {event['id']}: {str(e)}")
                time.sleep(2)

        except requests.RequestException as e:
            logger.error(f"Error fetching {league_config['name']}: {str(e)}")

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
            logger.error(f"Error fetching football events: {str(e)}")
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