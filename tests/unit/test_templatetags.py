"""
Unit tests for Tipster Arena template tags and filters.
Tests custom template tags and filters functionality.
"""
from django.test import TestCase
from django.template import Template, Context
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip


User = get_user_model()

class TemplateTagsTest(TestCase):
    """Test suite for template tags and filters."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )

    def test_format_odds_tag(self):
        """Test format_odds template tag."""
        template = Template(
            '{% load tipster_tags %}'
            '{{ odds|format_odds }}'
        )
        
        # Test decimal odds
        context = Context({'odds': '2.5'})
        self.assertEqual(template.render(context), '2.50')
        
        # Test fractional odds
        context = Context({'odds': '5/2'})
        self.assertEqual(template.render(context), '5/2')

    def test_calculate_win_rate_tag(self):
        """Test calculate_win_rate template tag."""
        template = Template(
            '{% load tipster_tags %}'
            '{{ profile|calculate_win_rate }}'
        )
        
        # Create some tips
        for i in range(10):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 5 else 'loss'
            )
        
        context = Context({'profile': self.profile})
        self.assertEqual(template.render(context), '50.0')

    def test_format_datetime_tag(self):
        """Test format_datetime template tag."""
        template = Template(
            '{% load tipster_tags %}'
            '{{ date|format_datetime }}'
        )
        
        from datetime import datetime
        from django.utils import timezone
        
        test_date = timezone.make_aware(
            datetime(2024, 1, 1, 12, 0)
        )
        context = Context({'date': test_date})
        
        rendered = template.render(context)
        self.assertIn('2024', rendered)
        self.assertIn('12:00', rendered)

    def test_user_badges_tag(self):
        """Test user_badges template tag."""
        template = Template(
            '{% load tipster_tags %}'
            '{% user_badges profile %}'
        )
        
        # Add some badges
        self.profile.badges = ['win_streak_5', 'tip_count_50']
        self.profile.save()
        
        context = Context({'profile': self.profile})
        rendered = template.render(context)
        
        self.assertIn('win_streak_5', rendered)
        self.assertIn('tip_count_50', rendered)

    def test_tip_status_tag(self):
        """Test tip_status template tag."""
        template = Template(
            '{% load tipster_tags %}'
            '{{ tip|tip_status }}'
        )
        
        tip = Tip.objects.create(
            user=self.user,
            prediction='Test prediction',
            odds='2.0',
            stake='10.0',
            status='win'
        )
        
        context = Context({'tip': tip})
        self.assertEqual(template.render(context), 'Win')

    def test_complex_template(self):
        """Test multiple template tags together."""
        template = Template(
            '{% load tipster_tags %}'
            '{{ tip.prediction }} - {{ tip.odds|format_odds }}'
            ' ({{ tip|tip_status }})'
        )
        
        tip = Tip.objects.create(
            user=self.user,
            prediction='Test prediction',
            odds='2.5',
            stake='10.0',
            status='win'
        )
        
        context = Context({'tip': tip})
        rendered = template.render(context)
        
        self.assertIn('Test prediction', rendered)
        self.assertIn('2.50', rendered)
        self.assertIn('Win', rendered) 