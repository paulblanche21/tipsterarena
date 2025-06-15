"""URL configuration for the core app of Tipster Arena."""

# core/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views.home_views import HomeView
from .views.profile_views import ProfileView, ProfileEditView
from .views.general_views import (
    LandingView,
    SearchView,
    TermsOfServiceView,
    PrivacyPolicyView,
    CookiePolicyView,
    AccessibilityView,
    ChatView,
)
from .views.subscription_views import (
    BecomeTipsterView,
    SetupTiersView,
    TipsterDashboardView,
    ManageTiersView,
    SubscribeToTipsterView,
    CancelSubscriptionView,
    TopTipstersLeaderboardView,
    StripeWebhookView,
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
)


# URL patterns for the Tipster Arena core app
urlpatterns = [
    # General routes
    path('', LandingView.as_view(), name='landing'),
    path('home/', HomeView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path('sport/<str:sport>/', views.SportView.as_view(), name='sport'),

    # Profile routes
    path('profile/<str:username>/',
        ProfileView.as_view(),
        name='profile'),
    path('profile/<str:username>/edit/',
        ProfileEditView.as_view(),
        name='profile_edit'),

    # Authentication routes
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('kyc/', views.KYCView.as_view(), name='kyc'),
    path('profile-setup/', views.ProfileSetupView.as_view(), name='profile_setup'),
    path('skip-profile-setup/', views.SkipProfileSetupView.as_view(), name='skip_profile_setup'),
    path('payment/', views.PaymentView.as_view(), name='payment'),
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('skip-payment/', views.SkipPaymentView.as_view(), name='skip_payment'),

    # Messaging routes
    path('messages/', MessagesView.as_view(), name='messages'),
    path('messages/<int:thread_id>/', MessagesView.as_view(), name='message_thread'),
    path('messages/settings/', MessageSettingsView.as_view(), name='message_settings'),

    # Social interaction routes
    path('notifications/', NotificationsView.as_view(), name='notifications'),
    path('bookmarks/', BookmarksView.as_view(), name='bookmarks'),

    # Policy routes
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('cookie-policy/', CookiePolicyView.as_view(), name='cookie_policy'),
    path('accessibility/', AccessibilityView.as_view(), name='accessibility'),

    # API routes for user interactions
    path('api/suggested-users/', views.SuggestedUsersView.as_view(), name='suggested_users_api'),
    path('api/post-tip/', views.PostTipView.as_view(), name='post_tip'),
    path('api/edit-tip/', views.EditTipView.as_view(), name='edit_tip'),
    path('api/delete-tip/', views.DeleteTipView.as_view(), name='delete_tip'),
    path('api/follow/<str:username>/', FollowUserView.as_view(), name='follow_user'),
    path('api/like-tip/', views.LikeTipView.as_view(), name='like_tip'),
    path('api/share-tip/', views.ShareTipView.as_view(), name='share_tip'),
    path('api/comment-tip/', views.CommentTipView.as_view(), name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.GetTipCommentsView.as_view(), name='get_tip_comments'),
    path('api/tip-list/', views.TipListView.as_view(), name='tip_list'),
    path('api/verify-tip/<int:tip_id>/', views.VerifyTipView.as_view(), name='verify_tip'),
    path('api/toggle-bookmark/', ToggleBookmarkView.as_view(), name='toggle_bookmark'),

    # API routes for data retrieval
    path('api/trending-tips/', views.TrendingTipsView.as_view(), name='trending_tips_api'),
    path('api/current-user/', views.CurrentUserView.as_view(), name='current_user_api'),
    
    # Message API routes
    path('api/messages/', GetMessagesView.as_view(), name='api_messages'),
    path('api/messages/send/<int:thread_id>/', SendMessageView.as_view(), name='api_send_message'),
    path('api/messages/thread/<int:thread_id>/', GetThreadMessagesView.as_view(), name='api_thread_messages'),
    path('api/messages/start/', StartMessageThreadView.as_view(), name='api_start_message_thread'),
    path('api/messages/settings/', UpdateMessageSettingsView.as_view(), name='api_message_settings'),
    path('api/users/search/', SearchUsersView.as_view(), name='api_search_users'),

    # Tipster routes
    path('tipster/', include([
        path('become/', BecomeTipsterView.as_view(), name='become_tipster'),
        path('setup-tiers/', SetupTiersView.as_view(), name='setup_tiers'),
        path('dashboard/', TipsterDashboardView.as_view(), name='tipster_dashboard'),
        path('tiers/', ManageTiersView.as_view(), name='manage_tiers'),
        path('subscribe/<str:username>/<int:tier_id>/', SubscribeToTipsterView.as_view(), name='subscribe_to_tipster'),
        path('cancel/<int:subscription_id>/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
        path('webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    ])),
    path('top-tipsters/', TopTipstersLeaderboardView.as_view(), name='top_tipsters_leaderboard'),
    path('api/mark-notification-read/', MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('api/upload-chat-image/', views.UploadChatImageView.as_view(), name='upload_chat_image_api'),
]


