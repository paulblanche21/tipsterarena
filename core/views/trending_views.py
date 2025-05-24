from django.http import JsonResponse
from django.db.models import Count
from core.models import Tip
from django.core.serializers import serialize
import json

def trending_tips(request):
    limit = int(request.GET.get('limit', 30))
    
    # Get top tips based on likes count
    tips = Tip.objects.annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments'),
        shares_count=Count('shares')
    ).order_by('-likes_count')[:limit]
    
    # Prepare the response data
    tips_data = []
    for tip in tips:
        tips_data.append({
            'id': tip.id,
            'text': tip.text,
            'created_at': tip.created_at.isoformat(),
            'likes_count': tip.likes_count,
            'comments_count': tip.comments_count,
            'shares_count': tip.shares_count,
            'user': {
                'username': tip.user.username,
                'avatar_url': tip.user.userprofile.avatar.url if tip.user.userprofile.avatar else None,
            }
        })
    
    return JsonResponse(tips_data, safe=False) 