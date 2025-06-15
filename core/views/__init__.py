"""Views for Tipster Arena."""

__all__ = [
    # Auth views
    'LoginView',
    'SignupView',
    'KYCView',
    'ProfileSetupView',
    'SkipProfileSetupView',
    'PaymentView',
    'CreateCheckoutSessionView',
    'PaymentSuccessView',
    'SkipPaymentView',

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
    'FollowUserView', 'MessagesView', 'send_message',
    'get_thread_messages', 'notifications', 'MessageSettingsView',
    'bookmarks', 'like_comment', 'share_comment', 'ToggleBookmarkView',
    'get_messages', 'start_message_thread', 'SearchUsersView',
    'update_message_settings', 'mark_notification_read',

    # API views
    'current_user_api', 'suggested_users_api',
    'trending_tips_api', 'VerifyTipView',
    'BurstRateThrottle', 'SustainedRateThrottle',
    'upload_chat_image_api',

    # General views
    'LandingView',
    'SearchView',
    'CSPReportView',
    'TermsOfServiceView',
    'PrivacyPolicyView',
    'CookiePolicyView',
    'AccessibilityView',
    'ChatView',

    # Subscription views
    'become_tipster', 'tipster_dashboard', 'manage_tiers',
    'subscribe_to_tipster', 'cancel_subscription', 'setup_tiers',
    'TierSetupView', 'stripe_webhook', 'top_tipsters_leaderboard',

    # New FollowUserView
    'FollowUserView',
]

from .auth_views import (
    LoginView,
    SignupView,
    KYCView,
    ProfileSetupView,
    SkipProfileSetupView,
    PaymentView,
    CreateCheckoutSessionView,
    PaymentSuccessView,
    SkipPaymentView,
)

from .tip_views import (
    PostTipView, EditTipView, DeleteTipView, LikeTipView,
    share_tip, comment_tip, get_tip_comments, TipDetailView,
    tip_list, verify_tip
)

from .profile_views import (
    ProfileView,
    ProfileEditView,
)

from .sport_views import (
    SportView,
)

from .home_views import (
    HomeView,
)

from .interaction_views import (
    FollowUserView,
    MessagesView,
    MessageSettingsView,
    SearchUsersView,
    notifications,
    send_message,
    get_thread_messages,
    bookmarks,
    like_comment,
    share_comment,
    ToggleBookmarkView,
    get_messages,
    start_message_thread,
    update_message_settings,
    mark_notification_read,
)

from .general_views import (
    LandingView,
    SearchView,
    TermsOfServiceView,
    PrivacyPolicyView,
    CookiePolicyView,
    AccessibilityView,
    ChatView,
)

from .subscription_views import become_tipster, tipster_dashboard, manage_tiers, subscribe_to_tipster, cancel_subscription, setup_tiers, TierSetupView, stripe_webhook, top_tipsters_leaderboard

from .api_views import current_user_api, suggested_users_api, trending_tips_api, VerifyTipView, BurstRateThrottle, SustainedRateThrottle, upload_chat_image_api 