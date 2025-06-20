"""Admin interface configuration for Tipster Arena models."""

# tipsterarena/core/admin.py
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from rest_framework.authtoken.models import Token

from .models import (
      Tip, UserProfile, Like,
      Follow, Share,
      Comment, MessageThread, Message)

class PendingTipFilter(admin.SimpleListFilter):
    """Filter to show pending tips."""
    title = 'Verification Status'
    parameter_name = 'verification_status'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pending Verification'),
            ('verified', 'Verified'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(status='pending')
        if self.value() == 'verified':
            return queryset.exclude(status='pending')
        return queryset

class TierFilter(admin.SimpleListFilter):
    """Filter to show users by tier."""
    title = 'Subscription Tier'
    parameter_name = 'tier'

    def lookups(self, request, model_admin):
        return (
            ('free', 'Free'),
            ('premium', 'Premium (€7/month)'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tier=self.value())
        return queryset

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    """Admin interface for managing betting tips and their verification status."""
    list_display = ('user', 'sport', 'text', 'odds', 'odds_format', 'bet_type', 'each_way', 'confidence', 'status', 'created_at')
    search_fields = ('user__username', 'text')
    list_filter = (PendingTipFilter, 'sport', 'each_way', 'status')
    actions = ['verify_as_win', 'verify_as_loss', 'verify_as_dead_heat', 'verify_as_void_non_runner']
    list_per_page = 50  # Show more tips per page
    ordering = ('-created_at',)  # Show newest tips first

    def get_queryset(self, request):
        """Customize the queryset to show pending tips first."""
        qs = super().get_queryset(request)
        return qs.order_by('status', '-created_at')  # Pending tips first, then by date

    def verify_as_win(self, request, queryset):
        """Verify selected tips as Win."""
        updated_count = 0
        for tip in queryset:
            tip.status = 'win'
            tip.verified = True
            tip.resolution_note = 'Verified as win via admin action'
            tip.save()
            updated_count += 1
        
        if updated_count == 1:
            self.message_user(request, f"Successfully verified 1 tip as win.", messages.SUCCESS)
        else:
            self.message_user(request, f"Successfully verified {updated_count} tips as win.", messages.SUCCESS)

    verify_as_win.short_description = "Verify selected tips as Win"

    def verify_as_loss(self, request, queryset):
        """Verify selected tips as Loss."""
        updated_count = 0
        for tip in queryset:
            tip.status = 'loss'
            tip.verified = True
            tip.resolution_note = 'Verified as loss via admin action'
            tip.save()
            updated_count += 1
        
        if updated_count == 1:
            self.message_user(request, f"Successfully verified 1 tip as loss.", messages.SUCCESS)
        else:
            self.message_user(request, f"Successfully verified {updated_count} tips as loss.", messages.SUCCESS)

    verify_as_loss.short_description = "Verify selected tips as Loss"

    def verify_as_dead_heat(self, request, queryset):
        """Verify selected tips as Dead Heat."""
        updated_count = 0
        for tip in queryset:
            tip.status = 'dead_heat'
            tip.verified = True
            tip.resolution_note = 'Verified as dead heat via admin action'
            tip.save()
            updated_count += 1
        
        if updated_count == 1:
            self.message_user(request, f"Successfully verified 1 tip as dead heat.", messages.SUCCESS)
        else:
            self.message_user(request, f"Successfully verified {updated_count} tips as dead heat.", messages.SUCCESS)

    verify_as_dead_heat.short_description = "Verify selected tips as Dead Heat"

    def verify_as_void_non_runner(self, request, queryset):
        """Verify selected tips as Void/Non Runner."""
        updated_count = 0
        for tip in queryset:
            tip.status = 'void_non_runner'
            tip.verified = True
            tip.resolution_note = 'Verified as void/non runner via admin action'
            tip.save()
            updated_count += 1
        
        if updated_count == 1:
            self.message_user(request, f"Successfully verified 1 tip as void/non runner.", messages.SUCCESS)
        else:
            self.message_user(request, f"Successfully verified {updated_count} tips as void/non runner.", messages.SUCCESS)

    verify_as_void_non_runner.short_description = "Verify selected tips as Void/Non Runner"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing user profiles and their subscription tiers."""
    list_display = ('user', 'handle', 'tier', 'tier_expiry', 'is_tipster', 'is_top_tipster', 'total_earnings')
    list_filter = (TierFilter, 'is_tipster', 'is_top_tipster')
    search_fields = ('user__username', 'handle', 'description')
    readonly_fields = ('total_earnings', 'monthly_earnings', 'revenue_share_percentage')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'handle', 'avatar', 'banner', 'description', 'location', 'date_of_birth')
        }),
        ('Subscription Status', {
            'fields': ('tier', 'tier_expiry', 'trial_used'),
            'description': 'Premium users (€7/month) get access to Top Tipsters and an ad-free experience.'
        }),
        ('Tipster Status', {
            'fields': ('is_tipster', 'is_top_tipster', 'top_tipster_since', 'tipster_description', 'tipster_rules')
        }),
        ('Earnings', {
            'fields': ('total_earnings', 'monthly_earnings', 'revenue_share_percentage')
        }),
        ('Account Settings', {
            'fields': ('allow_messages', 'kyc_completed', 'payment_completed', 'profile_completed')
        })
    )
    actions = ['upgrade_to_premium', 'downgrade_to_free']

    def upgrade_to_premium(self, request, queryset):
        """Upgrade selected users to Premium tier."""
        for profile in queryset:
            profile.tier = 'premium'
            profile.save()
        self.message_user(request, f"Successfully upgraded {queryset.count()} users to Premium tier.")
    upgrade_to_premium.short_description = "Upgrade selected users to Premium (€7/month)"

    def downgrade_to_free(self, request, queryset):
        """Downgrade selected users to Free tier."""
        for profile in queryset:
            profile.tier = 'free'
            profile.save()
        self.message_user(request, f"Successfully downgraded {queryset.count()} users to Free tier.")
    downgrade_to_free.short_description = "Downgrade selected users to Free"

# Other registrations unchanged...
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(Share)
admin.site.register(Comment)
admin.site.register(MessageThread)
admin.site.register(Message)
