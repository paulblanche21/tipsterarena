"""Constants for the Tipster Arena application.

This module contains all the constants used throughout the application,
including sports league configurations and other static data.
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