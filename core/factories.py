"""
Test Data Factories for Tipster Arena.

This module provides factory classes for generating test data using the factory_boy library.
These factories are used primarily for testing and development purposes to create realistic
test data for all models in the application.

The factories support:
1. User and Profile Management
   - UserFactory: Creates test users with unique usernames and emails
   - UserProfileFactory: Creates associated user profiles with realistic data

2. Core Features
   - TipFactory: Creates betting tips with realistic odds and confidence levels
   - NotificationFactory: Generates various types of user notifications

Each factory provides sensible defaults and uses Faker to generate realistic test data
where appropriate. The factories can be customized during instantiation to create
specific test scenarios.

Example usage:
    # Create a user with a profile
    user = UserFactory()
    profile = UserProfileFactory(user=user)

    # Create a tip
    tip = TipFactory(
        user=user,
        sport='football',
        text="Home team to win"
    )
"""

import factory
from django.contrib.auth.models import User
from core.models import (
    Tip, UserProfile, Notification
)
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

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

