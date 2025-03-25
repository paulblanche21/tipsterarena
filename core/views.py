from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth import authenticate, login 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User 
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.db.models import Count, F
from .models import Tip, Like, Follow, Share, UserProfile, Comment, MessageThread, RaceMeeting, RaceResult, Message, User 
from .forms import UserProfileForm, CustomUserCreationForm 
from django.contrib.auth.forms import AuthenticationForm 
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.serializers import ModelSerializer
from datetime import datetime
import json



import logging
import bleach

logger = logging.getLogger(__name__)

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect logged-in users to home
    return render(request, 'core/landing.html')  # No forms needed here

# views.py (relevant snippet)
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after signup
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

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


@login_required
def home(request):
    # Fetch tips for the main feed
    tips = Tip.objects.all().order_by('-created_at')[:20]  # Latest 20 tips

    # Ensure UserProfile exists for all users in tips
    for tip in tips:
        if not hasattr(tip.user, 'userprofile'):
            UserProfile.objects.get_or_create(user=tip.user)

    # Fetch trending tips based on likes and shares
    trending_tips = Tip.objects.annotate(
        total_likes=Count('likes'),
        total_shares=Count('shares')
    ).annotate(
        total_engagement=F('total_likes') + F('total_shares')
    ).order_by('-total_engagement')[:4]  # Get top 4 trending tips

    # Ensure UserProfile exists for all users in trending tips
    for tip in trending_tips:
        if not hasattr(tip.user, 'userprofile'):
            UserProfile.objects.get_or_create(user=tip.user)

    # Fetch suggested tipsters dynamically
    current_user = request.user
    followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
    suggested_users = User.objects.filter(
        tip__isnull=False
    ).exclude(
        id__in=followed_users
    ).exclude(
        id=current_user.id
    ).distinct()[:2]  # Limit to 2 for the sidebar

    suggested_tipsters = []
    for user in suggested_users:
        try:
            profile = user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'images/default-avatar.png'
            bio = profile.description or "No bio available"
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'images/default-avatar.png'
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

def sport_view(request, sport):
    # Validate the sport parameter
    valid_sports = ['football', 'golf', 'tennis', 'horse_racing']
    if sport not in valid_sports:
        return render(request, 'core/404.html', status=404)

    # Fetch tips for the specific sport
    tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]
    print(f"Sport: {sport}, Tip count: {tips.count()}")
    for tip in tips:
        print(f" - {tip.sport}: {tip.text}")

    # Pass the sport to the template to pre-select and disable the dropdown
    return render(request, 'core/sport.html', {
        'tips': tips,
        'sport': sport,  # Pass the sport to pre-select and disable the dropdown
    })


def explore(request):
    tips = Tip.objects.all().order_by('-created_at')[:20]  # Latest 20 tips from all users, X-like Explore

    # Ensure UserProfile exists for all users in tips
    for tip in tips:
        if not hasattr(tip.user, 'userprofile'):
            UserProfile.objects.get_or_create(user=tip.user)

    context = {
        'tips': tips,
        # No 'sport' variable passed, so dropdown is editable
    }
    return render(request, 'core/explore.html', context)


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
    
    # Create or check follow relationship
    follow, created = Follow.objects.get_or_create(
        follower=follower,
        followed=followed,
    )
    if created:
        return JsonResponse({'success': True, 'message': f'Now following {followed_username}'})
    else:
        return JsonResponse({'success': True, 'message': f'Already following {followed_username}'})


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    try:
        user_profile = user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.get_or_create(user=user)[0]
    
    user_tips = Tip.objects.filter(user=user).order_by('-created_at').select_related('user__userprofile')
    following_count = Follow.objects.filter(follower=user).count()
    followers_count = Follow.objects.filter(followed=user).count()
    
    is_owner = request.user == user
    form = UserProfileForm(instance=user_profile) if is_owner else None
    is_following = False if is_owner else Follow.objects.filter(follower=request.user, followed=user).exists()
    
    return render(request, 'core/profile.html', {
        'user': user,
        'user_profile': user_profile,
        'user_tips': user_tips,
        'following_count': following_count,
        'followers_count': followers_count,
        'form': form,
        'is_owner': is_owner,
        'is_following': is_following,
    })


@login_required  # Require users to log in to edit their profile
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    user_profile = user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid form data'})
    else:
        form = UserProfileForm(instance=user_profile)
        return render(request, 'core/profile.html', {'form': form, 'user_profile': user_profile})
    

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


@login_required
@require_POST
def comment_tip(request):
    tip_id = request.POST.get('tip_id')
    comment_text = request.POST.get('comment_text', '')  # Allow empty text
    parent_id = request.POST.get('parent_id')
    gif_url = request.POST.get('gif', '')  # Store GIF URL
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
            gif_url=request.POST.get('gif', '')  # Store GIF URL
        )
        logger.info(f"Comment created successfully for tip_id: {tip_id}, comment_id: {comment.id}")
        
        avatar_url = (request.user.userprofile.avatar.url 
                     if hasattr(request.user, 'userprofile') and request.user.userprofile.avatar 
                     else settings.STATIC_URL + 'images/default-avatar.png')
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
                avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'images/default-avatar.png'
            except UserProfile.DoesNotExist:
                avatar_url = settings.STATIC_URL + 'images/default-avatar.png'
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
                'gif_url': comment.gif_url if comment.gif_url else None  # Ensure gif_url is included
            })
        logger.info(f"Found {len(comments_data)} comments (including replies)")
        return JsonResponse({'success': True, 'comments': comments_data})
    except Tip.DoesNotExist:
        logger.error(f"Tip not found: tip_id={tip_id}")
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)

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


@login_required  # Require users to log in to see bookmarks
def bookmarks(request):
    # Placeholder view for Bookmarks (can be expanded later to show bookmarked tips)
    return render(request, 'core/bookmarks.html')

@login_required
def messages(request):
    user = request.user
    message_threads = (MessageThread.objects.filter(participants=user)
                      .order_by('-updated_at')[:20]
                      .prefetch_related('participants__userprofile'))  # Use prefetch_related for ManyToMany
    return render(request, 'core/messages.html', {
        'message_threads': message_threads,
    })

@login_required
def message_thread(request, thread_id):
    """View a specific message thread and its messages."""
    thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    messages = thread.messages.all().order_by('created_at')
    other_participant = thread.get_other_participant(request.user)

    return render(request, 'core/message_thread.html', {
        'thread': thread,
        'messages': messages,
        'other_participant': other_participant,
    })

@login_required
@require_POST
@csrf_exempt
def send_message(request):
    """Send a new message in a thread or create a new thread."""
    thread_id = request.POST.get('thread_id')
    recipient_username = request.POST.get('recipient_username')
    content = request.POST.get('content')

    if not content:
        return JsonResponse({'success': False, 'error': 'Message content cannot be empty'}, status=400)

    # If thread_id is provided, send a message in that thread
    if thread_id:
        thread = get_object_or_404(MessageThread, id=thread_id, participants=request.user)
    else:
        # Otherwise, create a new thread with the recipient
        if not recipient_username:
            return JsonResponse({'success': False, 'error': 'Recipient username required'}, status=400)
        recipient = get_object_or_404(User, username=recipient_username)
        if recipient == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot message yourself'}, status=400)

        # Check if a thread already exists between these users
        thread = MessageThread.objects.filter(participants=request.user).filter(participants=recipient).first()
        if not thread:
            thread = MessageThread.objects.create()
            thread.participants.add(request.user, recipient)

    # Create the message
    message = Message.objects.create(
        thread=thread,
        sender=request.user,
        content=content
    )

    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
        'sender': message.sender.username,
        'thread_id': thread.id,
    })

@login_required
def get_thread_messages(request, thread_id):
    """Fetch messages for a specific thread via API."""
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

@login_required  # Require users to log in to see notifications
def notifications(request):
    user = request.user
    # Get notifications with optimized queries for UserProfile
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

def terms_of_service(request):
    return render(request, 'core/terms_of_service.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def cookie_policy(request):
    return render(request, 'core/cookie_policy.html')

def accessibility(request):
    return render(request, 'core/accessibility.html')

@login_required
def suggested_users_api(request):
    current_user = request.user
    followed_users = Follow.objects.filter(follower=current_user).values_list('followed_id', flat=True)
    suggested_users = User.objects.filter(
        tip__isnull=False
    ).exclude(
        id__in=followed_users
    ).exclude(
        id=current_user.id
    ).distinct()[:10]

    users_data = []
    for user in suggested_users:
        try:
            profile = user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'images/default-avatar.png'
            bio = profile.description or "No bio available"
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'images/default-avatar.png'
            bio = "No bio available"
        users_data.append({
            'username': user.username,
            'avatar_url': avatar_url,
            'bio': bio,
            'profile_url': f"/profile/{user.username}/"
        })

    return JsonResponse({'users': users_data})


@csrf_exempt
@login_required
def post_tip(request):
    if request.method == 'POST':
        try:
            text = request.POST.get('text')
            audience = request.POST.get('audience', 'everyone')
            sport = request.POST.get('sport', 'golf')
            image = request.FILES.get('image')
            gif_url = request.POST.get('gif')  # Expecting a URL
            location = request.POST.get('location')
            poll = request.POST.get('poll', '{}')
            emojis = request.POST.get('emojis', '{}')

            if not text:
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty.'}, status=400)

            allowed_tags = ['b', 'i']
            sanitized_text = bleach.clean(text, tags=allowed_tags, strip=True)

            tip = Tip.objects.create(
                user=request.user,
                text=sanitized_text,
                audience=audience,
                sport=sport,
                image=image,
                gif_url=gif_url,  # Save the URL
                location=location,
                poll=poll,
                emojis=emojis
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
                    'avatar': tip.user.userprofile.avatar.url if tip.user.userprofile.avatar else settings.STATIC_URL + 'images/default-avatar.png',
                }
            }
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


# Serializer for RaceMeeting
class RaceMeetingSerializer(ModelSerializer):
    class Meta:
        model = RaceMeeting
        fields = ['date', 'venue', 'url']

# List view for RaceMeeting
class RaceMeetingList(generics.ListAPIView):
    queryset = RaceMeeting.objects.all()
    serializer_class = RaceMeetingSerializer

def horse_racing_fixtures(request):
    # Get all meetings within the next 7 days
    today = datetime.now().date()
    meetings = RaceMeeting.objects.filter(date__gte=today).order_by('date')
    
    # Format data for JSON
    fixtures = [
        {
            'venue': meeting.venue,
            'date': meeting.date.isoformat(),
            'displayDate': meeting.date.strftime('%b %d, %Y'),  # e.g., "Mar 19, 2025"
            'url': meeting.url
        }
        for meeting in meetings
    ]
    
    return JsonResponse({'fixtures': fixtures})

@login_required
def trending_tips_api(request):
    trending_tips = Tip.objects.annotate(
        total_likes=Count('likes'),
        total_shares=Count('shares')
    ).annotate(
        total_engagement=F('total_likes') + F('total_shares')
    ).order_by('-total_engagement')[:4]

    tips_data = []
    for tip in trending_tips:
        try:
            profile = tip.user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'images/default-avatar.png'
            # Strip the @ from the handle if it exists
            handle = profile.handle.lstrip('@') if profile.handle else tip.user.username
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'images/default-avatar.png'
            handle = tip.user.username
        tips_data.append({
            'username': tip.user.username,
            'handle': handle,
            'avatar_url': avatar_url,
            'text': tip.text[:50],
            'likes': tip.total_likes,
            'profile_url': f"/profile/{tip.user.username}/",
        })

    return JsonResponse({'trending_tips': tips_data})

@login_required
def current_user_api(request):
    user = request.user
    try:
        profile = user.userprofile
        avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'images/default-avatar.png'
        handle = profile.handle or user.username
    except UserProfile.DoesNotExist:
        avatar_url = settings.STATIC_URL + 'images/default-avatar.png'
        handle = user.username

    return JsonResponse({
        'success': True,
        'avatar_url': avatar_url,
        'handle': handle,
        'username': user.username
    })

@csrf_exempt
def csp_report(request):
    if request.method == "POST":
        report = json.loads(request.body.decode("utf-8"))
        print("CSP Violation:", report)  # Log the violation for debugging
        return HttpResponse(status=204)
    return HttpResponse(status=400)