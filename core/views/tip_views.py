"""Views for handling tips in Tipster Arena."""

import logging
import bleach
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q

from ..models import Tip, Like, Share, Comment, UserProfile

logger = logging.getLogger(__name__)

@csrf_exempt
def post_tip(request):
    """Handle posting a new tip."""
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
            odds = None
            if odds_type == 'decimal':
                odds = request.POST.get('odds-input-decimal')
            elif odds_type == 'fractional':
                numerator = request.POST.get('odds-numerator')
                denominator = request.POST.get('odds-denominator')
                if numerator and denominator:
                    odds = f"{numerator}/{denominator}"

            if not text:
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty'}, status=400)

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
            logger.error("Error posting tip: %s", str(e))
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
@require_POST
def edit_tip(request):
    """Handle editing an existing tip."""
    try:
        tip_id = request.POST.get('tip_id')
        new_text = request.POST.get('text')

        if not tip_id or not new_text:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        tip = get_object_or_404(Tip, id=tip_id)

        # Check if user owns the tip
        if tip.user != request.user:
            return JsonResponse({'success': False, 'error': 'Not authorized to edit this tip'}, status=403)

        # Sanitize the text
        allowed_tags = ['b', 'i']
        sanitized_text = bleach.clean(new_text, tags=allowed_tags, strip=True)

        tip.text = sanitized_text
        tip.save()

        return JsonResponse({
            'success': True,
            'message': 'Tip updated successfully',
            'tip': {
                'id': tip.id,
                'text': tip.text
            }
        })
    except Tip.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)
    except Exception as e:
        logger.error("Error editing tip: %s", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_tip(request):
    """Handle deleting a tip."""
    try:
        tip_id = request.POST.get('tip_id')
        if not tip_id:
            return JsonResponse({'success': False, 'error': 'Missing tip_id'}, status=400)

        tip = get_object_or_404(Tip, id=tip_id)

        # Check if user owns the tip
        if tip.user != request.user:
            return JsonResponse({'success': False, 'error': 'Not authorized to delete this tip'}, status=403)

        tip.delete()
        return JsonResponse({
            'success': True,
            'message': 'Tip deleted successfully'
        })
    except Tip.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)
    except Exception as e:
        logger.error("Error deleting tip: %s", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def like_tip(request):
    """Handle liking and unliking tips."""
    try:
        tip_id = request.POST.get('tip_id')
        if not tip_id:
            return JsonResponse({'success': False, 'error': 'Missing tip_id'}, status=400)

        tip = get_object_or_404(Tip, id=tip_id)
        user = request.user

        # Check if like already exists
        existing_like = Like.objects.filter(user=user, tip=tip).first()
        if existing_like:
            existing_like.delete()
            return JsonResponse({
                'success': True,
                'message': 'Like removed',
                'like_count': tip.likes.count()
            })
        else:
            # Create new like
            Like.objects.create(user=user, tip=tip)
            return JsonResponse({
                'success': True,
                'message': 'Tip liked',
                'like_count': tip.likes.count()
            })
    except Exception as e:
        logger.error("Error in like_tip view: %s", str(e))
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_POST
def share_tip(request):
    """Handle sharing and unsharing tips."""
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
    """Handle adding comments to tips."""
    tip_id = request.POST.get('tip_id')
    comment_text = request.POST.get('comment_text', '')
    parent_id = request.POST.get('parent_id')
    gif_url = request.POST.get('gif', '')
    logger.info("Received comment_tip request: tip_id=%s, comment_text=%s, parent_id=%s", tip_id, comment_text, parent_id)

    if not tip_id:
        logger.error("Missing tip_id: tip_id=%s", tip_id)
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
        logger.info("Comment created successfully for tip_id: %s, comment_id=%s", tip_id, comment.id)

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
        logger.error("Tip not found: tip_id=%s", tip_id)
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)
    except Comment.DoesNotExist:
        logger.error("Parent comment not found: parent_id=%s", parent_id)
        return JsonResponse({'success': False, 'error': 'Parent comment not found'}, status=404)
    except Exception as e:
        logger.error("Error creating comment: %s", str(e))
        return JsonResponse({'success': False, 'error': 'An error occurred while commenting.'}, status=500)

@login_required
def get_tip_comments(request, tip_id):
    """Fetch comments for a tip."""
    logger.info("Fetching comments for tip_id: %s", tip_id)
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
        logger.info("Found %s comments (including replies)", len(comments_data))
        return JsonResponse({'success': True, 'comments': comments_data})
    except Tip.DoesNotExist:
        logger.error("Tip not found: tip_id=%s", tip_id)
        return JsonResponse({'success': False, 'error': 'Tip not found'}, status=404)

@login_required
def tip_detail(request, tip_id):
    """Display detailed view of a single tip."""
    tip = get_object_or_404(Tip, id=tip_id)
    comments = Comment.objects.filter(tip=tip, parent_comment=None).order_by('-created_at')
    
    # Get user's interaction status with the tip
    is_liked = tip.likes.filter(id=request.user.id).exists()
    is_shared = tip.shares.filter(id=request.user.id).exists()
    is_bookmarked = tip.bookmarks.filter(id=request.user.id).exists()
    
    context = {
        'tip': tip,
        'comments': comments,
        'is_liked': is_liked,
        'is_shared': is_shared,
        'is_bookmarked': is_bookmarked,
        'like_count': tip.likes.count(),
        'share_count': tip.shares.count(),
        'comment_count': tip.comments.count(),
    }
    
    return render(request, 'core/tip_detail.html', context)

@login_required
def tip_list(request):
    """Display a list of tips with filtering options."""
    try:
        # Get filter parameters
        sport = request.GET.get('sport')
        user_id = request.GET.get('user_id')
        search_query = request.GET.get('search')
        
        # Base queryset
        tips = Tip.objects.select_related('user', 'user__userprofile').prefetch_related(
            'likes', 'shares', 'comments'
        ).order_by('-created_at')
        
        # Apply filters
        if sport:
            tips = tips.filter(sport=sport)
        if user_id:
            tips = tips.filter(user_id=user_id)
        if search_query:
            tips = tips.filter(
                Q(text__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        # Get interaction counts
        tips = tips.annotate(
            like_count=Count('likes'),
            share_count=Count('shares'),
            comment_count=Count('comments')
        )
        
        context = {
            'tips': tips,
            'sport': sport,
            'user_id': user_id,
            'search_query': search_query
        }
        
        return render(request, 'core/tip_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in tip_list view: {str(e)}")
        return JsonResponse(
            {'error': 'Internal server error', 'detail': str(e)},
            status=500
        ) 