"""Views for Tipster Arena."""

__all__ = [
    # Auth views
    'login_view', 'signup_view', 'kyc_view', 'profile_setup_view',
    'skip_profile_setup', 'payment_view', 'create_checkout_session',
    'payment_success', 'skip_payment',

    # Tip views
    'PostTipView', 'EditTipView', 'DeleteTipView', 'LikeTipView',
    'share_tip', 'comment_tip', 'get_tip_comments', 'TipDetailView',
    'tip_list', 'verify_tip',

    # Profile views
    'ProfileView', 'ProfileEditView',

    # Sport views
    'SportView',

    # Home view
    'HomeView',

    # Interaction views
    'FollowUserView', 'messages_view', 'send_message',
    'get_thread_messages', 'notifications', 'message_settings_view',
    'bookmarks', 'like_comment', 'share_comment', 'ToggleBookmarkView',
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
    'tier_setup', 'stripe_webhook', 'top_tipsters_leaderboard',

    # New FollowUserView
    'FollowUserView',
]

from .auth_views import (
    login_view, signup_view, kyc_view, profile_setup_view,
    skip_profile_setup, payment_view, create_checkout_session,
    payment_success, skip_payment
)

from .tip_views import (
    PostTipView, EditTipView, DeleteTipView, LikeTipView,
    share_tip, comment_tip, get_tip_comments, TipDetailView,
    tip_list, verify_tip
)

from .profile_views import (
    ProfileView, ProfileEditView
)

from .sport_views import (
    SportView
)

from .home_views import (
    HomeView
)

from .interaction_views import (
    FollowUserView, messages_view, send_message,
    get_thread_messages, notifications, message_settings_view,
    bookmarks, like_comment, share_comment, ToggleBookmarkView,
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