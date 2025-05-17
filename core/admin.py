"""Admin interface configuration for Tipster Arena models."""

# tipsterarena/core/admin.py
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
import requests
from rest_framework.authtoken.models import Token

from .models import (
      Tip, UserProfile, Like,
      Follow, Share,
      Comment, MessageThread, Message)

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    """Admin interface for managing betting tips and their verification status."""
    list_display = ('user', 'sport', 'text', 'odds', 'odds_format', 'bet_type', 'each_way', 'confidence', 'status', 'created_at')
    search_fields = ('user__username', 'text')
    list_filter = ('sport', 'each_way', 'status')
    actions = ['verify_as_win', 'verify_as_loss', 'verify_as_dead_heat', 'verify_as_void_non_runner']

    def verify_as_win(self, request, queryset):
        try:
            token = Token.objects.get_or_create(user=request.user)[0].key  # type: ignore[attr-defined]
            print(f"Using token: {token}")  # Debug to confirm token
        except Exception as e:
            self.message_user(
                request,
                f"Error retrieving token: {str(e)}",
                messages.ERROR
            )
            return

        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        }
        for tip in queryset:
            if tip.status == 'pending':
                try:
                    response = requests.post(
                        f"{settings.SITE_URL}/api/verify-tip/",
                        json={
                            'tip_id': tip.id,
                            'status': 'win',
                            'resolution_note': (
                                'Verified as win via admin action'
                            )
                        },
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    self.message_user(request, f"Tip {tip.id} verified as win.", messages.SUCCESS)
                except requests.exceptions.RequestException as e:
                    self.message_user(
                        request,
                        (
                            f"Error verifying tip {tip.id}: "
                            f"{response.json().get('error', response.text) if 'response' in locals() else str(e)}"
                        ),
                        messages.ERROR
                    )

    verify_as_win.short_description = "Verify selected tips as Win"

    def verify_as_loss(self, request, queryset):
        """Verify selected tips as Loss."""
        try:
            token = Token.objects.get_or_create(user=request.user)[0].key  # type: ignore[attr-defined]
            print(f"Using token: {token}")
        except Exception as e:
            self.message_user(
                request,
                f"Error retrieving token: {str(e)}",
                messages.ERROR
            )
            return

        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        }
        for tip in queryset:
            if tip.status == 'pending':
                try:
                    response = requests.post(
                        f"{settings.SITE_URL}/api/verify-tip/",
                        json={
                            'tip_id': tip.id,
                            'status': 'loss',
                            'resolution_note': (
                                'Verified as loss via admin action'
                            )
                        },
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    self.message_user(request, f"Tip {tip.id} verified as loss.", messages.SUCCESS)
                except requests.exceptions.RequestException as e:
                    self.message_user(
                        request,
                        (
                            f"Error verifying tip {tip.id}: "
                            f"{response.json().get('error', response.text) if 'response' in locals() else str(e)}"
                        ),
                        messages.ERROR
                    )

    verify_as_loss.short_description = "Verify selected tips as Loss"

    def verify_as_dead_heat(self, request, queryset):
        """Verify selected tips as Dead Heat."""
        try:
            token = Token.objects.get_or_create(user=request.user)[0].key  # type: ignore[attr-defined]
            print(f"Using token: {token}")
        except Exception as e:
            self.message_user(
                request,
                f"Error retrieving token: {str(e)}",
                messages.ERROR
            )
            return

        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        }
        for tip in queryset:
            if tip.status == 'pending':
                try:
                    response = requests.post(
                        f"{settings.SITE_URL}/api/verify-tip/",
                        json={
                            'tip_id': tip.id,
                            'status': 'dead_heat',
                            'resolution_note': (
                                'Verified as dead heat via admin action'
                            )
                        },
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    self.message_user(request, f"Tip {tip.id} verified as dead heat.", messages.SUCCESS)
                except requests.exceptions.RequestException as e:
                    self.message_user(
                        request,
                        (
                            f"Error verifying tip {tip.id}: "
                            f"{response.json().get('error', response.text) if 'response' in locals() else str(e)}"
                        ),
                        messages.ERROR
                    )

    verify_as_dead_heat.short_description = "Verify selected tips as Dead Heat"

    def verify_as_void_non_runner(self, request, queryset):
        """Verify selected tips as Void/Non Runner."""
        try:
            token = Token.objects.get_or_create(user=request.user)[0].key  # type: ignore[attr-defined]
            print(f"Using token: {token}")
        except Exception as e:
            self.message_user(
                request,
                f"Error retrieving token: {str(e)}",
                messages.ERROR
            )
            return

        headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        }
        for tip in queryset:
            if tip.status == 'pending':
                try:
                    response = requests.post(
                        f"{settings.SITE_URL}/api/verify-tip/",
                        json={
                            'tip_id': tip.id,
                            'status': 'void_non_runner',
                            'resolution_note': (
                                'Verified as void/non runner via admin action'
                            )
                        },
                        headers=headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    self.message_user(request, f"Tip {tip.id} verified as void/non runner.", messages.SUCCESS)
                except requests.exceptions.RequestException as e:
                    self.message_user(
                        request,
                        (
                            f"Error verifying tip {tip.id}: "
                            f"{response.json().get('error', response.text) if 'response' in locals() else str(e)}"
                        ),
                        messages.ERROR
                    )

    verify_as_void_non_runner.short_description = "Verify selected tips as Void/Non Runner"

# Other registrations unchanged...
admin.site.register(UserProfile)
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(Share)
admin.site.register(Comment)
admin.site.register(MessageThread)
admin.site.register(Message)
