"""
Constants for the Tipster Arena Application.

This module defines all the constant values used throughout the Tipster Arena application.
These constants are primarily used for configuration and other static data
that needs to be consistent across the application.

Available Constants:
1. SPORTS
   - Configuration for all supported sports
   - Each sport entry contains:
     * sport_id: Unique identifier (e.g., 'football' for Football)
     * name: Display name of the sport
     * icon: Emoji representing the sport
     * priority: Display order (1 being highest priority)

2. VIEW_CONSTANTS
   - Pagination limits for different views
   - Rate limiting settings
   - Cache timeouts
   - File upload limits
   - API response limits

3. SUBSCRIPTION_CONSTANTS
   - Tier configurations
   - Trial period settings
   - Subscription limits

4. API_CONSTANTS
   - API rate limits
   - Response formats
   - Error codes

Usage:
    These constants are used throughout the application for:
    - League/tour selection in forms and filters
    - Display of league/tour information in templates
    - API integrations with sports data providers
    - Sorting and organizing sports events
    - View configurations and limits
    - API and subscription settings

Example:
    from core.constants import SPORTS, VIEW_CONSTANTS

    # Get Football configuration
    football = next(
        sport for sport in SPORTS 
        if sport['sport_id'] == 'football'
    )
    print(f"{football['icon']} {football['name']}")

    # Use view constants
    tips_per_page = VIEW_CONSTANTS['TIPS_PER_PAGE']
"""

SPORTS = [
    {
        'sport_id': 'football',
        'name': 'Football',
        'icon': '⚽',
        'priority': 1
    },
    {
        'sport_id': 'golf',
        'name': 'Golf',
        'icon': '🏌️‍♂️',
        'priority': 2
    },
    {
        'sport_id': 'tennis',
        'name': 'Tennis',
        'icon': '🎾',
        'priority': 3
    },
    {
        'sport_id': 'horse_racing',
        'name': 'Horse Racing',
        'icon': '🐎',
        'priority': 4
    },
    {
        'sport_id': 'american_football',
        'name': 'American Football',
        'icon': '🏈',
        'priority': 5
    },
    {
        'sport_id': 'baseball',
        'name': 'Baseball',
        'icon': '⚾',
        'priority': 6
    },
    {
        'sport_id': 'basketball',
        'name': 'Basketball',
        'icon': '🏀',
        'priority': 7
    },
    {
        'sport_id': 'boxing',
        'name': 'Boxing',
        'icon': '🥊',
        'priority': 8
    },
    {
        'sport_id': 'cricket',
        'name': 'Cricket',
        'icon': '🏏',
        'priority': 9
    },
    {
        'sport_id': 'cycling',
        'name': 'Cycling',
        'icon': '🚴',
        'priority': 10
    },
    {
        'sport_id': 'darts',
        'name': 'Darts',
        'icon': '🎯',
        'priority': 11
    },
    {
        'sport_id': 'gaelic_games',
        'name': 'Gaelic Games',
        'icon': '🏐',
        'priority': 12
    },
    {
        'sport_id': 'greyhound_racing',
        'name': 'Greyhound Racing',
        'icon': '🐕',
        'priority': 13
    },
    {
        'sport_id': 'motor_sport',
        'name': 'Motor Sport',
        'icon': '🏎️',
        'priority': 14
    },
    {
        'sport_id': 'rugby_union',
        'name': 'Rugby Union',
        'icon': '🏉',
        'priority': 15
    },
    {
        'sport_id': 'snooker',
        'name': 'Snooker',
        'icon': '🎱',
        'priority': 16
    },
    {
        'sport_id': 'volleyball',
        'name': 'Volleyball',
        'icon': '🏐',
        'priority': 17
    }
]

# View-specific constants
VIEW_CONSTANTS = {
    # Pagination
    'TIPS_PER_PAGE': 20,
    'COMMENTS_PER_PAGE': 50,
    'USERS_PER_PAGE': 10,
    'MESSAGES_PER_PAGE': 30,
    'NOTIFICATIONS_PER_PAGE': 20,
    'TRENDING_TIPS_LIMIT': 10,
    'SUGGESTED_USERS_LIMIT': 5,

    # Rate Limiting
    'LOGIN_ATTEMPTS_LIMIT': 5,
    'LOGIN_ATTEMPTS_TIMEOUT': 300,  # 5 minutes
    'API_RATE_LIMIT': '100/day',
    'API_BURST_LIMIT': '5/minute',

    # Cache Timeouts
    'TRENDING_TIPS_CACHE': 300,  # 5 minutes
    'USER_PROFILE_CACHE': 600,   # 10 minutes
    'SPORT_LIST_CACHE': 3600,    # 1 hour

    # File Upload
    'MAX_IMAGE_SIZE': 5 * 1024 * 1024,  # 5MB
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/gif'],
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_FILE_TYPES': ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],

    # Message Settings
    'MAX_MESSAGE_LENGTH': 1000,
    'MAX_THREAD_PARTICIPANTS': 10,
    'MESSAGE_RETENTION_DAYS': 30,

    # Search
    'MIN_SEARCH_LENGTH': 2,
    'MAX_SEARCH_RESULTS': 20,
}

# Subscription-related constants
SUBSCRIPTION_CONSTANTS = {
    'TRIAL_PERIOD_DAYS': 30,
    'MAX_TIERS_PER_TIPSTER': 3,
    'MIN_TIER_PRICE': 5.00,
    'MAX_TIER_PRICE': 100.00,
    'MAX_SUBSCRIBERS_PER_TIER': 1000,
    'SUBSCRIPTION_GRACE_PERIOD_DAYS': 3,
    'CANCELLATION_NOTICE_DAYS': 7,
}

# API-specific constants
API_CONSTANTS = {
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    'DEFAULT_CACHE_TIMEOUT': 300,  # 5 minutes
    'MAX_RESPONSE_ITEMS': 1000,
    'ERROR_CODES': {
        'INVALID_REQUEST': 400,
        'UNAUTHORIZED': 401,
        'FORBIDDEN': 403,
        'NOT_FOUND': 404,
        'RATE_LIMITED': 429,
        'SERVER_ERROR': 500,
    },
    'SUCCESS_CODES': {
        'OK': 200,
        'CREATED': 201,
        'NO_CONTENT': 204,
    }
} 