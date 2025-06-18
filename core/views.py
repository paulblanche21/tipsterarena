"""Views for Tipster Arena.

This module is a placeholder that imports all views from their respective modules.
The actual view implementations can be found in the views/ directory.
"""

from .views.auth_views import (
    login_view,
    signup_view,
    kyc_view,
    profile_setup_view,
    skip_profile_setup,
    payment_view,
    create_checkout_session,
    payment_success,
    skip_payment
)

from .views.tip_views import (
    PostTipView,
    EditTipView,
    DeleteTipView,
    LikeTipView,
    ShareTipView,
    CommentTipView,
    GetTipCommentsView,
    TipDetailView,
    TipListView,
    VerifyTipView
)

from .views.profile_views import (
    profile,
    profile_edit_view
)

from .views.sport_views import (
    sport_view,
    home
)

from .views.general_views import (
    landing,
    search,
    csp_report,
    terms_of_service,
    privacy_policy,
    cookie_policy,
    accessibility,
    chat_view
)

from .views.interaction_views import (
    follow_user,
    messages_view,
    send_message,
    get_thread_messages,
    notifications,
    message_settings_view,
    bookmarks,
    toggle_bookmark,
    like_comment,
    share_comment,
    mark_notification_read,
    get_messages,
    start_message_thread,
    search_users,
    update_message_settings,
    MarkMessagesReadView
)

from .views.subscription_views import (
    become_tipster,
    setup_tiers,
    tipster_dashboard,
    manage_tiers,
    subscribe_to_tipster,
    cancel_subscription,
    stripe_webhook,
    top_tipsters_leaderboard
)

from .views.api_views import (
    current_user_api,
    upload_chat_image_api,
    suggested_users_api,
    trending_tips_api,
    VerifyTipView,
    BurstRateThrottle,
    SustainedRateThrottle
)