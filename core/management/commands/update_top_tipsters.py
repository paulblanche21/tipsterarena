"""
Management command to update Top Tipster status and calculate revenue sharing.

This command should be run monthly to:
1. Calculate comprehensive scores for all tipsters
2. Update Top Tipster status for the top 20 performers
3. Calculate revenue sharing percentages
4. Reset monthly earnings for the new month

Usage:
    python manage.py update_top_tipsters
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from core.models import User, UserProfile

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update Top Tipster status and calculate revenue sharing for the month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to the database',
        )
        parser.add_argument(
            '--monthly-revenue',
            type=float,
            default=1000.0,
            help='Total monthly revenue to distribute (default: 1000.0)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        monthly_revenue = Decimal(str(options['monthly_revenue']))
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Top Tipster update (dry_run={dry_run})')
        )
        
        try:
            # Get all tipsters with minimum activity
            tipsters = User.objects.filter(
                userprofile__is_tipster=True
            ).annotate(
                total_tips=Count('tip'),
                wins=Count('tip', filter=Q(tip__status='win')),
                losses=Count('tip', filter=Q(tip__status='loss')),
                dead_heats=Count('tip', filter=Q(tip__status='dead_heat')),
                void_tips=Count('tip', filter=Q(tip__status='void_non_runner')),
                total_verified=Count('tip', filter=Q(tip__status__in=['win', 'loss', 'dead_heat', 'void_non_runner'])),
                total_followers=Count('followers'),
                total_likes=Count('tip__likes'),
                total_comments=Count('tip__comments'),
                total_shares=Count('tip__shares'),
                avg_confidence=Avg('tip__confidence'),
                recent_tips=Count('tip', filter=Q(tip__created_at__gte=timezone.now() - timedelta(days=30)))
            ).filter(
                total_tips__gte=5  # Minimum 5 tips to be considered
            )
            
            # Calculate scores for each tipster
            tipsters_data = []
            for tipster in tipsters:
                profile = tipster.userprofile
                
                # Calculate win rate
                total_verified = tipster.total_verified or 0
                wins = tipster.wins or 0
                win_rate = (wins / total_verified * 100) if total_verified > 0 else 0
                
                # Calculate engagement score
                total_likes = tipster.total_likes or 0
                total_comments = tipster.total_comments or 0
                total_shares = tipster.total_shares or 0
                engagement_score = (total_likes * 1) + (total_comments * 2) + (total_shares * 3)
                
                # Calculate consistency score (recent activity)
                recent_tips = tipster.recent_tips or 0
                consistency_score = min(recent_tips * 10, 100)
                
                # Calculate confidence score
                avg_confidence = tipster.avg_confidence or 0
                confidence_score = (avg_confidence / 5) * 50
                
                # Calculate comprehensive score
                base_score = win_rate * 2
                volume_score = min(tipster.total_tips * 2, 100)
                engagement_bonus = min(engagement_score / 10, 50)
                
                total_score = base_score + volume_score + engagement_bonus + consistency_score + confidence_score
                
                tipsters_data.append({
                    'user': tipster,
                    'profile': profile,
                    'total_score': total_score,
                    'win_rate': win_rate,
                    'total_tips': tipster.total_tips,
                    'recent_tips': recent_tips,
                    'followers': tipster.total_followers,
                })
            
            # Sort by total score (highest first)
            tipsters_data.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Update Top Tipster status and calculate revenue sharing
            revenue_share_pool = monthly_revenue * Decimal('0.2')  # 20% of revenue
            top_20_count = min(20, len(tipsters_data))
            
            if not dry_run:
                # Reset all Top Tipster status
                UserProfile.objects.filter(is_top_tipster=True).update(
                    is_top_tipster=False,
                    top_tipster_since=None,
                    monthly_earnings=Decimal('0'),
                    revenue_share_percentage=Decimal('0')
                )
            
            # Process top 20 tipsters
            for i, tipster_data in enumerate(tipsters_data[:20]):
                user = tipster_data['user']
                profile = tipster_data['profile']
                rank = i + 1
                
                # Calculate revenue share percentage
                # Top 3 get higher percentages, rest split evenly
                if rank == 1:
                    revenue_share = Decimal('0.25')  # 25% of pool
                elif rank == 2:
                    revenue_share = Decimal('0.20')  # 20% of pool
                elif rank == 3:
                    revenue_share = Decimal('0.15')  # 15% of pool
                else:
                    # Remaining 17 split 40% of pool
                    revenue_share = Decimal('0.40') / Decimal('17')
                
                monthly_earnings = revenue_share_pool * revenue_share
                revenue_share_percentage = revenue_share * Decimal('100')
                
                self.stdout.write(
                    f"Rank {rank}: {user.username} - Score: {tipster_data['total_score']:.0f}, "
                    f"Win Rate: {tipster_data['win_rate']:.1f}%, "
                    f"Revenue: €{monthly_earnings:.2f} ({revenue_share_percentage:.1f}%)"
                )
                
                if not dry_run:
                    # Update profile
                    profile.is_top_tipster = True
                    profile.top_tipster_since = timezone.now()
                    profile.monthly_earnings = monthly_earnings
                    profile.revenue_share_percentage = revenue_share_percentage
                    profile.total_earnings += monthly_earnings
                    profile.save()
            
            # Log summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nTop Tipster Update Complete:\n'
                    f'- Total tipsters processed: {len(tipsters_data)}\n'
                    f'- Top 20 tipsters updated: {top_20_count}\n'
                    f'- Revenue pool: €{revenue_share_pool:.2f}\n'
                    f'- Total monthly revenue: €{monthly_revenue:.2f}'
                )
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN - No changes made to database')
                )
            
        except Exception as e:
            logger.error(f"Error updating Top Tipsters: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error updating Top Tipsters: {str(e)}')
            )
            raise 