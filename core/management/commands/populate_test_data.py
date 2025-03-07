from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Tip
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populate the database with test users, profiles, and tips'

    def handle(self, *args, **kwargs):
        # Sport-specific tips
        sport_tips = {
            'football': [
                "Salah to score a hat trick this weekend!",
                "Chelsea to win 2-1 against Arsenal.",
                "Man City to keep a clean sheet.",
                "Liverpool to win the Premier League.",
            ],
            'golf': [
                "Tiger Woods to win the Masters.",
                "Rory McIlroy to lead after Round 1.",
                "Jon Rahm to take the PGA Championship.",
            ],
            'tennis': [
                "Nadal to take the French Open.",
                "Serena Williams to win in straight sets.",
                "Djokovic to win the next Grand Slam.",
            ],
            'horse_racing': [
                "Bet on Thunderbolt in the next race!",
                "Dark Horse to place in the top 3.",
                "Golden Runner to win at Ascot.",
            ],
        }

        # Create 25 test users
        for i in range(1, 26):
            username = f"tipster{i}"
            email = f"tipster{i}@example.com"
            password = "password123"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))

            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'description': random.choice([
                        "Passionate football tipster!",
                        "Golf enthusiast sharing insights.",
                        "Tennis lover with hot tips.",
                        "Horse racing expert.",
                    ]),
                    'location': random.choice(['London', 'New York', 'Sydney', 'Tokyo', 'Paris']),
                    'date_of_birth': (datetime.now() - timedelta(days=random.randint(365*20, 365*40))).date(),
                }
            )

            # Create 1-5 tips, matching sport to text
            num_tips = random.randint(1, 5)
            for _ in range(num_tips):
                sport = random.choice(list(sport_tips.keys()))
                Tip.objects.get_or_create(
                    user=user,
                    sport=sport,
                    text=random.choice(sport_tips[sport]),
                    created_at=(datetime.now() - timedelta(days=random.randint(1, 30))),
                )
            self.stdout.write(self.style.SUCCESS(f"Created {num_tips} tips for: {username}"))

        self.stdout.write(self.style.SUCCESS("Successfully populated test data!"))