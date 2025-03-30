from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing, name='landing'),  # Root URL
    path('api/suggested-users/', views.suggested_users_api, name='suggested_users_api'),
    path('api/post-tip/', views.post_tip, name='api_post_tip'),  # New endpoint
    path('api/follow/', views.follow_user, name='follow_user'),
    path('home/', views.home, name='home'),
    path('sport/<str:sport>/', views.sport_view, name='sport'),
    path('explore/', views.explore, name='explore'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/edit/', views.profile_edit, name='profile_edit'),
    path('messages/', views.messages_view, name='messages'),
    path('send-message/', views.send_message, name='send_message'), 
    path('messages/<int:thread_id>/', views.messages_view, name='message_thread'),
    path('messages/settings/', views.message_settings_view, name='message_settings'),
    path('notifications/', views.notifications, name='notifications'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('api/like-tip/', views.like_tip, name='like_tip'),
    path('api/share-tip/', views.share_tip, name='share_tip'),
    path('api/comment-tip/', views.comment_tip, name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.get_tip_comments, name='get_tip_comments'),
    path('api/like-comment/', views.like_comment, name='like_comment'),
    path('api/share-comment/', views.share_comment, name='share_comment'),
    path('login/', views.login_view, name='login'),  # Separate login view
    path('signup/', views.signup, name='signup'),    # Separate signup view
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('accessibility/', views.accessibility, name='accessibility'),
    path('api/horse-racing-fixtures/', views.horse_racing_fixtures, name='horse_racing_fixtures'),
    path('api/race-meetings/', views.RaceMeetingList.as_view(), name='race-meetings'),
    path('api/trending-tips/', views.trending_tips_api, name='trending_tips_api'),
    path('api/current-user/', views.current_user_api, name='current_user_api'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('csp-report/', views.csp_report, name='csp_report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)