"""
Unit tests for Tipster Arena context processors.
Tests template context additions.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.context_processors import (
    user_profile_processor,
    site_settings_processor,
    notification_processor
)
from core.models import UserProfile

User = get_user_model()

class ContextProcessorTest(TestCase):
    """Test suite for context processors."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )

    def test_user_profile_processor(self):
        """Test user profile context processor."""
        request = self.factory.get('/')
        request.user = self.user
        
        context = user_profile_processor(request)
        
        self.assertIn('user_profile', context)
        self.assertEqual(context['user_profile'], self.profile)

    def test_site_settings_processor(self):
        """Test site settings context processor."""
        request = self.factory.get('/')
        
        context = site_settings_processor(request)
        
        self.assertIn('site_name', context)
        self.assertIn('site_description', context)
        self.assertIn('contact_email', context)

    def test_notification_processor(self):
        """Test notification context processor."""
        request = self.factory.get('/')
        request.user = self.user
        
        context = notification_processor(request)
        
        self.assertIn('notifications', context)
        self.assertIsInstance(context['notifications'], list)

    def test_anonymous_user_context(self):
        """Test context processors with anonymous user."""
        request = self.factory.get('/')
        request.user = None
        
        # Test user profile processor
        context = user_profile_processor(request)
        self.assertNotIn('user_profile', context)
        
        # Test notification processor
        context = notification_processor(request)
        self.assertNotIn('notifications', context)
        
        # Site settings should still work
        context = site_settings_processor(request)
        self.assertIn('site_name', context)

    def test_context_processor_chain(self):
        """Test multiple context processors together."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Get context from all processors
        context = {}
        context.update(user_profile_processor(request))
        context.update(site_settings_processor(request))
        context.update(notification_processor(request))
        
        # Check all expected keys are present
        self.assertIn('user_profile', context)
        self.assertIn('site_name', context)
        self.assertIn('notifications', context)
        
        # Check values are correct
        self.assertEqual(context['user_profile'], self.profile)
        self.assertIsInstance(context['notifications'], list) 