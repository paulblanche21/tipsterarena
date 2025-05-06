from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Tip, TipsterTier, TipsterSubscription
from django.utils import timezone
import random
from datetime import datetime, timedelta
import decimal

class Command(BaseCommand):
    help = 'Populate the database with test users, profiles, tips, and subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=25,
            help='Number of users to create'
        )
        parser.add_argument(
            '--pro-ratio',
            type=float,
            default=0.4,  # Increased pro ratio to ensure we have enough pro users
            help='Ratio of users that should be pro tipsters (0.0 to 1.0)'
        )

    def handle(self, *args, **kwargs):
        num_users = kwargs['users']
        pro_ratio = kwargs['pro_ratio']
        
        # Sport-specific tips with more variety and realism
        sport_tips = {
            'football': [
                {"text": "Manchester United to win and both teams to score", "odds": "2.50"},
                {"text": "Over 2.5 goals in Liverpool vs Chelsea", "odds": "1.95"},
                {"text": "Arsenal clean sheet against Newcastle", "odds": "2.75"},
                {"text": "Harry Kane to score first and Spurs to win", "odds": "4.50"},
                {"text": "Man City -1.5 Asian Handicap", "odds": "1.85"},
            ],
            'golf': [
                {"text": "Rory McIlroy to finish in top 5", "odds": "3.20"},
                {"text": "Jordan Spieth to win the tournament", "odds": "12.00"},
                {"text": "Dustin Johnson to lead after round 1", "odds": "8.50"},
                {"text": "Brooks Koepka top American player", "odds": "4.75"},
                {"text": "Tiger Woods to make the cut", "odds": "1.90"},
            ],
            'tennis': [
                {"text": "Djokovic to win in straight sets", "odds": "1.85"},
                {"text": "Nadal vs Federer over 3.5 sets", "odds": "2.10"},
                {"text": "Swiatek to win and under 20.5 games", "odds": "2.45"},
                {"text": "Medvedev +1.5 sets handicap", "odds": "1.75"},
                {"text": "Alcaraz to win the tournament", "odds": "3.50"},
            ],
            'horse_racing': [
                {"text": "Desert Crown (Each Way) in the 14:30 at Ascot", "odds": "8.00"},
                {"text": "Lucky Star to place in the Gold Cup", "odds": "3.25"},
                {"text": "Thunder Bolt / Speed King double", "odds": "5.50"},
                {"text": "Royal Flush to win by 2+ lengths", "odds": "4.25"},
                {"text": "Morning Glory (Each Way) in the opener", "odds": "11.00"},
            ],
        }

        bet_types = ['single', 'double', 'treble', 'accumulator', 'lucky15', 'yankee']
        statuses = ['pending', 'win', 'loss', 'void_non_runner']
        status_weights = [0.4, 0.3, 0.25, 0.05]  # Weights for each status

        # Create test users
        users = []
        for i in range(1, num_users + 1):
            username = f"tipster{i}"
            email = f"tipster{i}@example.com"
            password = "password123"
            is_pro = random.random() < pro_ratio

            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))

            # Create or update profile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'handle': f"@{username}",
                    'description': random.choice([
                        "Professional sports analyst sharing premium insights.",
                        "Expert tipster with proven track record.",
                        "Data-driven predictions and analysis.",
                        "Specializing in value bets and long-term profit.",
                        "Former bookmaker sharing insider knowledge.",
                    ]),
                    'location': random.choice(['London', 'Manchester', 'Liverpool', 'Dublin', 'Glasgow', 'Cardiff']),
                    'date_of_birth': (datetime.now() - timedelta(days=random.randint(365*25, 365*45))).date(),
                    'is_tipster': is_pro,
                    'kyc_completed': True,
                    'profile_completed': True,
                }
            )

            if is_pro:
                # Create subscription tiers
                tier_count = random.randint(2, 3)
                for t in range(tier_count):
                    price = decimal.Decimal(random.choice(['9.99', '19.99', '29.99', '49.99']))
                    name = random.choice(['Bronze', 'Silver', 'Gold', 'Platinum', 'VIP', 'Elite'])
                    max_subs = random.choice([None, 50, 100, 200])
                    
                    # Create tier without Stripe integration for now
                    tier, created = TipsterTier.objects.get_or_create(
                        tipster=user,
                        name=name,
                        defaults={
                            'price': price,
                            'description': f"Premium {name} tier with exclusive tips and insights",
                            'features': [
                                "All premium tips",
                                "Detailed analysis",
                                "Win probability ratings",
                                "Early access to tips",
                                "Monthly performance report",
                            ],
                            'max_subscribers': max_subs,
                            'is_popular': (t == 1),  # Make middle tier popular
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created {name} tier for {username}"))

            users.append(user)

        # Create tips for each user
        for user in users:
            # More tips for pro users
            num_tips = random.randint(15, 30) if user.userprofile.is_tipster else random.randint(5, 15)
            
            for _ in range(num_tips):
                sport = random.choice(list(sport_tips.keys()))
                tip_data = random.choice(sport_tips[sport])
                status = random.choices(statuses, weights=status_weights)[0]
                
                tip = Tip.objects.create(
                    user=user,
                    sport=sport,
                    text=tip_data['text'],
                    odds=tip_data['odds'],
                    odds_format='decimal',
                    bet_type=random.choice(bet_types),
                    each_way=random.choice(['yes', 'no']),
                    confidence=random.randint(1, 5),
                    status=status,
                    created_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                    visibility='public' if not user.userprofile.is_tipster else random.choice(['public', 'subscribers', 'tier'])
                )
                
                if status in ['win', 'loss']:
                    tip.verified_at = tip.created_at + timedelta(days=random.randint(1, 3))
                    tip.save()

            self.stdout.write(self.style.SUCCESS(f"Created {num_tips} tips for: {user.username}"))

        # Create subscriptions between users
        pro_users = [u for u in users if u.userprofile.is_tipster]
        regular_users = [u for u in users if not u.userprofile.is_tipster]

        if pro_users and regular_users:  # Only create subscriptions if we have both pro and regular users
            for regular_user in regular_users:
                # Subscribe to 1-3 pro tipsters
                num_subs = random.randint(1, min(3, len(pro_users)))
                selected_pros = random.sample(pro_users, num_subs)
                
                for pro_user in selected_pros:
                    # Get a random tier from the pro user
                    tiers = TipsterTier.objects.filter(tipster=pro_user)
                    if tiers.exists():  # Only create subscription if pro user has tiers
                        tier = random.choice(tiers)
                        
                        # Create subscription
                        start_date = timezone.now() - timedelta(days=random.randint(1, 90))
                        TipsterSubscription.objects.create(
                            subscriber=regular_user,
                            tier=tier,
                            status='active',
                            start_date=start_date,
                            end_date=start_date + timedelta(days=30),
                            auto_renew=True
                        )
                        
                        # Update tipster stats
                        pro_user.userprofile.total_subscribers += 1
                        pro_user.userprofile.subscription_revenue += tier.price
                        pro_user.userprofile.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Created subscription: {regular_user.username} -> {pro_user.username} ({tier.name})"
                            )
                        )

        self.stdout.write(self.style.SUCCESS("Successfully populated test data!"))