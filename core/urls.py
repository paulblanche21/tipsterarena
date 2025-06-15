"""URL configuration for the core app of Tipster Arena."""

# core/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views.home_views import HomeView
from .views.profile_views import ProfileView, ProfileEditView


# URL patterns for the Tipster Arena core app
urlpatterns = [
    # General routes
    path('', views.landing, name='landing'),
    path('home/', HomeView.as_view(), name='home'),
    path('search/', views.search, name='search'),
    path('sport/<str:sport>/', views.SportView.as_view(), name='sport'),

    # Profile routes
    path('profile/<str:username>/',
        ProfileView.as_view(),
        name='profile'),
    path('profile/<str:username>/edit/',
        ProfileEditView.as_view(),
        name='profile_edit'),

    # Authentication routes
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('signup/', views.signup_view, name='signup'),
    path('kyc/', views.kyc_view, name='kyc'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('profile-setup/skip/', views.skip_profile_setup, name='skip_profile_setup'),
    path('payment/', views.payment_view, name='payment'),
    path('payment/create-checkout-session/',
         views.create_checkout_session,
         name='create_checkout_session'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/skip/', views.skip_payment, name='skip_payment'),

    # Messaging routes
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:thread_id>/', views.messages_view, name='message_thread'),
    path('messages/settings/', views.message_settings_view, name='message_settings'),

    # Social interaction routes
    path('notifications/', views.notifications, name='notifications'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),

    # Policy routes
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('accessibility/', views.accessibility, name='accessibility'),

    # API routes for user interactions
    path('api/suggested-users/', views.suggested_users_api, name='suggested_users_api'),
    path('api/post-tip/', views.PostTipView.as_view(), name='post_tip'),
    path('api/edit-tip/', views.EditTipView.as_view(), name='edit_tip'),
    path('api/delete-tip/', views.DeleteTipView.as_view(), name='delete_tip'),
    path('api/follow/<str:username>/', views.FollowUserView.as_view(), name='follow_user'),
    path('api/like-tip/', views.LikeTipView.as_view(), name='like_tip'),
    # path('api/share-tip/', views.ShareTipView.as_view(), name='share_tip'),
    path('api/comment-tip/', views.comment_tip, name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.get_tip_comments, name='get_tip_comments'),
    path('api/like-comment/', views.like_comment, name='like_comment'),
    path('api/share-comment/', views.share_comment, name='share_comment'),
    path('api/tip/<int:tip_id>/', views.TipDetailView.as_view(), name='tip-detail'),
    path('api/toggle-bookmark/', views.ToggleBookmarkView.as_view(), name='toggle_bookmark'),
    path('api/verify-tip/<int:tip_id>/', views.VerifyTipView.as_view(), name='verify_tip'),

    # API routes for data retrieval
    path('api/trending-tips/', views.trending_tips_api, name='trending_tips_api'),
    path('api/current-user/', views.current_user_api, name='current_user_api'),
    
    # Message API routes
    path('api/messages/', views.get_messages, name='api_messages'),
    path('api/messages/send/<int:thread_id>/', views.send_message, name='api_send_message'),
    path('api/messages/thread/<int:thread_id>/', views.get_thread_messages, name='api_thread_messages'),
    path('api/messages/start/', views.start_message_thread, name='api_start_message_thread'),
    path('api/messages/settings/', views.update_message_settings, name='api_message_settings'),
    path('api/users/search/', views.search_users, name='api_search_users'),

    path('tipster/', include([
        path('tier-setup/', views.tier_setup, name='tier_setup'),
        path('setup-tiers/', views.setup_tiers, name='setup_tiers'),
        path('dashboard/', views.tipster_dashboard, name='tipster_dashboard'),
        path('tiers/', views.manage_tiers, name='manage_tiers'),
        path('subscribe/<str:username>/<int:tier_id>/', views.subscribe_to_tipster, name='subscribe_to_tipster'),
        path('cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
        path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    ])),
    path('top-tipsters/', views.top_tipsters_leaderboard, name='top_tipsters_leaderboard'),
    path('api/mark-notification-read/', views.mark_notification_read, name='mark_notification_read'),
    path('chat/', views.chat_view, name='chat'),
    path('api/upload-chat-image/', views.upload_chat_image_api, name='upload_chat_image_api'),
]


