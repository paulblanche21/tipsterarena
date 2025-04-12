# models.py
from django.db import models
from django.contrib.auth.models import User


# Model representing a user's tip
class Tip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Tip author
    sport = models.CharField(
        max_length=20,
        choices=[
            ('football', 'Football'),
            ('golf', 'Golf'),
            ('tennis', 'Tennis'),
            ('horse_racing', 'Horse Racing'),
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
    odds = models.CharField(max_length=20)  # Store odds as a string (e.g., "2.5" or "2/1")
    odds_format = models.CharField(
        max_length=20,
        choices=[
            ('decimal', 'Decimal'),
            ('fractional', 'Fractional'),
        ]
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
        ]
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

    def __str__(self):
        return f"{self.user.username} - {self.sport}: {self.text[:20]}"  # String representation for admin/debugging

# Model extending the default User with profile-specific fields
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to Django User model
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # Profile picture
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)  # Profile banner image
    description = models.TextField(blank=True)  # User bio
    location = models.CharField(max_length=255, blank=True)  # Optional user location
    date_of_birth = models.DateField(blank=True, null=True)  # Optional birth date
    handle = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        help_text="Your unique handle starting with @ (e.g., @username)"
    )  # Unique social handle
    allow_messages = models.CharField(
        max_length=20,
        choices=[
            ('no_one', 'No one'),
            ('followers', 'Followers'),
            ('everyone', 'Everyone'),
        ],
        default='everyone',
        help_text="Who can send you message requests"
    )  # Message permission setting
    # New fields for user metrics
    win_rate = models.FloatField(default=0.0)  # Percentage of tips won
    total_tips = models.PositiveIntegerField(default=0)  # Total number of tips (won or lost)
    wins = models.PositiveIntegerField(default=0)  # Number of tips won

    @property
    def followers_count(self):
        """Calculate the number of followers for this user."""
        return Follow.objects.filter(followed=self.user).count()

    def __str__(self):
        return f"{self.user.username}'s profile"  # String representation for admin/debugging

# (Remaining models - Like, Follow, Share, Comment, MessageThread, Message, RaceMeeting, RaceResult - unchanged)
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