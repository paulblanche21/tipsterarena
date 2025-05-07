"""
Unit tests for Tipster Arena rate limiting.
Tests throttling functionality and rate limits.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from core.throttles import (
    UserRateThrottle,
    TipRateThrottle,
    APIRateThrottle
)

User = get_user_model()

class ThrottlingTest(TestCase):
    """Test suite for rate limiting."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_throttle = UserRateThrottle()
        self.tip_throttle = TipRateThrottle()
        self.api_throttle = APIRateThrottle()

    def test_user_rate_limit(self):
        """Test user rate limiting."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Should allow first request
        self.assertTrue(self.user_throttle.allow_request(request))
        
        # Should allow requests within rate limit
        for _ in range(5):
            self.assertTrue(self.user_throttle.allow_request(request))
        
        # Should block after rate limit
        for _ in range(10):
            self.user_throttle.allow_request(request)
        self.assertFalse(self.user_throttle.allow_request(request))

    def test_tip_rate_limit(self):
        """Test tip creation rate limiting."""
        request = self.factory.post('/tips/create/')
        request.user = self.user
        
        # Should allow first tip
        self.assertTrue(self.tip_throttle.allow_request(request))
        
        # Should allow tips within rate limit
        for _ in range(3):
            self.assertTrue(self.tip_throttle.allow_request(request))
        
        # Should block after rate limit
        for _ in range(5):
            self.tip_throttle.allow_request(request)
        self.assertFalse(self.tip_throttle.allow_request(request))

    def test_api_rate_limit(self):
        """Test API rate limiting."""
        request = self.factory.get('/api/')
        request.user = self.user
        
        # Should allow first request
        self.assertTrue(self.api_throttle.allow_request(request))
        
        # Should allow requests within rate limit
        for _ in range(10):
            self.assertTrue(self.api_throttle.allow_request(request))
        
        # Should block after rate limit
        for _ in range(20):
            self.api_throttle.allow_request(request)
        self.assertFalse(self.api_throttle.allow_request(request))

    def test_rate_limit_reset(self):
        """Test rate limit reset after time period."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Exceed rate limit
        for _ in range(20):
            self.user_throttle.allow_request(request)
        self.assertFalse(self.user_throttle.allow_request(request))
        
        # Simulate time passing
        self.user_throttle.cache.set(
            self.user_throttle.get_cache_key(request),
            [],
            self.user_throttle.rate
        )
        
        # Should allow requests again
        self.assertTrue(self.user_throttle.allow_request(request))

    def test_different_users_rate_limits(self):
        """Test rate limits for different users."""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        request1 = self.factory.get('/')
        request1.user = self.user
        
        request2 = self.factory.get('/')
        request2.user = user2
        
        # Exceed rate limit for first user
        for _ in range(20):
            self.user_throttle.allow_request(request1)
        self.assertFalse(self.user_throttle.allow_request(request1))
        
        # Second user should still be allowed
        self.assertTrue(self.user_throttle.allow_request(request2)) 