"""
Unit tests for Tipster Arena middleware.
Tests request/response processing and custom middleware functionality.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.middleware import (
    UserActivityMiddleware,
    SubscriptionMiddleware
)
from core.models import UserProfile

User = get_user_model()

class UserActivityMiddlewareTest(TestCase):
    """Test suite for user activity middleware."""
    
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
        self.middleware = UserActivityMiddleware(get_response=lambda r: r)

    def test_user_activity_tracking(self):
        """Test user activity tracking."""
        request = self.factory.get('/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.last_active)

class SubscriptionMiddlewareTest(TestCase):
    """Test suite for subscription middleware."""
    
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
        self.middleware = SubscriptionMiddleware(get_response=lambda r: r)

    def test_subscription_check(self):
        """Test subscription status check."""
        request = self.factory.get('/')
        request.user = self.user
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('subscription_status', request.session) 