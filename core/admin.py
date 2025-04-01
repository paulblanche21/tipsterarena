from django.contrib import admin
from .models import UserProfile, Tip, Like, Follow, Share, Comment, RaceMeeting, RaceResult

# Custom admin configuration for UserProfile model
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing UserProfile instances."""
    list_display = ('user', 'handle', 'description', 'location')  # Columns shown in the list view
    search_fields = ('user__username', 'handle')  # Enable search by username or handle
    list_filter = ('handle',)  # Filter options to identify profiles with specific handles

# Custom admin configuration for Tip model
@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    """Admin interface for managing Tip instances."""
    list_display = ('user', 'sport', 'text', 'created_at')  # Columns shown in the list view
    search_fields = ('user__username', 'text')  # Enable search by username or tip text
    list_filter = ('sport',)  # Filter tips by sport category

# Basic admin registrations for other models with default settings
admin.site.register(Like)       # Admin interface for Like model
admin.site.register(Follow)     # Admin interface for Follow model
admin.site.register(Share)      # Admin interface for Share model
admin.site.register(Comment)    # Admin interface for Comment model
admin.site.register(RaceMeeting)  # Admin interface for RaceMeeting model
admin.site.register(RaceResult)   # Admin interface for RaceResult model