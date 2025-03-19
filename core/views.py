from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth import authenticate, login 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User 
from django.http import JsonResponse
from django.db import models
from .models import Tip, Like, Follow, Share, UserProfile, Comment, MessageThread, RaceMeeting, RaceResult
from .forms import UserProfileForm, CustomUserCreationForm 
from django.contrib.auth.forms import AuthenticationForm 
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.serializers import ModelSerializer
from datetime import datetime


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

@login_required  # Require users to log in to see the home page
def home(request):
    tips = Tip.objects.all().order_by('-created_at')[:20]  # Latest 20 tips
    # Suggest tipsters: Users who have posted tips, excluding the current user
    context = {'tips': tips}  # No suggested_tipsters
    # Annotate with UserProfile data if available
    
    return render(request, 'core/home.html', context)

def sport_view(request, sport):
    tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]
    print(f"Sport: {sport}, Tip count: {tips.count()}")
    for tip in tips:
        print(f" - {tip.sport}: {tip.text}")
    return render(request, f'core/sport_{sport}.html', {'tips': tips, 'sport': sport})

def explore(request):
    tips = Tip.objects.all().order_by('-created_at')[:20]  # Latest 20 tips from all users, X-like Explore
    return render(request, 'core/explore.html', {'tips': tips})

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
    comment_text = request.POST.get('comment_text')
    parent_id = request.POST.get('parent_id')
    logger.info(f"Received comment_tip request: tip_id={tip_id}, comment_text={comment_text}, parent_id={parent_id}")
    if not tip_id or not comment_text:
        logger.error(f"Missing tip_id or comment_text: tip_id={tip_id}, comment_text={comment_text}")
        return JsonResponse({'success': False, 'error': 'Missing tip_id or comment_text'}, status=400)
    try:
        tip = get_object_or_404(Tip, id=tip_id)
        parent_comment = get_object_or_404(Comment, id=parent_id) if parent_id else None
        comment = Comment.objects.create(user=request.user, tip=tip, content=comment_text, parent_comment=parent_comment)
        logger.info(f"Comment created successfully for tip_id: {tip_id}")
        return JsonResponse({'success': True, 'message': 'Comment added', 'comment_count': tip.comments.count(), 'comment_id': comment.id})
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while commenting.'}, status=500)

@login_required
def get_tip_comments(request, tip_id):
    logger.info(f"Fetching comments for tip_id: {tip_id}")
    tip = get_object_or_404(Tip, id=tip_id)
    comments = tip.comments.filter(parent_comment__isnull=True).order_by('-created_at').values(
        'id', 'user__username', 'content', 'created_at'
    ).annotate(
        like_count=models.Count('likes'),
        share_count=models.Count('shares'),
        reply_count=models.Count('replies')
    )
    logger.info(f"Found {comments.count()} top-level comments")
    return JsonResponse({'comments': list(comments)})

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

@login_required
@require_POST
def reply_to_comment(request):
    comment_id = request.POST.get('comment_id')
    reply_text = request.POST.get('reply_text')
    logger.info(f"Received reply_to_comment request: comment_id={comment_id}, reply_text={reply_text}")
    if not comment_id or not reply_text:
        logger.error(f"Missing comment_id or reply_text: comment_id={comment_id}, reply_text={reply_text}")
        return JsonResponse({'success': False, 'error': 'Missing comment_id or reply_text'}, status=400)
    try:
        parent_comment = get_object_or_404(Comment, id=comment_id)
        tip = parent_comment.tip
        reply = Comment.objects.create(user=request.user, tip=tip, content=reply_text, parent_comment=parent_comment)
        logger.info(f"Reply created successfully for comment_id: {comment_id}")
        return JsonResponse({'success': True, 'message': 'Reply added', 'comment_count': tip.comments.count(), 'comment_id': reply.id})
    except Exception as e:
        logger.error(f"Error creating reply: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while replying.'}, status=500)

@login_required  # Require users to log in to see bookmarks
def bookmarks(request):
    # Placeholder view for Bookmarks (can be expanded later to show bookmarked tips)
    return render(request, 'core/bookmarks.html')

@login_required  # Require users to log in to see messages
def messages(request):
    user = request.user
    message_threads = (MessageThread.objects.filter(participants=user)
                      .order_by('-updated_at')[:20]
                      .prefetch_related('participants__userprofile'))  # Use prefetch_related for ManyToMany
    return render(request, 'core/messages.html', {
        'message_threads': message_threads,
    })

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
            # Get data from request
            text = request.POST.get('text')
            audience = request.POST.get('audience', 'everyone')
            sport = request.POST.get('sport', 'golf')  # Default to 'golf' or set based on your logic
            image = request.FILES.get('image')
            gif = request.FILES.get('gif')
            location = request.POST.get('location')
            poll = request.POST.get('poll', '{}')
            emojis = request.POST.get('emojis', '{}')

            # Validate required fields
            if not text:
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty.'}, status=400)

            # Sanitize text to allow only <b> and <i> tags
            allowed_tags = ['b', 'i']
            sanitized_text = bleach.clean(text, tags=allowed_tags, strip=True)

            # Create the tip
            tip = Tip.objects.create(
                user=request.user,
                text=sanitized_text,
                audience=audience,
                sport=sport,
                image=image,
                gif=gif,
                location=location,
                poll=poll,
                emojis=emojis
            )
            tip.save()  # Explicit save is optional since create() saves automatically

            return JsonResponse({'success': True, 'message': 'Tip posted successfully!'})
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