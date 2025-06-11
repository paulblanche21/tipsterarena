"""Views for handling tips in Tipster Arena."""

import logging
import bleach
import json
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from ..models import Tip, Like, Share, Comment, UserProfile
from ..badges import award_badges

logger = logging.getLogger(__name__)

@csrf_exempt
def post_tip(request):
    """Handle posting a new tip."""
    if request.method == 'POST':
        try:
            logger.info("Received POST request to post_tip")
            logger.info("POST data: %s", request.POST)
            logger.info("FILES data: %s", request.FILES)
            
            text = request.POST.get('tip_text')
            audience = request.POST.get('audience', 'everyone')
            sport = request.POST.get('sport', 'golf')
            image = request.FILES.get('image')
            gif_url = request.POST.get('gif')
            location = request.POST.get('location')
            
            logger.info("Basic fields: text=%s, audience=%s, sport=%s", text, audience, sport)
            
            # Handle JSON fields safely
            try:
                poll = json.loads(request.POST.get('poll', '{}'))
                if not isinstance(poll, dict):
                    logger.error("Invalid poll format: %s", request.POST.get('poll'))
                    return JsonResponse({'success': False, 'error': 'Invalid poll format'}, status=400)
            except json.JSONDecodeError as e:
                logger.error("JSON decode error for poll: %s", str(e))
                return JsonResponse({'success': False, 'error': 'Invalid poll JSON'}, status=400)
                
            try:
                emojis = json.loads(request.POST.get('emojis', '{}'))
                if not isinstance(emojis, dict):
                    logger.error("Invalid emojis format: %s", request.POST.get('emojis'))
                    return JsonResponse({'success': False, 'error': 'Invalid emojis format'}, status=400)
            except json.JSONDecodeError as e:
                logger.error("JSON decode error for emojis: %s", str(e))
                return JsonResponse({'success': False, 'error': 'Invalid emojis JSON'}, status=400)

            # Handle release_schedule as a JSON field
            try:
                release_schedule = json.loads(request.POST.get('release_schedule', '{}'))
                if not isinstance(release_schedule, dict):
                    logger.error("Invalid release_schedule format: %s", request.POST.get('release_schedule'))
                    return JsonResponse({'success': False, 'error': 'Invalid release_schedule format'}, status=400)
            except json.JSONDecodeError as e:
                logger.error("JSON decode error for release_schedule: %s", str(e))
                return JsonResponse({'success': False, 'error': 'Invalid release_schedule JSON'}, status=400)

            # New fields
            odds_type = request.POST.get('odds_type')
            bet_type = request.POST.get('bet_type')
            each_way = request.POST.get('each_way', 'no')
            confidence = request.POST.get('confidence')
            
            logger.info("Odds fields: odds_type=%s, bet_type=%s, each_way=%s, confidence=%s", 
                       odds_type, bet_type, each_way, confidence)
            
            if confidence:
                try:
                    confidence = int(confidence)
                except (ValueError, TypeError) as e:
                    logger.error("Invalid confidence value: %s", str(e))
                    return JsonResponse({'success': False, 'error': 'Invalid confidence value'}, status=400)

            # Handle odds based on format
            odds = None
            logger.info("Odds type: %s", odds_type)
            
            # Only process odds if we have both odds_type and actual odds values
            if odds_type and (
                (odds_type == 'decimal' and request.POST.get('odds-input-decimal', '').strip()) or
                (odds_type == 'fractional' and request.POST.get('odds-numerator', '').strip() and request.POST.get('odds-denominator', '').strip())
            ):
                if odds_type == 'decimal':
                    odds_value = request.POST.get('odds-input-decimal')
                    logger.info("Decimal odds value: %s", odds_value)
                    if odds_value and odds_value.strip():
                        try:
                            odds_float = float(odds_value)
                            if odds_float < 1.0:
                                logger.error("Decimal odds less than 1.0: %s", odds_value)
                                return JsonResponse({'success': False, 'error': 'Decimal odds must be greater than or equal to 1.0'}, status=400)
                            odds = odds_value
                        except ValueError as e:
                            logger.error("Invalid decimal odds value: %s", str(e))
                            return JsonResponse({'success': False, 'error': 'Invalid decimal odds value'}, status=400)
                elif odds_type == 'fractional':
                    numerator = request.POST.get('odds-numerator')
                    denominator = request.POST.get('odds-denominator')
                    logger.info("Fractional odds: numerator=%s, denominator=%s", numerator, denominator)
                    if numerator and denominator and numerator.strip() and denominator.strip():
                        try:
                            num = int(numerator)
                            den = int(denominator)
                            if den == 0:
                                logger.error("Zero denominator in fractional odds")
                                return JsonResponse({'success': False, 'error': 'Denominator cannot be zero'}, status=400)
                            odds = f"{num}/{den}"
                        except ValueError as e:
                            logger.error("Invalid fractional odds values: %s", str(e))
                            return JsonResponse({'success': False, 'error': 'Invalid fractional odds values'}, status=400)
                else:
                    logger.error("Invalid odds type: %s", odds_type)
                    return JsonResponse({'success': False, 'error': 'Invalid odds type'}, status=400)

            if not text:
                logger.error("Empty tip text")
                return JsonResponse({'success': False, 'error': 'Tip text cannot be empty'}, status=400)

            allowed_tags = ['b', 'i']
            sanitized_text = bleach.clean(text, tags=allowed_tags, strip=True)
            
            logger.info("Creating tip with odds=%s, odds_format=%s", odds, odds_type if odds else None)
            
            # Create tip with validated data
            tip = Tip(
                user=request.user,
                text=sanitized_text,
                sport=sport,
                audience=audience,
                poll=json.dumps(poll),
                emojis=json.dumps(emojis),
                odds=odds,
                odds_format=odds_type if odds else None,  # Only set odds_format if odds are provided
                bet_type=bet_type if odds else None,  # Only set bet_type if odds are provided
                each_way=each_way if odds else 'no',  # Default to 'no' if no odds
                confidence=confidence,
                release_schedule=release_schedule
            )
            
            if image:
                tip.image = image
            if gif_url:
                tip.gif_url = gif_url
            if location:
                tip.location = location
                
            # Validate the model
            try:
                tip.full_clean()
                tip.save()
                logger.info("Tip saved successfully with ID: %s", tip.id)
            except ValidationError as e:
                logger.error("Validation error in post_tip: %s", str(e))
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'tip': {
                    'id': tip.id,
                    'text': tip.text,
                    'username': tip.user.username,
                    'handle': tip.user.userprofile.handle,
                    'avatar': tip.user.userprofile.avatar.url if tip.user.userprofile.avatar else None,
                    'sport': tip.sport,
                    'odds': tip.odds,
                    'odds_format': tip.odds_format,
                    'bet_type': tip.bet_type,
                    'each_way': tip.each_way,
                    'confidence': tip.confidence,
                    'status': tip.status,
                    'image': tip.image.url if tip.image else None,
                    'gif': tip.gif_url,
                    'created_at': tip.created_at.isoformat(),
                    'release_schedule': tip.release_schedule
                }
            })
            
        except Exception as e:
            logger.error("Unexpected error in post_tip: %s", str(e), exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
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

class LikeTipView(LoginRequiredMixin, View):
    """Handle liking and unliking tips."""
    def post(self, request):
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
                    'likes_count': tip.likes.count()
                })
            else:
                # Create new like
                Like.objects.create(user=user, tip=tip)
                return JsonResponse({
                    'success': True,
                    'message': 'Tip liked',
                    'likes_count': tip.likes.count()
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

class TipDetailView(LoginRequiredMixin, View):
    """Display detailed view of a single tip."""
    
    def get(self, request, tip_id):
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

@login_required
def verify_tip(request, tip_id):
    """Verify a tip's outcome and award badges if applicable."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    tip = get_object_or_404(Tip, id=tip_id)
    status = request.POST.get('status')
    
    if status not in ['won', 'lost', 'void']:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    tip.status = status
    tip.save()

    # Check and award badges
    award_badges(tip.user.userprofile)

    return JsonResponse({
        'success': True,
        'message': f'Tip marked as {status}',
        'tip_id': tip.id,
        'status': status
    }) 