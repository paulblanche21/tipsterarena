"""Views for Tipster Arena."""

__all__ = [
    # Auth views
    'login_view', 'signup_view', 'kyc_view', 'profile_setup_view',
    'skip_profile_setup', 'payment_view', 'create_checkout_session',
    'payment_success', 'skip_payment',

    # Tip views
    'post_tip', 'edit_tip', 'delete_tip', 'LikeTipView',
    'share_tip', 'comment_tip', 'get_tip_comments', 'tip_detail',
    'tip_list', 'verify_tip',

    # Profile views
    'profile', 'profile_edit_view',

    # Sport views
    'sport_view', 'home',

    # Interaction views
    'follow_user', 'messages_view', 'send_message',
    'get_thread_messages', 'notifications', 'message_settings_view',
    'bookmarks', 'like_comment', 'share_comment', 'toggle_bookmark',
    'get_messages', 'start_message_thread', 'search_users',
    'update_message_settings', 'mark_notification_read',

    # API views
    'current_user_api', 'suggested_users_api',
    'trending_tips_api', 'VerifyTipView',
    'BurstRateThrottle', 'SustainedRateThrottle',
    'upload_chat_image_api',

    # General views
    'landing', 'search', 'csp_report',
    'terms_of_service', 'privacy_policy',
    'cookie_policy', 'accessibility', 'chat_view',

    # Subscription views
    'become_tipster', 'tipster_dashboard', 'manage_tiers',
    'subscribe_to_tipster', 'cancel_subscription', 'setup_tiers',
    'tier_setup', 'stripe_webhook', 'top_tipsters_leaderboard'
]

from .auth_views import (
    login_view, signup_view, kyc_view, profile_setup_view,
    skip_profile_setup, payment_view, create_checkout_session,
    payment_success, skip_payment
)

from .tip_views import (
    post_tip, edit_tip, delete_tip, LikeTipView,
    share_tip, comment_tip, get_tip_comments, tip_detail,
    tip_list, verify_tip
)

from .profile_views import (
    profile, profile_edit_view
)

from .sport_views import (
    sport_view, home
)

from .interaction_views import (
    follow_user, messages_view, send_message,
    get_thread_messages, notifications, message_settings_view,
    bookmarks, like_comment, share_comment, toggle_bookmark,
    get_messages, start_message_thread, search_users,
    update_message_settings, mark_notification_read
)

from .api_views import (
    current_user_api, suggested_users_api,
    trending_tips_api, VerifyTipView,
    BurstRateThrottle, SustainedRateThrottle,
    upload_chat_image_api
)

from .general_views import (
    landing, search, csp_report,
    terms_of_service, privacy_policy,
    cookie_policy, accessibility, chat_view
)

from .subscription_views import (
    become_tipster, tipster_dashboard, manage_tiers,
    subscribe_to_tipster, cancel_subscription, setup_tiers,
    tier_setup, stripe_webhook, top_tipsters_leaderboard
) 