from django.contrib import admin
from .models import UserProfile, Tip, Like, Follow, Share, Comment, RaceMeeting, RaceResult

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'handle', 'description', 'location')  # Show these fields in the list view
    search_fields = ('user__username', 'handle')  # Search by username or handle
    list_filter = ('handle',)  # Filter to spot missing handles

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ('user', 'sport', 'text', 'created_at')  # Optional: customize Tip display
    search_fields = ('user__username', 'text')
    list_filter = ('sport',)

# Keep these as basic registrations unless you want customization
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(Share)
admin.site.register(Comment)
admin.site.register(RaceMeeting)
admin.site.register(RaceResult)