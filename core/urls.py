"""URL configuration for the core app of Tipster Arena."""

# core/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

# URL patterns for the Tipster Arena core app
urlpatterns = [
    # General routes
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('sport/<str:sport>/', views.sport_view, name='sport'),
    path('search/', views.search, name='search'),

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
    path('api/fetch-football-events/',
         views.FetchFootballEventsView.as_view(),
         name='fetch_football_events'),
    path('api/golf-events/fetch/', views.FetchGolfEventsView.as_view(), name='fetch_golf_events'),
    path('api/golf-events/', views.GolfEventsList.as_view(), name='golf-events-list'),
    path('api/golf-events/<str:event_id>/', views.GolfEventDetail.as_view(), name='golf-event-detail'),
    path('api/tennis-events/', views.TennisEventsList.as_view(), name='tennis-events-list'),
    path('api/tennis-events/<str:event_id>/', views.TennisEventDetail.as_view(), name='tennis-event-detail'),
    path('api/tennis-events/<str:event_id>/stats/',
         views.tennis_event_stats,
         name='tennis-event-stats'),
    path('api/horse-racing-events/', views.horse_racing_events, name='horse-racing-events'),
    path('api/tips/', views.tip_list, name='tip_list'),
    path('api/tips/<int:tip_id>/', views.tip_detail, name='tip_detail'),
    path('api/tips/<int:tip_id>/like/', views.like_tip, name='like_tip'),
    path('api/tips/<int:tip_id>/comments/', views.get_tip_comments, name='tip_comments'),

    # Authentication endpoints
    path('api/auth/login/', views.login_view, name='login'),
    path('api/auth/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User profile endpoints
    path('api/users/profile/', views.profile, name='user_profile'),
    path('api/users/kyc/', views.kyc_view, name='kyc'),
    path('api/users/notifications/', views.notifications, name='user_notifications'),

    # Sports events endpoints
    path('api/events/golf/', views.GolfEventsList.as_view(), name='golf_events'),
    path('api/events/golf/<str:event_id>/', views.GolfEventDetail.as_view(), name='golf_event_detail'),
    path('api/events/football/', views.FootballEventsList.as_view(), name='football_events'),
    path('api/events/football/<str:event_id>/', views.FootballEventDetail.as_view(), name='football_event_detail'),
    path('api/events/tennis/', views.TennisEventsList.as_view(), name='tennis_events'),
    path('api/events/tennis/<str:event_id>/', views.TennisEventDetail.as_view(), name='tennis_event_detail'),
    path('api/events/horse-racing/', views.horse_racing_events, name='horse_racing_events'),
    path('api/events/horse-racing/<str:meeting_id>/', views.HorseRacingMeetingDetail.as_view(), name='horse_racing_meeting_detail'),
    path('api/events/horse-racing/<str:meeting_id>/races/', views.HorseRacingRacesList.as_view(), name='horse_racing_races'),
    path('api/events/horse-racing/<str:meeting_id>/races/<str:race_id>/', views.HorseRacingRaceDetail.as_view(), name='horse_racing_race_detail'),
    
     # Tips endpoints
    path('api/tips/', views.tip_list, name='tip_list'),
    path('api/tips/<int:tip_id>/', views.tip_detail, name='tip_detail'),
    path('api/tips/<int:tip_id>/like/', views.like_tip, name='like_tip'),
    
     # Horse Racing endpoints
    path('api/horse-racing/betting-odds/bulk-upsert/',
         views.HorseRacingBettingOddsBulkUpsert.as_view(),
         name='horse_racing_betting_odds_bulk_upsert'),


   

    path('tipster/', include([
    path('become/', views.become_tipster, name='become_tipster'),
    path('dashboard/', views.tipster_dashboard, name='tipster_dashboard'),
    path('tiers/', views.manage_tiers, name='manage_tiers'),
    path('subscribe/<str:username>/<int:tier_id>/', views.subscribe_to_tipster, name='subscribe_to_tipster'),
    path('cancel/<int:subscription_id>/', views.cancel_subscription, name='cancel_subscription'),
]))

]


