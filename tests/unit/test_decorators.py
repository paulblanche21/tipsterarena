"""
Unit tests for Tipster Arena decorators.
Tests custom decorators and permission decorators.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from core.decorators import (
    subscription_required,
    profile_required,
    kyc_required
)
from core.models import UserProfile

User = get_user_model()

class SubscriptionRequiredDecoratorTest(TestCase):
    """Test suite for subscription required decorator."""
    
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

    def test_subscription_required(self):
        """Test subscription required decorator."""
        @subscription_required
        def test_view(request):
            return HttpResponse('Success')

        # Test with active subscription
        self.profile.subscription_status = 'active'
        self.profile.save()
        
        request = self.factory.get('/')
        request.user = self.user
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)

        # Test without subscription
        self.profile.subscription_status = 'inactive'
        self.profile.save()
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to subscription page

class ProfileRequiredDecoratorTest(TestCase):
    """Test suite for profile required decorator."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_required(self):
        """Test profile required decorator."""
        @profile_required
        def test_view(request):
            return HttpResponse('Success')

        request = self.factory.get('/')
        request.user = self.user
        
        # Test without profile
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to profile creation

        # Test with profile
        UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

class KYCRequiredDecoratorTest(TestCase):
    """Test suite for KYC required decorator."""
    
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

    def test_kyc_required(self):
        """Test KYC required decorator."""
        @kyc_required
        def test_view(request):
            return HttpResponse('Success')

        request = self.factory.get('/')
        request.user = self.user
        
        # Test without KYC
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect to KYC page

        # Test with KYC
        self.profile.kyc_verified = True
        self.profile.save()
        response = test_view(request)
        self.assertEqual(response.status_code, 200) 