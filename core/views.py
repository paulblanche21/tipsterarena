from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, F, Q
from .models import Tip, Like, Follow, Share, UserProfile, Comment, MessageThread, RaceMeeting, Message, FootballFixture
from core.serializers import FootballFixtureSerializer
from .forms import UserProfileForm, CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.serializers import ModelSerializer
from datetime import datetime, timedelta
from .horse_racing_events import get_racecards_json  # Re-enabled
import json
import requests
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
import logging
import bleach

logger = logging.getLogger(__name__)

# View for the landing page
def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/landing.html')

# View for user signup
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

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

# API view for suggested users


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

# Updated TipSerializer
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


class FootballFixturesView(APIView):
    def get(self, request):
        category = request.query_params.get('category', 'fixtures')
        current_time = timezone.now()
        fourteen_days_ago = current_time - timedelta(days=14)
        seven_days_future = current_time + timedelta(days=7)

        if category == 'fixtures':
            fixtures = FootballFixture.objects.filter(
                state='pre',
                match_date__gt=current_time,
                match_date__lte=seven_days_future
            )
        elif category == 'inplay':
            fixtures = FootballFixture.objects.filter(state='in')
        elif category == 'results':
            fixtures = FootballFixture.objects.filter(
                state='post',
                match_date__gte=fourteen_days_ago,
                match_date__lte=current_time
            )
        else:
            logger.error(f"Invalid category: {category}")
            return Response({'error': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Category: {category}, Fixtures found: {fixtures.count()}")
        for fixture in fixtures:
            logger.info(f"Fixture: {fixture.event_id}, {fixture.home_team} vs {fixture.away_team}, {fixture.match_date}, {fixture.state}")

        fixtures = fixtures.order_by('match_date')
        serializer = FootballFixtureSerializer(fixtures, many=True)
        return Response(serializer.data)
    
class FootballFixtureDetailView(APIView):
    def get(self, request, event_id):
        try:
            response = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/any/summary?event={event_id}", timeout=10)
            response.raise_for_status()
            return Response(response.json())
        except requests.RequestException as e:
            logger.error(f"Error fetching details for event {event_id}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)