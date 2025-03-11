from django.db import models
from django.contrib.auth.models import User

class Tip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sport = models.CharField(max_length=20, choices=[
        ('football', 'Football'),
        ('golf', 'Golf'),
        ('tennis', 'Tennis'),
        ('horse_racing', 'Horse Racing'),
    ])
    text = models.TextField()
    audience = models.CharField(  # New field
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
    

# models.py (relevant snippet)
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
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip')  # Prevent duplicate likes

    def __str__(self):
        return f"{self.user.username} liked {self.tip.user.username}'s tip"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')  # Prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"


class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name='shares')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tip')  # Prevent duplicate shares

    def __str__(self):
        return f"{self.user.username} shared {self.tip.user.username}'s tip"
    
class MessageThread(models.Model):
    participants = models.ManyToManyField(User, related_name='message_threads')
    last_message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Thread with {', '.join(p.username for p in self.participants.all()[:2])}"

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} in {self.thread}: {self.content[:20]}"