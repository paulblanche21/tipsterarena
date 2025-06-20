"""Core models for Tipster Arena.

Contains database models for user profiles, tips, and social interactions.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import stripe
from django.core.exceptions import ValidationError
import json

# Model representing a user's tip
class Tip(models.Model):
    """Represents a betting tip posted by a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Tip author
    sport = models.CharField(
        max_length=20,
        choices=[
            ('football', 'Football'),
            ('golf', 'Golf'),
            ('tennis', 'Tennis'),
            ('horse_racing', 'Horse Racing'),
            ('american_football', 'American Football'),
            ('baseball', 'Baseball'),
            ('basketball', 'Basketball'),
            ('boxing', 'Boxing'),
            ('cricket', 'Cricket'),
            ('cycling', 'Cycling'),
            ('darts', 'Darts'),
            ('gaelic_games', 'Gaelic Games'),
            ('greyhound_racing', 'Greyhound Racing'),
            ('motor_sport', 'Motor Sport'),
            ('rugby_union', 'Rugby Union'),
            ('snooker', 'Snooker'),
            ('volleyball', 'Volleyball'),
        ]
    )  # Sport category for the tip
    text = models.TextField()  # Main content of the tip
    image = models.ImageField(upload_to='tips/', blank=True, null=True)  # Optional image attachment
    gif_url = models.URLField(blank=True, null=True)  # URL for an attached GIF
    gif_width = models.PositiveIntegerField(null=True, blank=True)  # GIF width for display
    gif_height = models.PositiveIntegerField(null=True, blank=True)  # GIF height for display
    poll = models.TextField(blank=True, null=True, default='{}')  # JSON string for poll data
    emojis = models.TextField(blank=True, null=True, default='{}')  # JSON string for emoji data
    bookmarks = models.ManyToManyField(User, related_name='bookmarked_tips', blank=True)  # Users who bookmarked this tip
    location = models.CharField(max_length=255, blank=True, null=True)  # Optional location tag
    scheduled_at = models.DateTimeField(blank=True, null=True)  # Optional scheduled posting time
    audience = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Everyone'),
            ('followers', 'Followers'),
        ],
        default='everyone'
    )  # Visibility setting
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of tip creation
    # Updated fields for tip details
    odds = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="The odds for the tip (e.g., '2.5' or '2/1')"
    )  # Store odds as a string (e.g., "2.5" or "2/1")
    odds_format = models.CharField(
        max_length=20,
        choices=[
            ('decimal', 'Decimal'),
            ('fractional', 'Fractional'),
        ],
        null=True,
        blank=True
    )  # Format of the odds
    bet_type = models.CharField(
        max_length=50,
        choices=[
            ('single', 'Single'),
            ('double', 'Double'),
            ('treble', 'Treble'),
            ('fourfold', 'Fourfold'),
            ('fivefold', 'Fivefold'),
            ('sixfold', 'Sixfold'),
            ('sevenfold', 'Sevenfold'),
            ('eightfold', 'Eightfold'),
            ('accumulator', 'Accumulator'),
            ('trixie', 'Trixie'),
            ('yankee', 'Yankee'),
            ('canadian', 'Canadian / Super Yankee'),
            ('patent', 'Patent'),
            ('lucky15', 'Lucky 15'),
            ('lucky31', 'Lucky 31'),
            ('lucky63', 'Lucky 63'),
            ('heinz', 'Heinz'),
            ('super_heinz', 'Super Heinz'),
            ('goliath', 'Goliath'),
            ('super_heinz_singles', 'Super Heinz with Singles'),
            ('super_goliath', 'Super Goliath'),
        ],
        null=True,
        blank=True
    )  # Type of bet
    each_way = models.CharField(
        max_length=3,
        choices=[
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        default='no'
    )  # Single condition: Each Way (Yes/No)
    
    confidence = models.PositiveSmallIntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')],
        null=True,
        blank=True,
        help_text="Confidence level (1-5 stars, optional)"
    )

    # Updated fields for backend verification
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('win', 'Win'),
            ('loss', 'Loss'),
            ('dead_heat', 'Dead Heat'),
            ('void_non_runner', 'Void/Non Runner'),
        ],
        default='pending'
    )  # Updated status options
    resolution_note = models.TextField(blank=True, null=True)  # Optional note explaining the verification result
    verified_at = models.DateTimeField(blank=True, null=True)  # Timestamp of verification

    visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('premium', 'Premium Users Only'),
            ('subscribers', 'All Subscribers'),
            ('tier_specific', 'Specific Tiers')
        ],
        default='public'
    )
    allowed_tiers = models.ManyToManyField('TipsterTier', blank=True, related_name='exclusive_tips')
    release_schedule = models.JSONField(
        default=dict,
        help_text='JSON mapping tier IDs to release times'
    )
    is_released = models.BooleanField(default=True)
    scheduled_release = models.DateTimeField(null=True, blank=True)
    is_premium_tip = models.BooleanField(default=False, help_text='Is this a Premium Tip (only for Premium users)?')
    premium_tip_posted_at = models.DateTimeField(null=True, blank=True, help_text='When this Premium Tip was posted.')
    premium_tip_views = models.IntegerField(default=0, help_text='Number of times this Premium Tip was viewed.')

    def is_visible_to(self, user):
        """Check if tip is visible to user based on their tier and timing."""
        if not user.is_authenticated:
            return False

        # Premium users can see all tips immediately
        if user.userprofile.tier == 'premium':
            return True

        # For free users, check if the tip is from a top tipster
        if self.user.userprofile.is_top_tipster:
            # Check if 1 hour has passed since tip creation
            time_since_creation = timezone.now() - self.created_at
            return time_since_creation.total_seconds() >= 3600  # 1 hour in seconds

        # Free users can see non-top-tipster tips immediately
        return True

    def __str__(self):
        return f"{self.user.username} - {self.sport}: {self.text[:20]}"  # String representation for admin/debugging

    def clean(self):
        super().clean()
        # Only validate odds if they are provided
        if self.odds and self.odds_format:
            # Validate odds format
            if self.odds_format not in ['decimal', 'fractional']:
                raise ValidationError({'odds_format': 'Invalid odds format'})
            
            # Validate odds value
            if self.odds_format == 'decimal':
                try:
                    odds = float(self.odds)
                    if odds < 1.0:
                        raise ValidationError({'odds': 'Decimal odds must be greater than or equal to 1.0'})
                except ValueError:
                    raise ValidationError({'odds': 'Invalid decimal odds format'})
            elif self.odds_format == 'fractional':
                try:
                    num, denom = map(int, self.odds.split('/'))
                    if denom == 0:
                        raise ValidationError({'odds': 'Denominator cannot be zero'})
                except (ValueError, AttributeError):
                    raise ValidationError({'odds': 'Invalid fractional odds format'})
        
        # Validate bet type if provided
        if self.bet_type and self.bet_type not in ['single', 'double', 'treble', 'accumulator']:
            raise ValidationError({'bet_type': 'Invalid bet type'})

        # Validate JSON fields
        try:
            if self.poll:
                json.loads(self.poll)
            if self.emojis:
                json.loads(self.emojis)
            if self.release_schedule:
                if not isinstance(self.release_schedule, dict):
                    raise ValidationError({'release_schedule': 'Must be a valid JSON object'})
        except json.JSONDecodeError:
            raise ValidationError({'poll': 'Invalid JSON format'})

    def get_release_schedule(self):
        """Safe access to release schedule data."""
        return self.release_schedule or {}

    def get_poll_data(self):
        """Safe access to poll data."""
        try:
            return json.loads(self.poll) if self.poll else {}
        except json.JSONDecodeError:
            return {}

    def calculate_revenue_share(self):
        """Calculate revenue share for this tip."""
        if not self.user.userprofile.is_top_tipster:
            return 0

        # Get total premium revenue for the month
        total_premium_revenue = UserProfile.objects.filter(
            tier='premium'
        ).count() * 7  # €7 per premium user

        # Calculate share based on tipster's performance
        tipster = self.user.userprofile
        if tipster.revenue_share_percentage > 0:
            return (total_premium_revenue * tipster.revenue_share_percentage) / 100
        return 0

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile with a handle when a new User is created."""
    if created:
        # Generate a unique handle based on username
        base_handle = f"@{instance.username}"
        handle = base_handle
        counter = 1
        
        # Ensure handle uniqueness
        while UserProfile.objects.filter(handle=handle).exists():
            handle = f"{base_handle}{counter}"
            counter += 1
            
        UserProfile.objects.create(
            user=instance,
            handle=handle,
            full_name=instance.username
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure UserProfile is saved when User is saved."""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

@receiver(post_save, sender=Tip)
def update_user_stats(sender, instance, created, **kwargs):
    """Update user statistics when a tip is created or updated."""
    if created or instance.status in ['win', 'loss']:
        profile = instance.user.userprofile
        profile.total_tips = Tip.objects.filter(user=instance.user).count()
        profile.wins = Tip.objects.filter(user=instance.user, status='win').count()
        if profile.total_tips > 0:
            profile.win_rate = (profile.wins / profile.total_tips) * 100
        else:
            profile.win_rate = 0
        profile.save()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    description = models.TextField(max_length=160, blank=True)
    location = models.CharField(max_length=100, blank=True)
    handle = models.CharField(max_length=15, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    allow_messages = models.CharField(max_length=20, choices=[
        ('no_one', 'No one'),
        ('followers', 'Followers'),
        ('everyone', 'Everyone'),
    ], default='everyone')
    win_rate = models.FloatField(default=0.0)
    total_tips = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    kyc_completed = models.BooleanField(default=False)
    payment_completed = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    premium_until = models.DateTimeField(null=True, blank=True)
    premium_features = models.JSONField(
        default=dict,
        help_text='Features enabled for this user'
    )
    is_tipster = models.BooleanField(default=False)
    tipster_verified = models.BooleanField(default=False)
    total_subscribers = models.IntegerField(default=0)
    subscription_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tipster_description = models.TextField(blank=True)
    tipster_rules = models.TextField(blank=True)
    minimum_tier_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    maximum_tier_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Existing Badge fields
    has_badge_winning_streak_3 = models.BooleanField(default=False)
    has_badge_winning_streak_5 = models.BooleanField(default=False)
    has_badge_high_odds_win = models.BooleanField(default=False)
    has_badge_tips_10 = models.BooleanField(default=False)
    has_badge_tips_50 = models.BooleanField(default=False)
    has_badge_tips_100 = models.BooleanField(default=False)
    has_badge_win_rate_60 = models.BooleanField(default=False)
    has_badge_win_rate_75 = models.BooleanField(default=False)
    has_badge_football_expert = models.BooleanField(default=False)
    has_badge_horse_expert = models.BooleanField(default=False)

    # New Badge fields - General Performance
    has_badge_hot_streak = models.BooleanField(default=False)
    has_badge_blazing_inferno = models.BooleanField(default=False)
    has_badge_ice_cold = models.BooleanField(default=False)
    has_badge_tipster_titan = models.BooleanField(default=False)
    has_badge_rookie_rocket = models.BooleanField(default=False)

    # New Badge fields - Sport Specific
    has_badge_soccer_sniper = models.BooleanField(default=False)
    has_badge_hoop_hero = models.BooleanField(default=False)
    has_badge_touchdown_tycoon = models.BooleanField(default=False)
    has_badge_wicket_wizard = models.BooleanField(default=False)
    has_badge_hole_in_one = models.BooleanField(default=False)

    # New Badge fields - Humorous
    has_badge_crystal_ball = models.BooleanField(default=False)
    has_badge_upset_oracle = models.BooleanField(default=False)
    has_badge_late_night = models.BooleanField(default=False)
    has_badge_meme_lord = models.BooleanField(default=False)
    has_badge_hail_mary = models.BooleanField(default=False)

    # New Badge fields - Community
    has_badge_crowd_favorite = models.BooleanField(default=False)
    has_badge_tipster_mentor = models.BooleanField(default=False)
    has_badge_streak_starter = models.BooleanField(default=False)
    has_badge_anniversary = models.BooleanField(default=False)
    has_badge_viral = models.BooleanField(default=False)

    tier = models.CharField(
        max_length=10,
        choices=[('free', 'Free'), ('premium', 'Premium')],
        default='free',
        help_text='Current subscription tier for the user.'
    )
    tier_expiry = models.DateTimeField(null=True, blank=True, help_text='When the current paid tier expires.')
    trial_used = models.BooleanField(default=False, help_text='Has the user used their free trial?')
    is_top_tipster = models.BooleanField(default=False, help_text='Is this user a Top Tipster?')
    top_tipster_since = models.DateTimeField(null=True, blank=True, help_text='When the user became a Top Tipster.')

    # Revenue tracking
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Total earnings from tips and revenue sharing'
    )
    monthly_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Earnings for current month'
    )
    revenue_share_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Percentage of premium revenue shared with this tipster'
    )

    def save(self, *args, **kwargs):
        # Ensure handle starts with @
        if self.handle and not self.handle.startswith('@'):
            self.handle = f"@{self.handle}"
        super().save(*args, **kwargs)

    @property
    def followers_count(self):
        return Follow.objects.filter(followed=self.user).count()

    def __str__(self):
        return f"{self.user.username}'s profile"

    def can_subscribe_to_tipsters(self):
        """Check if user can subscribe to pro tipsters."""
        return self.is_premium and (
            self.premium_until is None or 
            self.premium_until > timezone.now()
        )

    def can_become_tipster(self):
        """Check if user can become a pro tipster."""
        return self.is_premium and (
            self.premium_until is None or 
            self.premium_until > timezone.now()
        )

    def can_post_tip(self):
        """Return (True, reason) if user can post a tip right now."""
        from django.utils import timezone
        now = timezone.now()
        today = now.date()
        tips_today = self.user.tip_set.filter(created_at__date=today).count()
        tips_this_month = self.user.tip_set.filter(created_at__year=now.year, created_at__month=now.month).count()
        if self.tier == 'free':
            if tips_today >= 2:
                return False, 'Free tier: Max 2 tips per day.'
            if tips_this_month >= 60:
                return False, 'Free tier: Max 60 tips per month.'
        elif self.tier == 'premium':
            if tips_this_month >= 100:
                return False, 'Premium tier: Max 100 tips per month.'
        # Premium: no enforced limit (could add a cap if desired)
        return True, ''

    def can_follow_more(self):
        """Return (True, reason) if user can follow another tipster."""
        if self.tier == 'free':
            following_count = self.user.following.count()
            if following_count >= 20:
                return False, 'Free tier: Max 20 follows.'
        return True, ''

    def can_comment(self):
        """Return True if user can comment on tips."""
        return self.tier in ['premium']

    def can_view_premium_tip(self):
        """Check if user can view premium tips."""
        return self.tier == 'premium'

    def can_post_premium_tip(self):
        """Check if user can post premium tips."""
        return self.tier == 'premium' and self.is_tipster

    def is_ad_free(self):
        """Check if user has ad-free experience."""
        return self.tier == 'premium'

    def can_view_early_tips(self):
        """Check if user can view tips before the 1-hour delay."""
        return self.tier == 'premium'

    def can_earn_revenue(self):
        """Check if user can earn from tips and revenue sharing."""
        return self.tier == 'premium' and self.is_tipster

    def get_tip_visibility_delay(self):
        """Get the delay in minutes before tips become visible to free users."""
        return 60  # 1 hour delay for free users

    def get_premium_features(self):
        """Get list of premium features available to user."""
        if self.tier == 'premium':
            return {
                'unlimited_tips': True,
                'unlimited_follows': True,
                'ad_free': True,
                'early_access': True,
                'top_tipsters': True,
                'revenue_sharing': True,
                'enhanced_engagement': True
            }
        return {
            'unlimited_tips': False,
            'unlimited_follows': False,
            'ad_free': False,
            'early_access': False,
            'top_tipsters': False,
            'revenue_sharing': False,
            'enhanced_engagement': False
        }

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='likes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip', 'comment')

    def __str__(self):
        if self.tip:
            return f"{self.user.username} liked {self.tip.user.username}'s tip"
        return f"{self.user.username} liked a comment"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='shares', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip')

    def __str__(self):
        return f"{self.user.username} shared {self.tip}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    image = models.ImageField(upload_to='comments/', blank=True, null=True)
    gif_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.tip.user.username}'s tip: {self.content[:20]}"

class MessageThread(models.Model):
    participants = models.ManyToManyField(User, related_name='message_threads')
    last_message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread with {', '.join(p.username for p in self.participants.all()[:2])}"

    def get_other_participant(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def update_last_message(self):
        latest_message = self.messages.order_by('-created_at').first()
        if latest_message:
            self.last_message = latest_message.content[:30]
            self.updated_at = latest_message.created_at
            self.save()

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    gif_url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} in {self.thread}: {self.content[:20]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.thread.update_last_message()

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)  # e.g., 'like', 'comment', 'follow'
    content = models.TextField()  # Notification message
    read = models.BooleanField(default=False)  # Whether notification has been read
    created_at = models.DateTimeField(auto_now_add=True)  # When notification was created
    related_tip = models.ForeignKey(Tip, on_delete=models.CASCADE, null=True, blank=True)  # Related tip if any
    related_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)  # Related comment if any
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='related_notifications')  # Related user if any

    def __str__(self):
        return f"Notification for {self.user.username}: {self.content[:50]}"

    class Meta:
        ordering = ['-created_at']  # Most recent notifications first

# DEPRECATED: Old tier/subscription models (to be removed in future)
class TipsterTier(models.Model):
    """DEPRECATED: Model for tipster subscription tiers. No longer used in new monetization model."""
    tipster = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_tiers')
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField()
    features = models.JSONField(default=list)
    max_subscribers = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    tip_release_delay = models.IntegerField(
        default=0,
        help_text='Minutes to delay tip release for this tier'
    )
    priority_access = models.BooleanField(
        default=False,
        help_text='Whether this tier gets immediate access to tips'
    )
    can_view_analysis = models.BooleanField(default=True)
    can_view_history = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('tipster', 'name')
        ordering = ['price']

    def calculate_release_time(self, base_time):
        """Calculate when a tip should be released for this tier."""
        if self.priority_access:
            return base_time
        return base_time + timezone.timedelta(minutes=self.tip_release_delay)

    def get_tier_features(self):
        """Get list of tier features including timing."""
        base_features = self.features or []
        timing_feature = (
            "Instant access to tips" if self.priority_access
            else f"Tips released after {self.tip_release_delay} minutes"
        )
        return [timing_feature] + base_features

    def save(self, *args, **kwargs):
        # Create or update Stripe price if not exists
        if not self.stripe_price_id and settings.STRIPE_SECRET_KEY:
            try:
                price = stripe.Price.create(
                    unit_amount=int(self.price * 100),  # Convert to cents
                    currency='eur',  # Using EUR as default
                    recurring={'interval': 'month'},
                    product_data={
                        'name': f"{self.tipster.username} - {self.name} Tier",
                        'description': self.description
                    }
                )
                self.stripe_price_id = price.id
            except Exception as e:
                # Log the error but don't prevent saving
                print(f"Error creating Stripe price: {e}")
        
        super().save(*args, **kwargs)

    def get_subscriber_count(self):
        """Get the number of active subscribers for this tier."""
        return self.subscriptions.filter(status='active').count()

    def is_full(self):
        """Check if tier has reached its subscriber limit."""
        if self.max_subscribers is None:
            return False
        return self.get_subscriber_count() >= self.max_subscribers

    def get_monthly_revenue(self):
        """Calculate monthly revenue from this tier."""
        active_subs = self.get_subscriber_count()
        return self.price * active_subs

    def clean(self):
        super().clean()
        # Validate features JSON
        if self.features:
            if not isinstance(self.features, list):
                raise ValidationError({'features': 'Must be a valid JSON array'})

    def get_features(self):
        """Safe access to tier features."""
        try:
            if not isinstance(self.features, list):
                return []
            return self.features
        except Exception:
            return []

class TipsterSubscription(models.Model):
    """DEPRECATED: Model for user subscriptions to tipsters. No longer used in new monetization model."""
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tipster_subscriptions')
    tier = models.ForeignKey(TipsterTier, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired')
    ], default='incomplete')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('subscriber', 'tier')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subscriber.username} -> {self.tier.tipster.username} ({self.tier.name})"

    def is_active(self):
        """Check if subscription is currently active."""
        return (
            self.status == 'active' and 
            self.end_date > timezone.now() and
            not self.tier.is_full()
        )

    def days_remaining(self):
        """Get number of days remaining in current billing period."""
        if not self.is_active():
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)

    def cancel(self):
        """Cancel the subscription."""
        if self.stripe_subscription_id:
            try:
                stripe.Subscription.delete(self.stripe_subscription_id)
            except Exception as e:
                # Log the error but continue with local cancellation
                print(f"Error cancelling Stripe subscription: {e}")
        
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()

        # Update tipster stats
        profile = self.tier.tipster.userprofile
        profile.total_subscribers = F('total_subscribers') - 1
        profile.subscription_revenue = F('subscription_revenue') - self.tier.price
        profile.save()

    def renew(self):
        """Renew the subscription for another period."""
        if not self.auto_renew or not self.is_active():
            return False
            
        self.end_date = self.end_date + timezone.timedelta(days=30)
        self.last_payment_date = timezone.now()
        self.next_payment_date = self.end_date
        self.save()
        return True

class EmailVerificationToken(models.Model):
    """Model for storing email verification tokens."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification token for {self.user.username}"

    class Meta:
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        ordering = ['-created_at']

class ChatMessage(models.Model):
    """Model for public chat room messages."""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    gif_url = models.URLField(blank=True, null=True)
    emoji = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.sender.username if self.sender else 'Anonymous'}: {self.content[:20]}"