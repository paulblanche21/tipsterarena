# models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max

class Tip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sport = models.CharField(max_length=20, choices=[
        ('football', 'Football'),
        ('golf', 'Golf'),
        ('tennis', 'Tennis'),
        ('horse_racing', 'Horse Racing'),
    ])
    text = models.TextField()
    image = models.ImageField(upload_to='tips/', blank=True, null=True)
    gif_url = models.URLField(blank=True, null=True)  # New field for GIF URLs
    gif_width = models.PositiveIntegerField(null=True, blank=True)
    gif_height = models.PositiveIntegerField(null=True, blank=True)
    poll = models.TextField(blank=True, null=True, default='{}')  # Store JSON as string
    emojis = models.TextField(blank=True, null=True, default='{}')  # Store JSON as string
    location = models.CharField(max_length=255, blank=True, null=True)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    audience = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Everyone'),
            ('followers', 'Followers'),
        ],
        default='everyone'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.sport}: {self.text[:20]}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    handle = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        help_text="Your unique handle starting with @ (e.g., @username)"
    )

    def __str__(self):
        return f"{self.user.username}'s profile"

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
        """Get the other participant in the thread besides the current user."""
        return self.participants.exclude(id=current_user.id).first()

    def update_last_message(self):
        """Update the last_message field with the latest message content."""
        latest_message = self.messages.order_by('-created_at').first()
        if latest_message:
            self.last_message = latest_message.content[:30]  # Truncate for display
            self.updated_at = latest_message.created_at
            self.save()

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} in {self.thread}: {self.content[:20]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the thread's last_message and updated_at fields
        self.thread.update_last_message()


class RaceMeeting(models.Model):
    date = models.DateField()
    venue = models.CharField(max_length=100)
    url = models.URLField(unique=True)  # Unique to avoid duplicates

    def __str__(self):
        return f"{self.venue} - {self.date}"

    class Meta:
        unique_together = ('date', 'venue')  # Prevent duplicate meetings

class RaceResult(models.Model):
    meeting = models.ForeignKey(RaceMeeting, on_delete=models.CASCADE, related_name='results')
    time = models.CharField(max_length=10)  # e.g., "14:30"
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=10)
    horse = models.CharField(max_length=100)
    jockey = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.horse} (Position: {self.position})"