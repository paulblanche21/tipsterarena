"""General views for Tipster Arena."""

import json
import logging
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, F
from django.conf import settings
from django.contrib.auth.decorators import login_required

from ..models import User, UserProfile, Tip, Follow

logger = logging.getLogger(__name__)

def landing(request):
    """Render the landing page for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/landing.html')

def search(request):
    """Search for users and tips based on query."""
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

@login_required
def csp_report(request):
    """Handle Content Security Policy violation reports."""
    if request.method == "POST":
        try:
            report = json.loads(request.body.decode("utf-8"))
            # Sanitize and validate the report
            if not isinstance(report, dict):
                return HttpResponse(status=400)
            
            # Log only essential information
            logger.warning(
                "CSP Violation: blocked-uri=%s, violated-directive=%s",
                report.get('csp-report', {}).get('blocked-uri', 'unknown'),
                report.get('csp-report', {}).get('violated-directive', 'unknown')
            )
            return HttpResponse(status=204)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return HttpResponse(status=400)
    return HttpResponse(status=405)  # Method Not Allowed

# Policy page views
def terms_of_service(request):
    """Render terms of service page."""
    return render(request, 'core/terms_of_service.html')

def privacy_policy(request):
    """Render privacy policy page."""
    return render(request, 'core/privacy_policy.html')

def cookie_policy(request):
    """Render cookie policy page."""
    return render(request, 'core/cookie_policy.html')

def accessibility(request):
    """Render accessibility page."""
    return render(request, 'core/accessibility.html')

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
    ).distinct()[:10]

    suggested_tipsters = []
    for user in suggested_users:
        try:
            profile = user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else settings.STATIC_URL + 'img/default-avatar.png'
            bio = profile.description or "No bio available"
            handle = profile.handle or f"@{user.username}"
        except UserProfile.DoesNotExist:
            avatar_url = settings.STATIC_URL + 'img/default-avatar.png'
            bio = "No bio available"
            handle = f"@{user.username}"
            
        # Calculate user stats
        total_tips = Tip.objects.filter(user=user).count()
        followers_count = Follow.objects.filter(followed=user).count()
        
        # Calculate win rate
        tips = Tip.objects.filter(user=user, status__in=['win', 'loss'])
        total_verified_tips = tips.count()
        wins = tips.filter(status='win').count()
        win_rate = (wins / total_verified_tips * 100) if total_verified_tips > 0 else 0
        
        suggested_tipsters.append({
            'username': user.username,
            'handle': handle,
            'avatar_url': avatar_url,
            'bio': bio,
            'total_tips': total_tips,
            'win_rate': round(win_rate, 1),
            'followers_count': followers_count
        })

    context = {
        'tips': tips,
        'trending_tips': trending_tips,
        'suggested_tipsters': suggested_tipsters,
    }
    return render(request, 'core/home.html', context)

def chat_view(request):
    """Render the chat interface."""
    return render(request, 'core/chat.html') 