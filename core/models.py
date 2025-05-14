"""Core models for Tipster Arena.

Contains database models for user profiles, tips, and sports events.
"""

# models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import stripe
from django.core.exceptions import ValidationError

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
        """Check if tip is visible to a specific user."""
        # Public tips are visible to everyone
        if self.visibility == 'public':
            return True

        # Must be authenticated
        if not user.is_authenticated:
            return False

        # Tip owner can always see their tips
        if user == self.user:
            return True

        # Check premium access
        if self.visibility == 'premium' and not user.userprofile.is_premium:
            return False

        # Check subscriber access
        if self.visibility == 'subscribers':
            return TipsterSubscription.objects.filter(
                subscriber=user,
                tier__tipster=self.user,
                status='active'
            ).exists()

        # Check tier-specific access
        if self.visibility == 'tier_specific':
            current_time = timezone.now()
            user_subs = TipsterSubscription.objects.filter(
                subscriber=user,
                tier__in=self.allowed_tiers.all(),
                status='active'
            )
            
            for sub in user_subs:
                release_time = self.release_schedule.get(str(sub.tier.id))
                if release_time and timezone.datetime.fromisoformat(release_time) <= current_time:
                    return True
            
            return False

        return False

    def __str__(self):
        return f"{self.user.username} - {self.sport}: {self.text[:20]}"  # String representation for admin/debugging

    def clean(self):
        super().clean()
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
        
        # Validate bet type
        if self.bet_type not in ['single', 'double', 'treble', 'accumulator']:
            raise ValidationError({'bet_type': 'Invalid bet type'})

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
        choices=[('free', 'Free'), ('basic', 'Basic'), ('premium', 'Premium')],
        default='free',
        help_text='Current subscription tier for the user.'
    )
    tier_expiry = models.DateTimeField(null=True, blank=True, help_text='When the current paid tier expires.')
    trial_used = models.BooleanField(default=False, help_text='Has the user used their free trial?')
    is_top_tipster = models.BooleanField(default=False, help_text='Is this user a Top Tipster?')
    top_tipster_since = models.DateTimeField(null=True, blank=True, help_text='When the user became a Top Tipster.')

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
        elif self.tier == 'basic':
            if tips_this_month >= 100:
                return False, 'Basic tier: Max 100 tips per month.'
        # Premium: no enforced limit (could add a cap if desired)
        return True, ''

    def can_follow_more(self):
        """Return (True, reason) if user can follow another tipster."""
        if self.tier == 'free':
            following_count = self.user.following.count()
            if following_count >= 10:
                return False, 'Free tier: Max 10 follows.'
        return True, ''

    def can_comment(self):
        """Return True if user can comment on tips."""
        return self.tier in ['basic', 'premium']

    def can_view_premium_tip(self):
        """Return True if user can view Premium Tips."""
        return self.tier == 'premium'

    def can_post_premium_tip(self):
        """Return (True, reason) if user can post a Premium Tip (Top Tipsters only, 1/week)."""
        from django.utils import timezone
        if not self.is_top_tipster:
            return False, 'Only Top Tipsters can post Premium Tips.'
        now = timezone.now()
        week_ago = now - timezone.timedelta(days=7)
        tips_this_week = self.user.tip_set.filter(is_premium_tip=True, premium_tip_posted_at__gte=week_ago).count()
        if tips_this_week >= 1:
            return False, 'Top Tipsters: Only 1 Premium Tip per week.'
        return True, ''

    def is_ad_free(self):
        """Return True if user should not see ads (Premium only)."""
        return self.tier == 'premium'

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
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='shares', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip', 'comment')

    def __str__(self):
        if self.tip:
            return f"{self.user.username} shared {self.tip.user.username}'s tip"
        return f"{self.user.username} shared a comment"

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

    def __str__(self):
        return f"{self.sender.username} in {self.thread}: {self.content[:20]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.thread.update_last_message()

class RaceMeeting(models.Model):
    date = models.DateField()
    venue = models.CharField(max_length=100)
    url = models.URLField(unique=True)

    def __str__(self):
        return f"{self.venue} - {self.date}"

    class Meta:
        unique_together = ('date', 'venue')

class Race(models.Model):
    meeting = models.ForeignKey(RaceMeeting, on_delete=models.CASCADE, related_name="races")
    race_time = models.TimeField()
    name = models.CharField(max_length=200, blank=True)
    horses = models.JSONField()  # Store list of horses as JSON: [{"number": 1, "name": "Horse 1"}, ...]

    def __str__(self):
        return f"{self.name} at {self.race_time} - {self.meeting.venue}"

    class Meta:
        unique_together = ('meeting', 'race_time')

class RaceResult(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name="results", null=True)  # Temporarily nullable
    winner = models.CharField(max_length=100, blank=True)
    placed_horses = models.JSONField(blank=True, null=True)  # e.g., [{"position": 2, "name": "Horse 2"}, ...]

    def __str__(self):
        return f"Result for {self.race} - Winner: {self.winner}"
    
    

# Model for a football league
class FootballLeague(models.Model):
    league_id = models.CharField(max_length=50, unique=True)  # e.g., "eng.1", "esp.1"
    name = models.CharField(max_length=100)  # e.g., "Premier League"
    icon = models.CharField(max_length=10, default="⚽")  # Emoji icon
    priority = models.PositiveIntegerField(default=999)  # Sorting priority

    def __str__(self):
        return self.name

# Model for a football team
class FootballTeam(models.Model):
    name = models.CharField(max_length=100)  # Team name, e.g., "Manchester United"
    logo = models.URLField(blank=True, null=True)  # Team logo URL
    form = models.CharField(max_length=50, blank=True, null=True)  # Recent form, e.g., "W-L-D"
    record = models.CharField(max_length=50, blank=True, null=True)  # Season record, e.g., "10-5-3"

    def __str__(self):
        return self.name

# Model for team statistics in a match
class TeamStats(models.Model):
    possession = models.CharField(max_length=10, default='N/A')
    shots = models.CharField(max_length=10, default='N/A')
    shots_on_target = models.CharField(max_length=10, default='N/A')
    corners = models.CharField(max_length=10, default='N/A')
    fouls = models.CharField(max_length=10, default='N/A')

    def __str__(self):
        return f"Stats: {self.possession}% possession, {self.shots} shots"

# Model for a football event (match)
class FootballEvent(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)  # Match name, e.g., "Man United vs Arsenal"
    date = models.DateTimeField()  # Match date and time
    state = models.CharField(
        max_length=20,
        choices=[
            ('pre', 'Pre'),
            ('in', 'In Progress'),
            ('post', 'Post'),
            ('unknown', 'Unknown'),
        ],
        default='pre'
    )  # Match status
    status_description = models.CharField(max_length=100, default="Unknown")  # e.g., "Scheduled", "In Progress"
    status_detail = models.CharField(max_length=100, default="N/A")  # e.g., "Half Time", "Final"
    league = models.ForeignKey(FootballLeague, on_delete=models.CASCADE, related_name='events', null=True)
    venue = models.CharField(max_length=200, default="Location TBD")  # Venue name
    home_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='home_events', null=True)
    away_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name='away_events', null=True)
    home_score = models.IntegerField(default=0)
    away_score = models.IntegerField(default=0)
    home_team_stats = models.OneToOneField(TeamStats, on_delete=models.SET_NULL, null=True, related_name='home_team_event')
    away_team_stats = models.OneToOneField(TeamStats, on_delete=models.SET_NULL, null=True, related_name='away_team_event')
    clock = models.CharField(max_length=10, blank=True, null=True)  # Match clock, e.g., "45:00"
    period = models.PositiveIntegerField(default=0)  # Match period, e.g., 1 for first half
    broadcast = models.CharField(max_length=100, default="N/A")  # Broadcast info
    last_updated = models.DateTimeField(auto_now=True)  # Last time event was updated

    def __str__(self):
        return f"{self.name} ({self.date})"

    def clean(self):
        super().clean()
        # Validate event date
        if self.date < timezone.now():
            raise ValidationError({'date': 'Event date cannot be in the past'})
        
        # Validate home and away teams
        if self.home_team == self.away_team:
            raise ValidationError('Home and away teams cannot be the same')

# Model for key events (e.g., goals, cards)
class KeyEvent(models.Model):
    event = models.ForeignKey(FootballEvent, on_delete=models.CASCADE, related_name='key_events')
    type = models.CharField(max_length=50, default="Unknown")  # e.g., "Goal", "Yellow Card"
    time = models.CharField(max_length=10, default="N/A")  # e.g., "45:00"
    team = models.CharField(max_length=100, default="Unknown")  # Team involved
    player = models.CharField(max_length=100, default="Unknown")  # Player involved
    assist = models.CharField(max_length=100, blank=True, null=True)
    is_goal = models.BooleanField(default=False)
    is_yellow_card = models.BooleanField(default=False)
    is_red_card = models.BooleanField(default=False)
    is_penalty = models.BooleanField(default=False)  # New field for penalty goals

    def __str__(self):
        return f"{self.type} by {self.player} at {self.time}"

# Model for betting odds
class BettingOdds(models.Model):
    event = models.ForeignKey(FootballEvent, on_delete=models.CASCADE, related_name='odds')
    home_odds = models.CharField(max_length=20, default="N/A")  # Home team odds
    away_odds = models.CharField(max_length=20, default="N/A")  # Away team odds
    draw_odds = models.CharField(max_length=20, default="N/A")  # Draw odds
    provider = models.CharField(max_length=100, default="Unknown Provider")  # Odds provider

    def __str__(self):
        return f"Odds for {self.event.name}"

# Model for detailed match statistics
class DetailedStats(models.Model):
    event = models.ForeignKey(FootballEvent, on_delete=models.CASCADE, related_name='detailed_stats')
    possession = models.CharField(max_length=50, default="N/A")  # e.g., "55% - 45%"
    home_shots = models.CharField(max_length=10, default="N/A")  # Home team shots
    away_shots = models.CharField(max_length=10, default="N/A")  # Away team shots
    goals = models.JSONField(default=list)  # List of goals: [{"scorer": "Player", "team": "Team", "time": "45:00", "assist": "Player"}]

    def __str__(self):
        return f"Stats for {self.event.name}"

# Model for a golf tour (e.g., PGA, LPGA)
class GolfTour(models.Model):
    tour_id = models.CharField(max_length=50, unique=True)  # e.g., "pga", "lpga"
    name = models.CharField(max_length=100)  # e.g., "PGA Tour"
    icon = models.CharField(max_length=10, default="🏌️‍♂️")  # Emoji icon
    priority = models.PositiveIntegerField(default=999)  # Sorting priority

    def __str__(self):
        return self.name

# Model for a golf course
class GolfCourse(models.Model):
    name = models.CharField(max_length=200)  # Course name
    par = models.CharField(max_length=10, default="N/A")  # Course par
    yardage = models.CharField(max_length=20, default="N/A")  # Course yardage

    def __str__(self):
        return self.name

# Model for a golf player
class GolfPlayer(models.Model):
    player_id = models.CharField(max_length=50, unique=True)  # ESPN player ID
    name = models.CharField(max_length=100)  # Player name
    country = models.CharField(max_length=100, blank=True, null=True)  # Player's country
    world_ranking = models.PositiveIntegerField(null=True, blank=True)  # World ranking

    def __str__(self):
        return self.name

# Model for a golf event
class GolfEvent(models.Model):
    event_id = models.CharField(max_length=50, unique=True)  # ESPN event ID
    name = models.CharField(max_length=200)  # Event name, e.g., "The Masters"
    short_name = models.CharField(max_length=200)  # Shortened name
    date = models.DateTimeField()  # Event date and time
    state = models.CharField(
        max_length=20,
        choices=[
            ('pre', 'Pre'),
            ('in', 'In Progress'),
            ('post', 'Post'),
            ('unknown', 'Unknown'),
        ],
        default='pre'
    )  # Event status
    completed = models.BooleanField(default=False)  # Whether event is completed
    venue = models.CharField(max_length=200, default="Location TBD")  # Venue name
    city = models.CharField(max_length=100, default="Unknown")  # City
    state_location = models.CharField(max_length=100, default="Unknown")  # State or region
    tour = models.ForeignKey(GolfTour, on_delete=models.CASCADE, related_name='events', null=True)  # Associated tour
    course = models.ForeignKey(GolfCourse, on_delete=models.CASCADE, related_name='events', null=True)  # Associated course
    purse = models.CharField(max_length=20, default="N/A")  # Prize purse
    broadcast = models.CharField(max_length=100, default="N/A")  # Broadcast info
    current_round = models.PositiveIntegerField(default=1)  # Current round
    total_rounds = models.PositiveIntegerField(default=4)  # Total rounds
    is_playoff = models.BooleanField(default=False)  # Playoff status
    weather_condition = models.CharField(max_length=100, default="N/A")  # Weather condition
    weather_temperature = models.CharField(max_length=20, default="N/A")  # Weather temperature
    last_updated = models.DateTimeField(auto_now=True)  # Last update timestamp

    def __str__(self):
        return f"{self.name} ({self.date})"

# Model for leaderboard entries
class LeaderboardEntry(models.Model):
    event = models.ForeignKey(GolfEvent, on_delete=models.CASCADE, related_name='leaderboard')
    player = models.ForeignKey(GolfPlayer, on_delete=models.CASCADE, related_name='leaderboard_entries')
    position = models.CharField(max_length=10, default="N/A")  # Position in leaderboard
    score = models.CharField(max_length=10, default="N/A")  # Current score
    rounds = models.JSONField(default=list)  # List of round scores, e.g., [70, 72, 71, "N/A"]
    strokes = models.CharField(max_length=10, default="N/A")  # Total strokes
    status = models.CharField(max_length=20, default="active")  # Player status, e.g., "active", "withdrawn"

    def __str__(self):
        return f"{self.player.name} - {self.event.name} (Pos: {self.position})"

    class Meta:
        unique_together = ('event', 'player')
        
# Tennis models
class TennisLeague(models.Model):
    league_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default="🎾")
    priority = models.PositiveIntegerField(default=999)

    def __str__(self):
        return self.name

class TennisTournament(models.Model):
    tournament_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    league = models.ForeignKey(TennisLeague, on_delete=models.CASCADE, related_name='tournaments')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('upcoming', 'Upcoming'),
            ('active', 'Active'),
            ('completed', 'Completed')
        ],
        default='upcoming'
    )
    tournament_type = models.CharField(
        max_length=50,
        choices=[
            ('grand_slam', 'Grand Slam'),
            ('masters', 'Masters 1000'),
            ('atp_500', 'ATP 500'),
            ('atp_250', 'ATP 250'),
            ('wta_1000', 'WTA 1000'),
            ('wta_500', 'WTA 500'),
            ('wta_250', 'WTA 250')
        ],
        default='atp_250'
    )
    surface = models.CharField(
        max_length=20,
        choices=[
            ('hard', 'Hard'),
            ('clay', 'Clay'),
            ('grass', 'Grass'),
            ('carpet', 'Carpet')
        ],
        default='hard'
    )
    prize_money = models.CharField(max_length=100, blank=True, null=True)
    draw_size = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_tournament_type_display()})"

    class Meta:
        ordering = ['-start_date', 'name']

class TennisPlayer(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50, blank=True)
    world_ranking = models.CharField(max_length=10, default="N/A")

    def __str__(self):
        return self.name

class TennisPlayerStats(models.Model):
    player = models.OneToOneField(TennisPlayer, on_delete=models.CASCADE, related_name='stats')
    matches_played = models.PositiveIntegerField(default=0)
    matches_won = models.PositiveIntegerField(default=0)
    surface_stats = models.JSONField(default=dict)  # Stats by surface
    tournament_stats = models.JSONField(default=dict)  # Stats by tournament
    head_to_head = models.JSONField(default=dict)  # H2H records
    current_streak = models.IntegerField(default=0)
    best_ranking = models.PositiveIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.player.name}"

    def update_stats(self):
        """Update player statistics based on their matches"""
        matches = TennisEvent.objects.filter(
            Q(player1=self.player) | Q(player2=self.player),
            state='post'
        )
        
        self.matches_played = matches.count()
        self.matches_won = matches.filter(winner=self.player).count()
        
        # Update surface stats
        surface_stats = {}
        for surface in ['hard', 'clay', 'grass', 'carpet']:
            surface_matches = matches.filter(tournament__surface=surface)
            surface_stats[surface] = {
                'played': surface_matches.count(),
                'won': surface_matches.filter(winner=self.player).count()
            }
        self.surface_stats = surface_stats
        
        # Update tournament stats
        tournament_stats = {}
        for tournament in TennisTournament.objects.all():
            tournament_matches = matches.filter(tournament=tournament)
            tournament_stats[tournament.tournament_id] = {
                'played': tournament_matches.count(),
                'won': tournament_matches.filter(winner=self.player).count()
            }
        self.tournament_stats = tournament_stats
        
        self.save()

class TennisVenue(models.Model):
    name = models.CharField(max_length=200)
    court = models.CharField(max_length=100, default="Unknown")

    def __str__(self):
        return f"{self.name} - {self.court}"

class TennisEvent(models.Model):
    event_id = models.CharField(max_length=50, unique=True)
    tournament = models.ForeignKey(TennisTournament, on_delete=models.CASCADE, related_name='events')
    date = models.DateTimeField()
    state = models.CharField(
        max_length=20,
        choices=[
            ('pre', 'Pre'),
            ('in', 'In Progress'),
            ('post', 'Post'),
            ('unknown', 'Unknown'),
        ],
        default='pre'
    )
    completed = models.BooleanField(default=False)
    player1 = models.ForeignKey(TennisPlayer, on_delete=models.CASCADE, related_name='player1_events')
    player2 = models.ForeignKey(TennisPlayer, on_delete=models.CASCADE, related_name='player2_events')
    score = models.CharField(max_length=50, default="TBD")
    sets = models.JSONField(default=list)
    stats = models.JSONField(default=dict)
    clock = models.CharField(max_length=20, default="0:00")
    period = models.PositiveIntegerField(default=0)
    round_name = models.CharField(max_length=100, default="Unknown Round")
    venue = models.ForeignKey(TennisVenue, on_delete=models.SET_NULL, null=True, related_name='events')
    match_type = models.CharField(max_length=50, default="Unknown")
    player1_rank = models.CharField(max_length=10, default="N/A")
    player2_rank = models.CharField(max_length=10, default="N/A")
    last_updated = models.DateTimeField(auto_now=True)
    
    # New fields
    duration = models.DurationField(null=True, blank=True)
    tiebreak_sets = models.JSONField(default=list)  # Store tiebreak scores
    service_stats = models.JSONField(default=dict)  # Store service statistics
    point_by_point = models.JSONField(default=list)  # Store point-by-point data
    weather = models.JSONField(default=dict)  # Store weather conditions
    court_conditions = models.CharField(max_length=100, default="Normal")
    winner = models.ForeignKey(
        TennisPlayer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_matches'
    )

    def __str__(self):
        return f"{self.player1.name} vs {self.player2.name} - {self.tournament.name} ({self.date})"

    def save(self, *args, **kwargs):
        # Update winner if match is completed
        if self.state == 'post' and self.completed and not self.winner:
            self.update_winner()
        
        # Update player stats if match is completed
        if self.state == 'post' and self.completed:
            self.update_player_stats()
        
        super().save(*args, **kwargs)

    def update_winner(self):
        """Determine and set the winner of the match"""
        if not self.sets:
            return
        
        player1_sets = sum(1 for set_data in self.sets if int(set_data['team1Score']) > int(set_data['team2Score']))
        player2_sets = sum(1 for set_data in self.sets if int(set_data['team2Score']) > int(set_data['team1Score']))
        
        if player1_sets > player2_sets:
            self.winner = self.player1
        elif player2_sets > player1_sets:
            self.winner = self.player2

    def update_player_stats(self):
        """Update statistics for both players"""
        for player in [self.player1, self.player2]:
            stats, _ = TennisPlayerStats.objects.get_or_create(player=player)
            stats.update_stats()

    class Meta:
        indexes = [
            models.Index(fields=['date', 'state']),
            models.Index(fields=['tournament']),
            models.Index(fields=['winner']),
        ]

class TennisBettingOdds(models.Model):
    event = models.ForeignKey(TennisEvent, on_delete=models.CASCADE, related_name='odds')
    player1_odds = models.CharField(max_length=20, default="N/A")
    player2_odds = models.CharField(max_length=20, default="N/A")
    provider = models.CharField(max_length=100, default="Unknown Provider")

    def __str__(self):
        return f"Odds for {self.event.player1.name} vs {self.event.player2.name}"

# Model for a horse racing course
class HorseRacingCourse(models.Model):
    course_id = models.IntegerField(unique=True, null=True, blank=True)  # RacingPost course ID
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, default="Unknown")
    track_type = models.CharField(max_length=50)  # e.g., "Flat", "National Hunt"
    surface = models.CharField(max_length=50)  # e.g., "Turf", "All Weather"
    region = models.CharField(max_length=10, default="GB")  # e.g., "GB", "IRE", "FR"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

# Model for a horse racing meeting (replaces RaceMeeting)
class HorseRacingMeeting(models.Model):
    date = models.DateField()
    course = models.ForeignKey(HorseRacingCourse, on_delete=models.CASCADE, related_name='meetings')
    url = models.URLField(unique=True, blank=True, null=True)  # Optional RacingPost URL

    def __str__(self):
        return f"{self.course.name} - {self.date}"

    class Meta:
        unique_together = ('date', 'course')

# Model for a horse racing race (replaces Race)
class HorseRacingRace(models.Model):
    meeting = models.ForeignKey(HorseRacingMeeting, on_delete=models.CASCADE, related_name='races')
    race_id = models.IntegerField(unique=True)  # RacingPost race ID
    off_time = models.CharField(max_length=5)  # e.g., "14:40"
    name = models.CharField(max_length=255)  # Race name
    distance_round = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2m4½f"
    distance = models.CharField(max_length=50, blank=True, null=True)  # e.g., "2m4f127y"
    distance_f = models.FloatField(blank=True, null=True)  # Distance in furlongs
    pattern = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Grade 2", "Listed"
    race_class = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Class 1"
    type = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Chase", "Flat"
    age_band = models.CharField(max_length=50, blank=True, null=True)  # e.g., "5yo+"
    rating_band = models.CharField(max_length=50, blank=True, null=True)  # Rating band
    prize = models.CharField(max_length=50, blank=True, null=True)  # e.g., "£39,865"
    field_size = models.IntegerField(blank=True, null=True)  # Number of runners
    going = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Good"
    rail_movements = models.CharField(max_length=255, blank=True, null=True)  # Rail movements
    stalls = models.CharField(max_length=50, blank=True, null=True)  # Stalls position
    weather = models.CharField(max_length=255, blank=True, null=True)  # Weather conditions
    surface = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Turf"

    def __str__(self):
        return f"{self.name} at {self.off_time} - {self.meeting.course.name}"

    class Meta:
        unique_together = ('meeting', 'off_time', 'race_id')

# Model for a horse
class Horse(models.Model):
    horse_id = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=100)
    dob = models.DateField(blank=True, null=True)  # Date of birth
    age = models.IntegerField(blank=True, null=True)  # Age
    sex = models.CharField(max_length=50, blank=True, null=True)  # e.g., "gelding"
    sex_code = models.CharField(max_length=1, blank=True, null=True)  # e.g., "G"
    colour = models.CharField(max_length=50, blank=True, null=True)  # e.g., "b"
    region = models.CharField(max_length=50, blank=True, null=True)  # e.g., "IRE"
    breeder = models.CharField(max_length=100, blank=True, null=True)  # Breeder name
    dam = models.CharField(max_length=100, blank=True, null=True)  # Dam name
    dam_region = models.CharField(max_length=50, blank=True, null=True)  # Dam region
    sire = models.CharField(max_length=100, blank=True, null=True)  # Sire name
    sire_region = models.CharField(max_length=50, blank=True, null=True)  # Sire region
    grandsire = models.CharField(max_length=100, blank=True, null=True)  # Grandsire name
    damsire = models.CharField(max_length=100, blank=True, null=True)  # Damsire name
    damsire_region = models.CharField(max_length=50, blank=True, null=True)  # Damsire region

    def __str__(self):
        return self.name

# Model for a trainer
class Trainer(models.Model):
    trainer_id = models.CharField(max_length=16, unique=True)  # Changed to CharField
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Jockey(models.Model):
    jockey_id = models.CharField(max_length=16, unique=True)  # Changed to CharField
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Model for a runner in a race
class RaceRunner(models.Model):
    race = models.ForeignKey(HorseRacingRace, on_delete=models.CASCADE, related_name='runners')
    horse = models.ForeignKey(Horse, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
    jockey = models.ForeignKey(Jockey, on_delete=models.CASCADE, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Weight in stones and pounds
    number = models.IntegerField(default=0)  # Race card number
    draw = models.IntegerField(null=True, blank=True)  # Stall draw number
    headgear = models.CharField(max_length=50, blank=True, null=True)  # e.g., "b", "p", "t"
    headgear_first = models.BooleanField(default=False)  # First time wearing headgear
    lbs = models.IntegerField(blank=True, null=True)  # Weight in pounds
    official_rating = models.IntegerField(blank=True, null=True)  # Official rating
    rpr = models.IntegerField(blank=True, null=True)  # Racing Post Rating
    topspeed = models.IntegerField(blank=True, null=True)  # Topspeed rating
    form = models.CharField(max_length=50, blank=True, null=True)  # Recent form
    last_run = models.DateField(blank=True, null=True)  # Date of last run
    trainer_rtf = models.CharField(max_length=50, blank=True, null=True)  # Trainer RTF
    trainer_14_days_runs = models.IntegerField(blank=True, null=True)  # Trainer runs in last 14 days
    trainer_14_days_wins = models.IntegerField(blank=True, null=True)  # Trainer wins in last 14 days
    trainer_14_days_percent = models.FloatField(blank=True, null=True)  # Trainer win percentage in last 14 days
    owner = models.CharField(max_length=100, blank=True, null=True)  # Owner name
    comment = models.TextField(blank=True, null=True)  # Comment on horse
    spotlight = models.TextField(blank=True, null=True)  # Spotlight comment
    stats = models.JSONField(default=dict)  # Additional stats

    def __str__(self):
        return f"{self.horse.name} ({self.number})"

    class Meta:
        ordering = ['number']
        unique_together = ('race', 'number')

# Model for runner quotes
class RunnerQuote(models.Model):
    runner = models.ForeignKey(RaceRunner, on_delete=models.CASCADE, related_name='quotes')
    date = models.DateField()  # Quote date
    race_id = models.IntegerField(blank=True, null=True)  # Race ID
    course = models.CharField(max_length=100, blank=True, null=True)  # Course name
    course_id = models.IntegerField(blank=True, null=True)  # Course ID
    distance_f = models.FloatField(blank=True, null=True)  # Distance in furlongs
    distance_y = models.IntegerField(blank=True, null=True)  # Distance in yards
    quote = models.TextField()  # Quote text

    def __str__(self):
        return f"Quote for {self.runner.horse.name} on {self.date}"

# Model for race results (replaces RaceResult)
class HorseRacingResult(models.Model):
    race = models.ForeignKey(HorseRacingRace, on_delete=models.CASCADE, related_name='results')
    horse = models.ForeignKey(Horse, on_delete=models.CASCADE, related_name='results')
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, related_name='results')
    jockey = models.ForeignKey(Jockey, on_delete=models.SET_NULL, null=True, related_name='results')
    position = models.CharField(max_length=10, blank=True, null=True)  # Changed to CharField
    draw = models.IntegerField(blank=True, null=True)  # Draw position
    ovr_btn = models.FloatField(blank=True, null=True)  # Overall beaten distance
    btn = models.FloatField(blank=True, null=True)  # Beaten distance to previous horse
    lbs = models.IntegerField(blank=True, null=True)  # Weight carried
    headgear = models.CharField(max_length=50, blank=True, null=True)  # Headgear
    time = models.CharField(max_length=50, blank=True, null=True)  # Finishing time
    seconds = models.FloatField(blank=True, null=True)  # Time in seconds
    decimal_time = models.FloatField(blank=True, null=True)  # Decimal time
    prize = models.CharField(max_length=50, blank=True, null=True)  # Prize money
    official_rating = models.IntegerField(blank=True, null=True)  # Official rating
    rpr = models.IntegerField(blank=True, null=True)  # Racing Post Rating
    comment = models.TextField(blank=True, null=True)  # Comment on performance

    def __str__(self):
        return f"Result for {self.horse.name} in {self.race.name} - Pos: {self.position}"

    class Meta:
        unique_together = ('race', 'horse')

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

class HorseRacingBettingOdds(models.Model):
    runner = models.ForeignKey(RaceRunner, on_delete=models.CASCADE, related_name='odds')
    bookmaker = models.CharField(max_length=100)  # Bookmaker name
    odds = models.DecimalField(max_digits=7, decimal_places=2)  # Odds value
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bookmaker} odds for {self.runner}"

    class Meta:
        unique_together = ('runner', 'bookmaker')
        ordering = ['bookmaker', '-updated_at']

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