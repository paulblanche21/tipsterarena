"""URL configuration for the Tipster Arena application."""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views.subscription_views import SetupTiersView

urlpatterns = [
    # Authentication routes
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('verify-email/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('kyc/', views.KYCView.as_view(), name='kyc'),
    path('profile-setup/', views.ProfileSetupView.as_view(), name='profile_setup'),
    path('skip-profile-setup/', views.SkipProfileSetupView.as_view(), name='skip_profile_setup'),
    path('payment/', views.PaymentView.as_view(), name='payment'),
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('skip-payment/', views.SkipPaymentView.as_view(), name='skip_payment'),

    # Subscription routes
    path('setup-tiers/', SetupTiersView.as_view(), name='setup_tiers'),
    path('become-tipster/', views.BecomeTipsterView.as_view(), name='become_tipster'),
    path('tipster-dashboard/', views.TipsterDashboardView.as_view(), name='tipster_dashboard'),
    path('manage-tiers/', views.ManageTiersView.as_view(), name='manage_tiers'),
    path('subscribe/<str:username>/<int:tier_id>/', views.SubscribeToTipsterView.as_view(), name='subscribe_to_tipster'),
    path('cancel-subscription/', views.CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('stripe-webhook/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
    path('top-tipsters/', views.TopTipstersLeaderboardView.as_view(), name='top_tipsters_leaderboard'),

    # Messaging routes
    path('messages/', views.MessagesView.as_view(), name='messages'),
    path('messages/<int:thread_id>/', views.GetThreadMessagesView.as_view(), name='thread_messages'),
    path('api/send-message/', views.SendMessageView.as_view(), name='send_message'),
    path('api/get-messages/', views.GetMessagesView.as_view(), name='get_messages'),
    path('api/start-thread/', views.StartMessageThreadView.as_view(), name='start_thread'),
    path('api/search-users/', views.SearchUsersView.as_view(), name='search_users'),
    path('api/update-message-settings/', views.UpdateMessageSettingsView.as_view(), name='update_message_settings'),
    path('api/mark-messages-read/', views.MarkMessagesReadView.as_view(), name='mark_messages_read'),
    path('message-settings/', views.MessageSettingsView.as_view(), name='message_settings'),

    # Notification routes
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('api/mark-notification-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),

    # Bookmark routes
    path('bookmarks/', views.BookmarksView.as_view(), name='bookmarks'),
    path('api/toggle-bookmark/', views.ToggleBookmarkView.as_view(), name='toggle_bookmark'),

    # Comment routes
    path('api/like-comment/', views.LikeCommentView.as_view(), name='like_comment'),
    path('api/share-comment/', views.ShareCommentView.as_view(), name='share_comment'),

    # API routes for user interactions
    path('api/suggested-users/', views.SuggestedUsersView.as_view(), name='suggested_users_api'),
    path('api/post-tip/', views.PostTipView.as_view(), name='post_tip'),
    path('api/edit-tip/', views.EditTipView.as_view(), name='edit_tip'),
    path('api/delete-tip/', views.DeleteTipView.as_view(), name='delete_tip'),
    path('api/follow/<str:username>/', views.FollowUserView.as_view(), name='follow_user'),
    path('api/like-tip/', views.LikeTipView.as_view(), name='like_tip'),
    path('api/share-tip/', views.ShareTipView.as_view(), name='share_tip'),
    path('api/comment-tip/', views.CommentTipView.as_view(), name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.GetTipCommentsView.as_view(), name='get_tip_comments'),
    path('api/tip-list/', views.TipListView.as_view(), name='tip_list'),
    path('api/verify-tip/<int:tip_id>/', views.VerifyTipView.as_view(), name='verify_tip'),

    # API routes for data retrieval
    path('api/trending-tips/', views.TrendingTipsView.as_view(), name='trending_tips_api'),
    path('api/current-user/', views.CurrentUserView.as_view(), name='current_user_api'),

    # Profile routes
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('profile/<str:username>/edit/', views.ProfileEditView.as_view(), name='profile_edit'),

    # Sport routes
    path('sport/<str:sport>/', views.SportView.as_view(), name='sport'),

    # Home route
    path('home/', views.HomeView.as_view(), name='home'),

    # General routes
    path('', views.LandingView.as_view(), name='landing'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('csp-report/', views.CSPReportView.as_view(), name='csp_report'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('cookies/', views.CookiePolicyView.as_view(), name='cookie_policy'),
    path('accessibility/', views.AccessibilityView.as_view(), name='accessibility'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('api/upload-chat-image/', views.UploadChatImageView.as_view(), name='upload_chat_image_api'),
]


