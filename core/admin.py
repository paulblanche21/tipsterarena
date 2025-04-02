from django.contrib import admin
from .models import Tip, UserProfile, Like, Follow, Share, Comment, MessageThread, Message, RaceMeeting, RaceResult
import requests
from django.conf import settings

# Custom admin configuration for UserProfile model
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing UserProfile instances."""
    list_display = ('user', 'handle', 'description', 'location')  # Columns shown in the list view
    search_fields = ('user__username', 'handle')  # Enable search by username or handle
    list_filter = ('handle',)  # Filter options to identify profiles with specific handles
    actions = ['verify_as_won', 'verify_as_lost']

# Custom admin configuration for Tip model
@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    """Admin interface for managing Tip instances."""
    list_display = ('user', 'sport', 'text', 'created_at')  # Columns shown in the list view
    search_fields = ('user__username', 'text')  # Enable search by username or tip text
    list_filter = ('sport',)  # Filter tips by sport category
    actions = ['verify_as_won', 'verify_as_lost']

    def verify_as_won(self, request, queryset):
        for tip in queryset:
            if tip.status == 'pending':
                response = requests.post(
                    f"{settings.SITE_URL}/api/verify-tip/",
                    data={
                        'tip_id': tip.id,
                        'status': 'won',
                        'resolution_note': 'Verified as won via admin action'
                    },
                    headers={
                        'X-CSRFToken': request.COOKIES.get('csrftoken'),
                        'Cookie': f"sessionid={request.COOKIES.get('sessionid')}"
                    }
                )
                if response.status_code == 200:
                    self.message_user(request, f"Tip {tip.id} verified as won.")
                else:
                    self.message_user(request, f"Error verifying tip {tip.id}: {response.json().get('error')}")
    verify_as_won.short_description = "Verify selected tips as won"

    def verify_as_lost(self, request, queryset):
        for tip in queryset:
            if tip.status == 'pending':
                response = requests.post(
                    f"{settings.SITE_URL}/api/verify-tip/",
                    data={
                        'tip_id': tip.id,
                        'status': 'lost',
                        'resolution_note': 'Verified as lost via admin action'
                    },
                    headers={
                        'X-CSRFToken': request.COOKIES.get('csrftoken'),
                        'Cookie': f"sessionid={request.COOKIES.get('sessionid')}"
                    }
                )
                if response.status_code == 200:
                    self.message_user(request, f"Tip {tip.id} verified as lost.")
                else:
                    self.message_user(request, f"Error verifying tip {tip.id}: {response.json().get('error')}")
    verify_as_lost.short_description = "Verify selected tips as lost"

# Basic admin registrations for other models with default settings
admin.site.register(Like)       # Admin interface for Like model
admin.site.register(Follow)     # Admin interface for Follow model
admin.site.register(Share)      # Admin interface for Share model
admin.site.register(Comment)    # Admin interface for Comment model
admin.site.register(MessageThread)
admin.site.register(Message)
admin.site.register(RaceMeeting)  # Admin interface for RaceMeeting model
admin.site.register(RaceResult)   # Admin interface for RaceResult model