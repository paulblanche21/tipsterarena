"""Views for Tipster Arena."""

__all__ = [
    # Auth views
    'login_view', 'signup_view', 'kyc_view', 'profile_setup_view',
    'skip_profile_setup', 'payment_view', 'create_checkout_session',
    'payment_success', 'skip_payment',

    # Tip views
    'post_tip', 'edit_tip', 'delete_tip', 'like_tip',
    'share_tip', 'comment_tip', 'get_tip_comments', 'tip_detail',
    'tip_list',

    # Profile views
    'profile', 'profile_edit_view',

    # Sport views
    'sport_view', 'explore', 'home',

    # Interaction views
    'follow_user', 'messages_view', 'send_message',
    'get_thread_messages', 'notifications', 'message_settings_view',
    'bookmarks', 'like_comment', 'share_comment', 'toggle_bookmark',

    # API views
    'current_user_api', 'suggested_users_api',
    'trending_tips_api', 'VerifyTipView',
    'BurstRateThrottle', 'SustainedRateThrottle',

    # Horse racing views
    'validate_date_param', 'horse_racing_fixtures',
    'racecards_json_view', 'horse_racing_events',
    'HorseRacingMeetingDetail', 'HorseRacingBettingOddsBulkUpsert',
    'RaceMeetingList', 'HorseRacingRacesList', 'HorseRacingRaceDetail',

    # Tennis views
    'validate_state_param', 'TennisEventsList',
    'TennisEventDetail', 'tennis_event_stats',
    'get_head_to_head_stats', 'get_player_form',
    'get_tournament_history',

    # Football views
    'FootballEventsList', 'FootballEventDetail',
    'FetchFootballEventsView',

    # Golf views
    'GolfEventsList', 'GolfEventDetail',
    'FetchGolfEventsView',

    # General views
    'landing', 'search', 'csp_report',
    'terms_of_service', 'privacy_policy',
    'cookie_policy', 'accessibility'
]

from .auth_views import (
    login_view, signup_view, kyc_view, profile_setup_view,
    skip_profile_setup, payment_view, create_checkout_session,
    payment_success, skip_payment
)

from .tip_views import (
    post_tip, edit_tip, delete_tip, like_tip,
    share_tip, comment_tip, get_tip_comments, tip_detail,
    tip_list
)

from .profile_views import (
    profile, profile_edit_view
)

from .sport_views import (
    sport_view, explore, home
)

from .interaction_views import (
    follow_user, messages_view, send_message,
    get_thread_messages, notifications, message_settings_view,
    bookmarks, like_comment, share_comment, toggle_bookmark
)

from .api_views import (
    current_user_api, suggested_users_api,
    trending_tips_api, VerifyTipView,
    BurstRateThrottle, SustainedRateThrottle
)

from .horse_racing_views import (
    validate_date_param, horse_racing_fixtures,
    racecards_json_view, horse_racing_events,
    HorseRacingMeetingDetail, HorseRacingBettingOddsBulkUpsert,
    RaceMeetingList, HorseRacingRacesList, HorseRacingRaceDetail
)

from .tennis_views import (
    validate_state_param, TennisEventsList,
    TennisEventDetail, tennis_event_stats,
    get_head_to_head_stats, get_player_form,
    get_tournament_history
)

from .football_views import (
    FootballEventsList, FootballEventDetail,
    FetchFootballEventsView
)

from .golf_views import (
    GolfEventsList, GolfEventDetail,
    golf_player_stats, golf_tournament_history,
    FetchGolfEventsView
)

from .general_views import (
    landing, search, csp_report,
    terms_of_service, privacy_policy,
    cookie_policy, accessibility
) 