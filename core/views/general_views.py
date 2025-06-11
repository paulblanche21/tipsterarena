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
        if user.username is None or user.username == 'None' or handle is None or handle == 'None':
            logger.warning(f"[SEARCH API] Invalid username or handle: username='{user.username}', handle='{handle}'")
    logger.info(f"[SEARCH API] Returning users: {[u['username'] for u in user_results]}")

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

def chat_view(request):
    """Render the chat interface."""
    return render(request, 'core/chat.html') 