from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth import authenticate, login 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.models import User 
from django.http import JsonResponse 
from .models import Tip, Like, Follow, Share, UserProfile, MessageThread 
from .forms import UserProfileForm, CustomUserCreationForm 
from django.contrib.auth.forms import AuthenticationForm 
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect logged-in users to home
    return render(request, 'core/landing.html')  # No forms needed here

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
    
    # Check if the logged-in user is the profile owner
    is_owner = request.user == user
    
    # Only include the form if the user is the profile owner
    form = UserProfileForm(instance=user_profile) if is_owner else None
    
    # Check if the logged-in user is following this profile
    is_following = False
    if not is_owner:
        is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
    
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
    return render(request, 'terms_of_service.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def cookie_policy(request):
    return render(request, 'cookie_policy.html')

def accessibility(request):
    return render(request, 'accessibility.html')


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

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Tip
import json

@csrf_exempt
@login_required
def post_tip(request):
    if request.method == 'POST':
        try:
            text = request.POST.get('text')
            audience = request.POST.get('audience', 'everyone')  # Default to everyone

            if not text:
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty.'}, status=400)

            # Create the tip
            tip = Tip.objects.create(
                user=request.user,
                text=text,
                audience=audience,
                # Sport field can be added later if implemented
            )
            return JsonResponse({'success': True, 'message': 'Tip posted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)