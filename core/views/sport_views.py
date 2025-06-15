"""Views for handling sport-specific pages in Tipster Arena."""

from django.shortcuts import render
from django.views import View



class SportView(View):
    def get(self, request, sport):
        valid_sports = [
            'football', 'golf', 'tennis', 'horse_racing',
            'american_football', 'baseball', 'basketball', 'boxing', 'cricket',
            'cycling', 'darts', 'gaelic_games', 'greyhound_racing', 'motor_sport',
            'rugby_union', 'snooker', 'volleyball'
        ]
        if sport not in valid_sports:
            return render(request, 'core/404.html', status=404)

        tips = Tip.objects.filter(sport=sport).order_by('-created_at')[:20]
        return render(request, 'core/sport.html', {
            'tips': tips,
            'sport': sport,
        }) 