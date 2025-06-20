"""Views for Tipster Arena.

This module is a placeholder that imports all views from their respective modules.
The actual view implementations can be found in the views/ directory.
"""

from .views.auth_views import (
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
    ProfileView,
    ProfileEditView
)

from .views.sport_views import (
    SportView,
)

from .views.home_views import (
    HomeView,
)

from .views.general_views import (
    LandingView,
    SearchView,
    CSPReportView,
    TermsOfServiceView,
    PrivacyPolicyView,
    CookiePolicyView,
    AccessibilityView,
    ChatView
)

from .views.interaction_views import (
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
    MarkMessagesReadView
)

from .views.subscription_views import (
    BecomeTipsterView,
    SetupTiersView,
    TipsterDashboardView,
    ManageTiersView,
    SubscribeToTipsterView,
    CancelSubscriptionView,
    StripeWebhookView,
    TopTipstersLeaderboardView
)

from .views.api_views import (
    CurrentUserView,
    UploadChatImageView,
    SuggestedUsersView,
    TrendingTipsView,
    VerifyTipView,
    BurstRateThrottle,
    SustainedRateThrottle
)