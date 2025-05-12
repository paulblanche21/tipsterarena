"""Views for handling user profiles in Tipster Arena."""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Sum

from ..models import UserProfile, Tip, Follow
from ..forms import UserProfileForm

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
    if user_own_tips.exists():
        total_odds = 0
        valid_tips = 0
        for tip in user_own_tips:
            try:
                if tip.odds is None or tip.odds_format is None:
                    continue
                if tip.odds_format.lower() == 'decimal':
                    odds_value = float(tip.odds)
                elif tip.odds_format.lower() == 'fractional':
                    numerator, denominator = map(float, tip.odds.split('/'))
                    odds_value = (numerator / denominator) + 1
                else:
                    continue
                total_odds += odds_value
                valid_tips += 1
            except (ValueError, ZeroDivisionError):
                continue
        if valid_tips > 0:
            average_odds = total_odds / valid_tips

    # Calculate premium tip stats
    premium_tips_count = user.tip_set.filter(is_premium_tip=True).count()
    premium_tips_views = user.tip_set.filter(is_premium_tip=True).aggregate(
        total_views=Sum('premium_tip_views')
    )['total_views'] or 0

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
        'premium_tips_count': premium_tips_count,
        'premium_tips_views': premium_tips_views,
    })

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