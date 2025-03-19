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
    path('messages/', views.messages, name='messages'),
    path('notifications/', views.notifications, name='notifications'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('api/like-tip/', views.like_tip, name='like_tip'),
    path('api/share-tip/', views.share_tip, name='share_tip'),
    path('api/comment-tip/', views.comment_tip, name='comment_tip'),
    path('api/tip/<int:tip_id>/comments/', views.get_tip_comments, name='get_tip_comments'),
    path('api/like-comment/', views.like_comment, name='like_comment'),
    path('api/share-comment/', views.share_comment, name='share_comment'),
    path('api/reply-to-comment/', views.reply_to_comment, name='reply_to_comment'),
    path('login/', views.login_view, name='login'),  # Separate login view
    path('signup/', views.signup, name='signup'),    # Separate signup view
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),
    path('accessibility/', views.accessibility, name='accessibility'),
    path('api/horse-racing-fixtures/', views.horse_racing_fixtures, name='horse_racing_fixtures'),
    path('api/race-meetings/', views.RaceMeetingList.as_view(), name='race-meetings'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)