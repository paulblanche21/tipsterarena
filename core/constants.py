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

Usage:
    These constants are used throughout the application for:
    - League/tour selection in forms and filters
    - Display of league/tour information in templates
    - API integrations with sports data providers
    - Sorting and organizing sports events

Example:
    from core.constants import SPORTS

    # Get Football configuration
    football = next(
        sport for sport in SPORTS 
        if sport['sport_id'] == 'football'
    )
    print(f"{football['icon']} {football['name']}")
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