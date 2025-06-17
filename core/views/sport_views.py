"""Views for handling sport-specific pages in Tipster Arena."""

from django.shortcuts import render
from django.views import View
from core.models import Tip

class SportView(View):
    def get(self, request, sport):
        valid_sports = [
            'football', 'golf', 'tennis', 'horse_racing',
            'american_football', 'baseball', 'basketball', 'boxing', 'cricket',
            'cycling', 'darts', 'gaelic_games', 'greyhound_racing', 'motor_sport',
            'rugby_union', 'snooker', 'volleyball'
        ]
        
        # Check if sport is None, empty, or not in valid_sports
        if not sport or sport.lower() == 'none' or sport not in valid_sports:
            return render(request, 'core/404.html', status=404)

        tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]
        return render(request, 'core/sport.html', {
            'tips': tips,
            'sport': sport,
        }) 