"""Views for the Tipster Arena application."""

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
    EmailVerificationView,
)

from .tip_views import (
    PostTipView,
    EditTipView,
    DeleteTipView,
    LikeTipView,
    ShareTipView,
    CommentTipView,
    GetTipCommentsView,
    TipListView,
    VerifyTipView,
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
    SendMessageView,
    GetThreadMessagesView,
    NotificationsView,
    MessageSettingsView,
    BookmarksView,
    ToggleBookmarkView,
    LikeCommentView,
    ShareCommentView,
    MarkNotificationReadView,
    GetMessagesView,
    StartMessageThreadView,
    SearchUsersView,
    UpdateMessageSettingsView,
)

from .general_views import (
    LandingView,
    SearchView,
    CSPReportView,
    TermsOfServiceView,
    PrivacyPolicyView,
    CookiePolicyView,
    AccessibilityView,
    ChatView,
)

from .subscription_views import (
    BecomeTipsterView,
    SetupTiersView,
    TipsterDashboardView,
    ManageTiersView,
    SubscribeToTipsterView,
    CancelSubscriptionView,
    TopTipstersLeaderboardView,
    StripeWebhookView,
)

from .api_views import (
    CurrentUserView,
    UploadChatImageView,
    SuggestedUsersView,
    TrendingTipsView,
)

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
    'EmailVerificationView',

    # Tip views
    'PostTipView',
    'EditTipView',
    'DeleteTipView',
    'LikeTipView',
    'ShareTipView',
    'CommentTipView',
    'GetTipCommentsView',
    'TipListView',
    'VerifyTipView',

    # Profile views
    'ProfileView',
    'ProfileEditView',

    # Sport views
    'SportView',

    # Home views
    'HomeView',

    # Interaction views
    'FollowUserView',
    'MessagesView',
    'SendMessageView',
    'GetThreadMessagesView',
    'NotificationsView',
    'MessageSettingsView',
    'BookmarksView',
    'ToggleBookmarkView',
    'LikeCommentView',
    'ShareCommentView',
    'MarkNotificationReadView',
    'GetMessagesView',
    'StartMessageThreadView',
    'SearchUsersView',
    'UpdateMessageSettingsView',

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
    'BecomeTipsterView',
    'SetupTiersView',
    'TipsterDashboardView',
    'ManageTiersView',
    'SubscribeToTipsterView',
    'CancelSubscriptionView',
    'TopTipstersLeaderboardView',
    'StripeWebhookView',

    # API views
    'CurrentUserView',
    'UploadChatImageView',
    'SuggestedUsersView',
    'TrendingTipsView',
]
