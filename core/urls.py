from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# URL patterns for the Tipster Arena core app
urlpatterns = [
    # General routes
    path('', views.landing, name='landing'),  # Root URL displays the landing page
    path('home/', views.home, name='home'),  # Main feed for authenticated users
    path('sport/<str:sport>/', views.sport_view, name='sport'),  # Sport-specific tip feed
    path('explore/', views.explore, name='explore'),  # Broad tip exploration page
    path('search/', views.search, name='search'),  # Search for users and tips

    # Profile routes
    path('profile/<str:username>/', views.profile, name='profile'),  # User profile page
    path('profile/<str:username>/edit/', views.profile_edit, name='profile_edit'),  # Profile editing page

    # Authentication routes
    path('login/', views.login_view, name='login'),  # Custom login page
    path('signup/', views.signup, name='signup'),  # Custom signup page
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),  # Logout with redirect to landing

    # Messaging routes
    path('messages/', views.messages_view, name='messages'),  # Main messages page
    path('messages/<int:thread_id>/', views.messages_view, name='message_thread'),  # Specific message thread
    path('messages/settings/', views.message_settings_view, name='message_settings'),  # Message settings panel

    # Social interaction routes
    path('notifications/', views.notifications, name='notifications'),  # User notifications page
    path('bookmarks/', views.bookmarks, name='bookmarks'),  # User bookmarked tips page

    # Policy routes
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),  # Terms of Service page
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),  # Privacy Policy page
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),  # Cookie Policy page
    path('accessibility/', views.accessibility, name='accessibility'),  # Accessibility page

    # API routes for user interactions
    path('api/suggested-users/', views.suggested_users_api, name='suggested_users_api'),  # Suggested users for following
    path('api/post-tip/', views.post_tip, name='api_post_tip'),  # Post a new tip
    path('api/follow/', views.follow_user, name='follow_user'),  # Follow a user
    path('api/like-tip/', views.like_tip, name='like_tip'),  # Like a tip
    path('api/share-tip/', views.share_tip, name='share_tip'),  # Share a tip
    path('api/comment-tip/', views.comment_tip, name='comment_tip'),  # Comment on a tip
    path('api/tip/<int:tip_id>/comments/', views.get_tip_comments, name='get_tip_comments'),  # Get comments for a tip
    path('api/like-comment/', views.like_comment, name='like_comment'),  # Like a comment
    path('api/share-comment/', views.share_comment, name='share_comment'),  # Share a comment
    path('toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),  # Toggle bookmark on a tip
    path('send-message/', views.send_message, name='send_message'),  # Send a message
    path('api/verify-tip/', views.VerifyTipView.as_view(), name='verify_tip'),

    # API routes for data retrieval
    path('horse-racing/cards/', views.horse_racing_fixtures, name='horse_racing_fixtures'),  # Updated path
    path('api/race-meetings/', views.RaceMeetingList.as_view(), name='race-meetings'), 
    path('api/trending-tips/', views.trending_tips_api, name='trending_tips_api'),  # Trending tips
    path('api/current-user/', views.current_user_api, name='current_user_api'),  # Current user info

    # CSP reporting route
    path('csp-report/', views.csp_report, name='csp_report'),  # Endpoint for CSP violation reports
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files when DEBUG is True


def debug_verify_tip(request):
    print("URL routing hit for /api/verify-tip/!")
    return views.VerifyTipView.as_view()(request)