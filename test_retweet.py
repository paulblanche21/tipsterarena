#!/usr/bin/env python
"""
Test script to verify retweet functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/paulblanche/Desktop/Tipster Arena')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tipsterarena.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Tip, UserProfile

def test_retweet_functionality():
    """Test the retweet functionality"""
    print("Testing retweet functionality...")
    
    # Create test users if they don't exist
    user1, created = User.objects.get_or_create(
        username='testuser1',
        defaults={'email': 'test1@example.com'}
    )
    if created:
        user1.set_password('testpass123')
        user1.save()
        # Get or create user profile
        profile1, created = UserProfile.objects.get_or_create(
            user=user1,
            defaults={'handle': '@testuser1'}
        )
        if created:
            print(f"Created profile for: {user1.username}")
    
    user2, created = User.objects.get_or_create(
        username='testuser2',
        defaults={'email': 'test2@example.com'}
    )
    if created:
        user2.set_password('testpass123')
        user2.save()
        # Get or create user profile
        profile2, created = UserProfile.objects.get_or_create(
            user=user2,
            defaults={'handle': '@testuser2'}
        )
        if created:
            print(f"Created profile for: {user2.username}")
    
    # Create a test tip
    original_tip = Tip.objects.create(
        user=user1,
        sport='football',
        text='This is a test tip for retweet functionality',
        odds='2.5',
        odds_format='decimal',
        bet_type='single',
        each_way='no',
        confidence=3
    )
    print(f"Created original tip: {original_tip.id}")
    
    # Create a retweet
    retweet = Tip.objects.create(
        user=user2,
        sport=original_tip.sport,
        text=original_tip.text,
        odds=original_tip.odds,
        odds_format=original_tip.odds_format,
        bet_type=original_tip.bet_type,
        each_way=original_tip.each_way,
        confidence=original_tip.confidence,
        is_retweet=True,
        original_tip=original_tip
    )
    print(f"Created retweet: {retweet.id}")
    
    # Test the relationships
    print(f"\nOriginal tip retweets count: {original_tip.retweets.count()}")
    print(f"Retweet original tip: {retweet.original_tip.id}")
    print(f"Retweet is_retweet: {retweet.is_retweet}")
    
    # Test user tips query (like in profile view)
    user2_tips = Tip.objects.filter(
        user=user2
    ).order_by('-created_at')
    print(f"\nUser2 tips count: {user2_tips.count()}")
    for tip in user2_tips:
        if tip.is_retweet:
            print(f"  - Retweet of tip {tip.original_tip.id} by {tip.original_tip.user.username}")
        else:
            print(f"  - Original tip {tip.id}")
    
    # Test home feed query (like in home view)
    home_tips = Tip.objects.filter(
        is_retweet=False
    ).order_by('-created_at')[:10]
    print(f"\nHome feed tips count: {home_tips.count()}")
    
    # Clean up
    retweet.delete()
    original_tip.delete()
    print("\nTest completed successfully!")

if __name__ == '__main__':
    test_retweet_functionality() 