# models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max

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

    @property
    def followers_count(self):
        """Calculate the number of followers for this user."""
        return Follow.objects.filter(followed=self.user).count()

    def __str__(self):
        return f"{self.user.username}'s profile"  # String representation for admin/debugging

# Model for tracking likes on tips or comments
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')  # User who liked
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='likes', null=True, blank=True)  # Liked tip
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='likes', null=True, blank=True)  # Liked comment
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of like

    class Meta:
        unique_together = ('user', 'tip', 'comment')  # Ensure a user can like a tip or comment only once

    def __str__(self):
        if self.tip:
            return f"{self.user.username} liked {self.tip.user.username}'s tip"
        return f"{self.user.username} liked a comment"  # String representation for admin/debugging

# Model for tracking follow relationships between users
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # User following
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')  # User being followed
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of follow action

    class Meta:
        unique_together = ('follower', 'followed')  # Prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"  # String representation for admin/debugging

# Model for tracking shares of tips or comments
class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')  # User who shared
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='shares', null=True, blank=True)  # Shared tip
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='shares', null=True, blank=True)  # Shared comment
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of share

    class Meta:
        unique_together = ('user', 'tip', 'comment')  # Ensure a user can share a tip or comment only once

    def __str__(self):
        if self.tip:
            return f"{self.user.username} shared {self.tip.user.username}'s tip"
        return f"{self.user.username} shared a comment"  # String representation for admin/debugging

# Model for comments on tips
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')  # Comment author
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='comments')  # Associated tip
    content = models.TextField(max_length=280)  # Comment text
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of comment
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')  # Support for nested replies
    image = models.ImageField(upload_to='comments/', blank=True, null=True)  # Optional image attachment
    gif_url = models.URLField(blank=True, null=True)  # Optional GIF URL

    def __str__(self):
        return f"{self.user.username} commented on {self.tip.user.username}'s tip: {self.content[:20]}"  # String representation

# Model for message threads between users
class MessageThread(models.Model):
    participants = models.ManyToManyField(User, related_name='message_threads')  # Users in the thread
    last_message = models.TextField(blank=True)  # Preview of the latest message
    updated_at = models.DateTimeField(auto_now=True)  # Last update timestamp

    def __str__(self):
        return f"Thread with {', '.join(p.username for p in self.participants.all()[:2])}"  # String representation

    def get_other_participant(self, current_user):
        """Retrieve the other participant in a two-user thread."""
        return self.participants.exclude(id=current_user.id).first()

    def update_last_message(self):
        """Update the last_message field with the latest message content."""
        latest_message = self.messages.order_by('-created_at').first()
        if latest_message:
            self.last_message = latest_message.content[:30]  # Truncate for brevity
            self.updated_at = latest_message.created_at
            self.save()

# Model for individual messages within a thread
class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')  # Associated thread
    sender = models.ForeignKey(User, on_delete=models.CASCADE)  # Message sender
    content = models.TextField()  # Message text
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of message
    image = models.ImageField(upload_to='messages/', blank=True, null=True)  # Optional image attachment
    gif_url = models.URLField(blank=True, null=True)  # Optional GIF URL

    def __str__(self):
        return f"{self.sender.username} in {self.thread}: {self.content[:20]}"  # String representation

    def save(self, *args, **kwargs):
        """Override save to update thread's last_message after saving."""
        super().save(*args, **kwargs)
        self.thread.update_last_message()

# Model for horse racing meetings
class RaceMeeting(models.Model):
    date = models.DateField()  # Date of the meeting
    venue = models.CharField(max_length=100)  # Location of the meeting
    url = models.URLField(unique=True)  # Unique URL for the meeting

    def __str__(self):
        return f"{self.venue} - {self.date}"  # String representation

    class Meta:
        unique_together = ('date', 'venue')  # Prevent duplicate meetings by date and venue

# Model for race results within a meeting
class RaceResult(models.Model):
    meeting = models.ForeignKey(RaceMeeting, on_delete=models.CASCADE, related_name='results')  # Associated meeting
    time = models.CharField(max_length=10)  # Race time (e.g., "14:30")
    name = models.CharField(max_length=200)  # Race name
    position = models.CharField(max_length=10)  # Finishing position
    horse = models.CharField(max_length=100)  # Horse name
    jockey = models.CharField(max_length=100)  # Jockey name

    def __str__(self):
        return f"{self.name} - {self.horse} (Position: {self.position})"  # String representation