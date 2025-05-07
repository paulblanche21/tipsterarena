"""
Functional tests for Tipster Arena user journeys.
Tests complete user workflows from registration to tip placement.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event
from decimal import Decimal


User = get_user_model()

class UserJourneyTest(TestCase):
    """Test suite for complete user journeys."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User',
            bio='Test bio',
            location='Test Location'
        )
        self.event = Event.objects.create(
            name='Test Event',
            start_time='2024-01-01T12:00:00Z',
            status='upcoming'
        )

    def test_complete_user_journey(self):
        """Test complete user journey from registration to tip placement."""
        # 1. Register new user
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        
        # 2. Login
        response = self.client.post(reverse('login'), {
            'username': 'newuser',
            'password': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
        # 3. Complete KYC
        response = self.client.post(reverse('kyc'), {
            'document_type': 'passport',
            'document_number': '123456789'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after KYC
        
        # 4. Set up profile
        response = self.client.post(reverse('profile_setup'), {
            'display_name': 'New User',
            'bio': 'New bio',
            'location': 'New Location'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after profile setup
        
        # 5. Place a tip
        response = self.client.post(reverse('place_tip'), {
            'event': self.event.id,
            'prediction': 'Test prediction',
            'odds': '2.0',
            'stake': '10.0',
            'reasoning': 'Test reasoning'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after tip placement
        
        # 6. Verify tip was created
        tip = Tip.objects.filter(user__username='newuser').first()
        self.assertIsNotNone(tip)
        self.assertEqual(tip.prediction, 'Test prediction')
        self.assertEqual(tip.odds, Decimal('2.0'))

    def test_tip_verification_journey(self):
        """Test tip verification journey."""
        # 1. Login
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Place a tip
        response = self.client.post(reverse('place_tip'), {
            'event': self.event.id,
            'prediction': 'Test prediction',
            'odds': '2.0',
            'stake': '10.0',
            'reasoning': 'Test reasoning'
        })
        self.assertEqual(response.status_code, 302)
        
        # 3. Verify tip
        tip = Tip.objects.filter(user=self.user).first()
        response = self.client.post(reverse('verify_tip', args=[tip.id]), {
            'verification': 'win'
        })
        self.assertEqual(response.status_code, 302)
        
        # 4. Check tip status
        tip.refresh_from_db()
        self.assertEqual(tip.status, 'win')

    def test_payment_journey(self):
        """Test payment setup journey."""
        # 1. Login
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Set up payment
        response = self.client.post(reverse('payment_setup'), {
            'plan': 'monthly',
            'payment_method': 'card'
        })
        self.assertEqual(response.status_code, 302)
        
        # 3. Verify payment status
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.payment_completed) 