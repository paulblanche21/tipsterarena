from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Tip, Like, Follow, Share, UserProfile, MessageThread
from .forms import UserProfileForm, CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm


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
    return render(request, 'core/home.html', {'tips': tips})

def sport_view(request, sport):
    tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]  # Latest 20 tips for the sport
    return render(request, f'core/sport_{sport}.html', {'tips': tips, 'sport': sport})

def explore(request):
    tips = Tip.objects.all().order_by('-created_at')[:20]  # Latest 20 tips from all users, X-like Explore
    return render(request, 'core/explore.html', {'tips': tips})

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
    
    # Add the form to the context
    form = UserProfileForm(instance=user_profile)
    
    return render(request, 'core/profile.html', {
        'user': user,
        'user_profile': user_profile,
        'user_tips': user_tips,
        'following_count': following_count,
        'followers_count': followers_count,
        'form': form,  # Pass the form
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

