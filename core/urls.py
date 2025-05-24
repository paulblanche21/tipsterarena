"""URL configuration for the core app of Tipster Arena."""

# core/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import subscription_views
from .views.interaction_views import mark_notification_read
from .views.general_views import chat_view
from .views.api_views import upload_chat_image_api
from .views.trending_views import trending_tips

# URL patterns for the Tipster Arena core app
urlpatterns = [
    # General routes
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('sport/<str:sport>/', views.sport_view, name='sport'),

    # Profile routes
    path('profile/<str:username>/',
        views.profile,
        name='profile'),
    path('profile/<str:username>/edit/',
        views.profile_edit_view,
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
    path('messages/send/<int:thread_id>/', views.send_message, name='send_message'),
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
    path('api/post-tip/', views.post_tip, name='api_post_tip'),
    path('api/edit-tip/', views.edit_tip, name='edit_tip'),
    path('api/delete-tip/', views.delete_tip, name='delete_tip'),
    path('api/follow/', views.follow_user, name='follow_user'),
    path('api/like-tip/', views.like_tip, name='like_tip'),
    path('api/share-tip/', views.share_tip, name='share_tip'),
    path('api/comment-tip/', views.comment_tip, name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.get_tip_comments, name='get_tip_comments'),
    path('api/like-comment/', views.like_comment, name='like_comment'),
    path('api/share-comment/', views.share_comment, name='share_comment'),
    path('api/tip/<int:tip_id>/', views.tip_detail, name='tip-detail'),
    path('api/toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('api/verify-tip/<int:tip_id>/', views.VerifyTipView.as_view(), name='verify_tip'),

    # API routes for data retrieval
    path('api/trending-tips/', trending_tips, name='trending_tips_api'),
    path('api/current-user/', views.current_user_api, name='current_user_api'),
    path('csp-report/', views.csp_report, name='csp_report'),

    # Authentication endpoints
    path('api/auth/login/', views.login_view, name='login'),
    path('api/auth/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User profile endpoints
    path('api/users/profile/', views.profile, name='user_profile'),
    path('api/users/kyc/', views.kyc_view, name='kyc'),
    path('api/users/notifications/', views.notifications, name='user_notifications'),
    
    # Tips endpoints
    path('api/tips/', views.tip_list, name='tip_list'),
    path('api/tips/<int:tip_id>/', views.tip_detail, name='tip_detail'),
    path('api/tips/<int:tip_id>/like/', views.like_tip, name='like_tip'),

    path('tipster/', include([
        path('tier-setup/', subscription_views.tier_setup, name='tier_setup'),
        path('dashboard/', subscription_views.tipster_dashboard, name='tipster_dashboard'),
        path('tiers/', subscription_views.manage_tiers, name='manage_tiers'),
        path('subscribe/<str:username>/<int:tier_id>/', subscription_views.subscribe_to_tipster, name='subscribe_to_tipster'),
        path('cancel/<int:subscription_id>/', subscription_views.cancel_subscription, name='cancel_subscription'),
        path('webhook/', subscription_views.stripe_webhook, name='stripe_webhook'),
    ])),
    path('top-tipsters/', subscription_views.top_tipsters_leaderboard, name='top_tipsters_leaderboard'),
    path('api/mark-notification-read/', mark_notification_read, name='mark_notification_read'),
    path('chat/', chat_view, name='chat'),
    path('api/upload-chat-image/', upload_chat_image_api, name='upload_chat_image_api'),
]


