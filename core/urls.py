# core/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views
from core.views import FetchGolfEventsView, GolfEventsList


# URL patterns for the Tipster Arena core app
urlpatterns = [
    # General routes
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('sport/<str:sport>/', views.sport_view, name='sport'),
    path('explore/', views.explore, name='explore'),
    path('search/', views.search, name='search'),

    # Profile routes
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/edit/', views.profile_edit, name='profile_edit'),

    # Authentication routes
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('signup/', views.signup_view, name='signup'),
    path('kyc/', views.kyc_view, name='kyc'),
     path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('profile-setup/skip/', views.skip_profile_setup, name='skip_profile_setup'),

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
    path('api/post-tip/', views.post_tip, name='api_post_tip'),
    path('api/follow/', views.follow_user, name='follow_user'),
    path('api/like-tip/', views.like_tip, name='like_tip'),
    path('api/share-tip/', views.share_tip, name='share_tip'),
    path('api/comment-tip/', views.comment_tip, name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.get_tip_comments, name='get_tip_comments'),
    path('api/like-comment/', views.like_comment, name='like_comment'),
    path('api/share-comment/', views.share_comment, name='share_comment'),
    path('api/tip/<int:tip_id>/', views.tip_detail, name='tip_detail'),
    path('toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('send-message/', views.send_message, name='send_message'),
    path('api/verify-tip/', views.VerifyTipView.as_view(), name='verify_tip'),

    # API routes for data retrieval
    path('horse-racing/cards/', views.horse_racing_fixtures, name='horse_racing_fixtures'),
    path('api/race-meetings/', views.RaceMeetingList.as_view(), name='race-meetings'),
    path('api/trending-tips/', views.trending_tips_api, name='trending_tips_api'),
    path('api/current-user/', views.current_user_api, name='current_user_api'),
    path('horse-racing/cards-json/', views.racecards_json_view, name='racecards_json'),
    path('csp-report/', views.csp_report, name='csp_report'),
    path('api/fetch-football-events/', views.FetchFootballEventsView.as_view(), name='fetch_football_events'),
    path('api/football-events/', views.FootballEventsList.as_view(), name='football_events'),
    path('api/golf/events/fetch/', FetchGolfEventsView.as_view(), name='fetch_golf_events'),
    path('api/golf/events/', GolfEventsList.as_view(), name='golf_events_list'),
    path('api/tennis-events/', views.tennis_events, name='tennis_events'),
    path('api/tennis-events/<str:event_id>/stats/', views.tennis_event_stats, name='tennis_event_stats'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)