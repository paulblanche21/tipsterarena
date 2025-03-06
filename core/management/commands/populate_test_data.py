from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Tip  # Adjust 'yourapp' to your app name
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populate the database with test users, profiles, and tips'

    def handle(self, *args, **kwargs):
        # List of sports for tips
        sports = ['football', 'golf', 'tennis', 'horse_racing']
        
        # List of sample bios
        sample_bios = [
            "Passionate football tipster!",
            "Golf enthusiast sharing insights.",
            "Tennis lover with hot tips.",
            "Horse racing expert.",
            "Sports betting guru.",
            "I predict winners!",
            "Follow for daily tips!",
            "Avid sports fan.",
            "Sharing my best picks.",
            "Let’s win together!"
        ]
        
        # List of sample tips
        sample_tips = [
            "Salah to score a hat trick this weekend!",
            "Tiger Woods to win the Masters.",
            "Nadal to take the French Open.",
            "Bet on Thunderbolt in the next race!",
            "Chelsea to win 2-1 against Arsenal.",
            "Rory McIlroy to lead after Round 1.",
            "Serena Williams to win in straight sets.",
            "Dark Horse to place in the top 3.",
            "Man City to keep a clean sheet.",
            "Djokovic to win the next Grand Slam."
        ]

        # Create 25 test users
        for i in range(1, 26):  # Creates users tipster1 to tipster25
            username = f"tipster{i}"
            email = f"tipster{i}@example.com"
            password = "password123"  # Simple password for testing

            # Create or get user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'password': password,
                }
            )
            if created:
                user.set_password(password)  # Properly set password
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))

            # Create or get user profile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'description': random.choice(sample_bios),
                    'location': random.choice(['London', 'New York', 'Sydney', 'Tokyo', 'Paris']),
                    'date_of_birth': (datetime.now() - timedelta(days=random.randint(365*20, 365*40))).date(),  # Random DOB (20-40 years ago)
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created profile for: {username}"))

            # Create 1-5 tips for each user
            num_tips = random.randint(1, 5)
            for _ in range(num_tips):
                Tip.objects.get_or_create(
                    user=user,
                    sport=random.choice(sports),
                    text=random.choice(sample_tips),
                    created_at=(datetime.now() - timedelta(days=random.randint(1, 30))),  # Random creation date (past 30 days)
                )
            self.stdout.write(self.style.SUCCESS(f"Created {num_tips} tips for: {username}"))

        self.stdout.write(self.style.SUCCESS("Successfully populated test data!"))