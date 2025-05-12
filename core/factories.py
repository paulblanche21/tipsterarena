"""
Test Data Factories for Tipster Arena.

This module provides factory classes for generating test data using the factory_boy library.
These factories are used primarily for testing and development purposes to create realistic
test data for all models in the application.

The factories support:
1. User and Profile Management
   - UserFactory: Creates test users with unique usernames and emails
   - UserProfileFactory: Creates associated user profiles with realistic data

2. Sports Events and Data
   - Football: Teams, Leagues, Events, and Team Stats
   - Tennis: Players, Tournaments, Leagues, Venues, and Events
   - Golf: Tours, Courses, and Events
   - Horse Racing: Courses, Meetings, Races, Horses, Jockeys, and Trainers

3. Core Features
   - TipFactory: Creates betting tips with realistic odds and confidence levels
   - NotificationFactory: Generates various types of user notifications

Each factory provides sensible defaults and uses Faker to generate realistic test data
where appropriate. The factories can be customized during instantiation to create
specific test scenarios.

Example usage:
    # Create a user with a profile
    user = UserFactory()
    profile = UserProfileFactory(user=user)

    # Create a football match with teams
    match = FootballEventFactory(
        home_team=FootballTeamFactory(name="Home FC"),
        away_team=FootballTeamFactory(name="Away FC")
    )

    # Create a tip for the match
    tip = TipFactory(
        user=user,
        sport='football',
        text="Home team to win"
    )
"""

import factory
from django.contrib.auth.models import User
from core.models import (
    Tip, UserProfile, GolfEvent, FootballEvent,
    TennisEvent, GolfTour, Notification, HorseRacingMeeting,
    HorseRacingCourse, HorseRacingRace, Horse, Jockey, Trainer,
    GolfCourse, FootballTeam, TennisTournament, TennisLeague,
    FootballLeague, TeamStats, TennisPlayer, TennisVenue
)
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

class FootballTeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FootballTeam

    name = factory.Sequence(lambda n: f'Team {n}')
    logo = factory.LazyAttribute(lambda obj: f'https://example.com/logos/{obj.name.lower().replace(" ", "_")}.png')
    record = "10-5-3"
    form = "WWDLL"

class TennisLeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TennisLeague

    league_id = factory.Sequence(lambda n: f'league_{n}')
    name = factory.Sequence(lambda n: f'League {n}')
    icon = '🎾'
    priority = factory.Sequence(lambda n: n)

class TennisTournamentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TennisTournament

    name = factory.Sequence(lambda n: f'Tournament {n}')
    tournament_id = factory.Sequence(lambda n: f'tournament_{n}')
    league = factory.SubFactory(TennisLeagueFactory)
    start_date = factory.Faker('date_this_year')
    end_date = factory.Faker('date_this_year')

class TipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tip

    user = factory.SubFactory(UserFactory)
    sport = 'football'
    text = factory.Faker('text')
    audience = 'public'
    status = 'pending'
    odds_format = 'decimal'
    odds = factory.Faker('pyfloat', positive=True, min_value=1.1, max_value=10.0)
    confidence = factory.Faker('random_int', min=1, max=5)
    created_at = factory.LazyFunction(timezone.now)
    scheduled_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))

class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    display_name = factory.Faker('name')
    bio = factory.Faker('text')
    avatar = None
    verified = False
    tipster_rating = factory.Faker('pyfloat', positive=True, min_value=1.0, max_value=5.0)
    total_tips = 0
    successful_tips = 0
    failed_tips = 0
    void_tips = 0
    pending_tips = 0
    followers_count = 0
    following_count = 0

class GolfTourFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GolfTour

    tour_id = factory.Sequence(lambda n: f'tour_{n}')
    name = factory.Sequence(lambda n: f'Golf Tour {n}')
    icon = "🏌️‍♂️"
    priority = factory.Sequence(lambda n: n)

class GolfCourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GolfCourse

    name = factory.Sequence(lambda n: f'Golf Course {n}')
    par = "72"
    yardage = "7,200"

class GolfEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GolfEvent

    event_id = factory.Sequence(lambda n: f'golf_event_{n}')
    tour = factory.SubFactory(GolfTourFactory)
    course = factory.SubFactory(GolfCourseFactory)
    name = factory.Sequence(lambda n: f'Golf Event {n}')
    short_name = factory.Sequence(lambda n: f'Event {n}')
    date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))
    state = 'pre'
    completed = False
    venue = factory.Faker('city')
    city = factory.Faker('city')
    state_location = factory.Faker('state')
    purse = factory.Faker('random_int', min=1000000, max=10000000)
    broadcast = "TV Network"
    current_round = 1
    total_rounds = 4
    is_playoff = False
    weather_condition = "Sunny"
    weather_temperature = "72°F"

class FootballLeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FootballLeague

    league_id = factory.Sequence(lambda n: f'league_{n}')
    name = factory.Sequence(lambda n: f'League {n}')
    icon = '⚽'
    priority = factory.Sequence(lambda n: n)

class TeamStatsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamStats

    possession = '50%'
    shots = '10'
    shots_on_target = '5'
    corners = '5'
    fouls = '10'

class FootballEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FootballEvent

    event_id = factory.Sequence(lambda n: f'football_event_{n}')
    name = factory.Sequence(lambda n: f'Match {n}')
    date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))
    state = 'pre'
    status_description = 'Scheduled'
    status_detail = 'N/A'
    league = factory.SubFactory(FootballLeagueFactory)
    venue = factory.Faker('city')
    home_team = factory.SubFactory(FootballTeamFactory)
    away_team = factory.SubFactory(FootballTeamFactory)
    home_score = '0'
    away_score = '0'
    home_stats = factory.SubFactory(TeamStatsFactory)
    away_stats = factory.SubFactory(TeamStatsFactory)
    clock = None
    period = 0
    broadcast = 'TV Network'

class TennisPlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TennisPlayer

    name = factory.Sequence(lambda n: f'Player {n}')
    short_name = factory.Sequence(lambda n: f'P{n}')
    world_ranking = factory.Sequence(lambda n: str(n))

class TennisVenueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TennisVenue

    name = factory.Sequence(lambda n: f'Venue {n}')
    court = factory.Sequence(lambda n: f'Court {n}')

class TennisEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TennisEvent

    event_id = factory.Sequence(lambda n: f'tennis_event_{n}')
    tournament = factory.SubFactory(TennisTournamentFactory)
    date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))
    state = 'pre'
    completed = False
    player1 = factory.SubFactory(TennisPlayerFactory)
    player2 = factory.SubFactory(TennisPlayerFactory)
    score = 'TBD'
    sets = []
    stats = {}
    clock = '0:00'
    period = 0
    round_name = 'First Round'
    venue = factory.SubFactory(TennisVenueFactory)
    match_type = 'Singles'
    player1_rank = 'N/A'
    player2_rank = 'N/A'

class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    type = factory.Iterator(['like', 'comment', 'follow'])
    content = factory.Faker('sentence')
    read = False
    related_tip = factory.SubFactory(TipFactory)
    related_comment = None
    related_user = None

class HorseRacingCourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HorseRacingCourse

    name = factory.Sequence(lambda n: f'Course {n}')
    location = factory.Faker('city')
    track_type = factory.Iterator(['Flat', 'National Hunt'])
    surface = factory.Iterator(['Turf', 'All Weather'])

class HorseRacingMeetingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HorseRacingMeeting

    date = factory.LazyFunction(lambda: timezone.now().date())
    course = factory.SubFactory(HorseRacingCourseFactory)
    url = factory.Sequence(lambda n: f'https://example.com/meeting/{n}')

class HorseRacingRaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HorseRacingRace

    meeting = factory.SubFactory(HorseRacingMeetingFactory)
    race_id = factory.Sequence(lambda n: n)
    off_time = factory.Sequence(lambda n: f"{(14 + n % 8):02d}:00")  # Races from 14:00 to 21:00
    name = factory.Sequence(lambda n: f'Race {n}')
    distance_round = "2m4½f"
    distance = "2m4f127y"
    distance_f = 20.5
    pattern = factory.Iterator(['Grade 1', 'Grade 2', 'Grade 3', 'Listed'])
    race_class = factory.Iterator(['Class 1', 'Class 2', 'Class 3', 'Class 4'])
    type = factory.Iterator(['Chase', 'Hurdle', 'Flat'])
    age_band = "5yo+"
    rating_band = "0-145"
    prize = "£39,865"
    field_size = factory.Faker('random_int', min=5, max=20)
    going = factory.Iterator(['Good', 'Good to Soft', 'Soft', 'Heavy'])
    rail_movements = None
    stalls = None
    weather = "Cloudy"
    surface = "Turf"

class HorseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Horse

    horse_id = factory.Sequence(lambda n: f'HORSE{n}')
    name = factory.Sequence(lambda n: f'Horse {n}')
    age = factory.Faker('random_int', min=2, max=12)
    sex = factory.Iterator(['gelding', 'mare', 'colt', 'filly'])
    sex_code = factory.Iterator(['G', 'M', 'C', 'F'])
    colour = factory.Iterator(['b', 'br', 'ch', 'gr'])
    region = factory.Iterator(['GB', 'IRE', 'FR', 'USA'])

class JockeyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Jockey

    jockey_id = factory.Sequence(lambda n: f'JOCKEY{n}')
    name = factory.Sequence(lambda n: f'Jockey {n}')

class TrainerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trainer

    trainer_id = factory.Sequence(lambda n: f'TRAINER{n}')
    name = factory.Sequence(lambda n: f'Trainer {n}')
    location = factory.Faker('city')

class GolfCourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GolfCourse

    name = factory.Sequence(lambda n: f'Golf Course {n}')
    par = "72"
    yardage = "7,200"

