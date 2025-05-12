"""
Constants for the Tipster Arena Application.

This module defines all the constant values used throughout the Tipster Arena application.
These constants are primarily used for sports league configurations and other static data
that needs to be consistent across the application.

Available Constants:
1. FOOTBALL_LEAGUES
   - Configuration for major football leagues
   - Each league entry contains:
     * league_id: Unique identifier (e.g., 'eng.1' for Premier League)
     * name: Display name of the league
     * icon: Flag emoji representing the league's country
     * priority: Display order (1 being highest priority)
   - Currently includes: Premier League, La Liga, Serie A, Bundesliga, Ligue 1

2. GOLF_TOURS
   - Configuration for professional golf tours
   - Each tour entry contains:
     * tour_id: Unique identifier (e.g., 'pga' for PGA Tour)
     * name: Display name of the tour
     * icon: Emoji representing the sport
     * priority: Display order
   - Currently includes: PGA Tour, LPGA Tour, European Tour

3. TENNIS_LEAGUES
   - Configuration for professional tennis tours
   - Each league entry contains:
     * league_id: Unique identifier (e.g., 'atp' for ATP Tour)
     * name: Display name of the league
     * icon: Emoji representing the sport
     * priority: Display order
   - Currently includes: ATP Tour, WTA Tour

Usage:
    These constants are used throughout the application for:
    - League/tour selection in forms and filters
    - Display of league/tour information in templates
    - API integrations with sports data providers
    - Sorting and organizing sports events

Example:
    from core.constants import FOOTBALL_LEAGUES

    # Get Premier League configuration
    premier_league = next(
        league for league in FOOTBALL_LEAGUES 
        if league['league_id'] == 'eng.1'
    )
    print(f"{premier_league['icon']} {premier_league['name']}")
"""

FOOTBALL_LEAGUES = [
    {
        'league_id': 'eng.1',  # Premier League
        'name': 'Premier League',
        'icon': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        'priority': 1
    },
    {
        'league_id': 'esp.1',  # La Liga
        'name': 'La Liga',
        'icon': '🇪🇸',
        'priority': 2
    },
    {
        'league_id': 'ita.1',  # Serie A
        'name': 'Serie A',
        'icon': '🇮🇹',
        'priority': 3
    },
    {
        'league_id': 'ger.1',  # Bundesliga
        'name': 'Bundesliga',
        'icon': '🇩🇪',
        'priority': 4
    },
    {
        'league_id': 'fra.1',  # Ligue 1
        'name': 'Ligue 1',
        'icon': '🇫🇷',
        'priority': 5
    }
]

GOLF_TOURS = [
    {
        'tour_id': 'pga',
        'name': 'PGA Tour',
        'icon': '🏌️‍♂️',
        'priority': 1
    },
    {
        'tour_id': 'lpga',
        'name': 'LPGA Tour',
        'icon': '🏌️‍♀️',
        'priority': 2
    },
    {
        'tour_id': 'euro',
        'name': 'European Tour',
        'icon': '🇪🇺',
        'priority': 3
    }
]

TENNIS_LEAGUES = [
    {
        'league_id': 'atp',
        'name': 'ATP Tour',
        'icon': '🎾',
        'priority': 1
    },
    {
        'league_id': 'wta',
        'name': 'WTA Tour',
        'icon': '🎾',
        'priority': 2
    }
] 