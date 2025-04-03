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

# Custom admin configuration for Tip model
@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    """Admin interface for managing Tip instances."""
    list_display = ('user', 'sport', 'text', 'odds', 'odds_format', 'bet_type', 'each_way', 'confidence', 'status', 'created_at')  # Updated columns
    search_fields = ('user__username', 'text')  # Enable search by username or tip text
    list_filter = ('sport', 'each_way', 'status')  # Updated filters
    actions = ['verify_as_win', 'verify_as_loss', 'verify_as_dead_heat', 'verify_as_void_non_runner']

    def verify_as_win(self, request, queryset):
        """Verify selected tips as 'win' via API."""
        for tip in queryset:
            if tip.status == 'pending':
                response = requests.post(
                    f"{settings.SITE_URL}/api/verify-tip/",
                    data={
                        'tip_id': tip.id,
                        'status': 'win',  # Updated to match new status
                        'resolution_note': 'Verified as win via admin action'
                    },
                    headers={
                        'X-CSRFToken': request.COOKIES.get('csrftoken'),
                        'Cookie': f"sessionid={request.COOKIES.get('sessionid')}"
                    }
                )
                if response.status_code == 200:
                    self.message_user(request, f"Tip {tip.id} verified as win.")
                else:
                    self.message_user(request, f"Error verifying tip {tip.id}: {response.json().get('error')}")
    verify_as_win.short_description = "Verify selected tips as Win"

    def verify_as_loss(self, request, queryset):
        """Verify selected tips as 'loss' via API."""
        for tip in queryset:
            if tip.status == 'pending':
                response = requests.post(
                    f"{settings.SITE_URL}/api/verify-tip/",
                    data={
                        'tip_id': tip.id,
                        'status': 'loss',  # Updated to match new status
                        'resolution_note': 'Verified as loss via admin action'
                    },
                    headers={
                        'X-CSRFToken': request.COOKIES.get('csrftoken'),
                        'Cookie': f"sessionid={request.COOKIES.get('sessionid')}"
                    }
                )
                if response.status_code == 200:
                    self.message_user(request, f"Tip {tip.id} verified as loss.")
                else:
                    self.message_user(request, f"Error verifying tip {tip.id}: {response.json().get('error')}")
    verify_as_loss.short_description = "Verify selected tips as Loss"

    def verify_as_dead_heat(self, request, queryset):
        """Verify selected tips as 'dead_heat' via API."""
        for tip in queryset:
            if tip.status == 'pending':
                response = requests.post(
                    f"{settings.SITE_URL}/api/verify-tip/",
                    data={
                        'tip_id': tip.id,
                        'status': 'dead_heat',  # New status
                        'resolution_note': 'Verified as dead heat via admin action'
                    },
                    headers={
                        'X-CSRFToken': request.COOKIES.get('csrftoken'),
                        'Cookie': f"sessionid={request.COOKIES.get('sessionid')}"
                    }
                )
                if response.status_code == 200:
                    self.message_user(request, f"Tip {tip.id} verified as dead heat.")
                else:
                    self.message_user(request, f"Error verifying tip {tip.id}: {response.json().get('error')}")
    verify_as_dead_heat.short_description = "Verify selected tips as Dead Heat"

    def verify_as_void_non_runner(self, request, queryset):
        """Verify selected tips as 'void_non_runner' via API."""
        for tip in queryset:
            if tip.status == 'pending':
                response = requests.post(
                    f"{settings.SITE_URL}/api/verify-tip/",
                    data={
                        'tip_id': tip.id,
                        'status': 'void_non_runner',  # New status
                        'resolution_note': 'Verified as void/non runner via admin action'
                    },
                    headers={
                        'X-CSRFToken': request.COOKIES.get('csrftoken'),
                        'Cookie': f"sessionid={request.COOKIES.get('sessionid')}"
                    }
                )
                if response.status_code == 200:
                    self.message_user(request, f"Tip {tip.id} verified as void/non runner.")
                else:
                    self.message_user(request, f"Error verifying tip {tip.id}: {response.json().get('error')}")
    verify_as_void_non_runner.short_description = "Verify selected tips as Void/Non Runner"

# Basic admin registrations for other models with default settings
admin.site.register(Like)       # Admin interface for Like model
admin.site.register(Follow)     # Admin interface for Follow model
admin.site.register(Share)      # Admin interface for Share model
admin.site.register(Comment)    # Admin interface for Comment model
admin.site.register(MessageThread)
admin.site.register(Message)
admin.site.register(RaceMeeting)  # Admin interface for RaceMeeting model
admin.site.register(RaceResult)   # Admin interface for RaceResult model