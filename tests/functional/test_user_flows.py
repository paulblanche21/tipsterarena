"""
Functional tests for Tipster Arena user flows.
Tests end-to-end user interactions and workflows.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event


User = get_user_model()

class UserFlowTest(TestCase):
    """Test suite for user flows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )

    def test_registration_flow(self):
        """Test user registration flow."""
        # Test registration form
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'testpass123',
                'password2': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify user was created
        self.assertTrue(
            User.objects.filter(username='newuser').exists()
        )
        
        # Verify profile was created
        new_user = User.objects.get(username='newuser')
        self.assertTrue(
            UserProfile.objects.filter(user=new_user).exists()
        )

    def test_login_flow(self):
        """Test user login flow."""
        # Test login
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify user is logged in
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_tip_creation_flow(self):
        """Test tip creation flow."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Create an event
        event = Event.objects.create(
            name='Test Event',
            start_time='2024-01-01 12:00:00',
            status='upcoming'
        )
        
        # Create a tip
        response = self.client.post(
            reverse('create_tip'),
            {
                'event': event.id,
                'prediction': 'Test prediction',
                'odds': '2.0',
                'stake': '10.0',
                'confidence': 3
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify tip was created
        self.assertTrue(
            Tip.objects.filter(
                user=self.user,
                prediction='Test prediction'
            ).exists()
        )

    def test_event_management_flow(self):
        """Test event management flow."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Create an event
        response = self.client.post(
            reverse('create_event'),
            {
                'name': 'Test Event',
                'start_time': '2024-01-01 12:00:00',
                'venue': 'Test Venue',
                'race_type': 'flat',
                'distance': '1200m',
                'surface': 'turf'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify event was created
        self.assertTrue(
            Event.objects.filter(name='Test Event').exists()
        )
        
        # Update event
        event = Event.objects.get(name='Test Event')
        response = self.client.post(
            reverse('update_event', args=[event.id]),
            {
                'name': 'Updated Event',
                'start_time': '2024-01-01 12:00:00',
                'venue': 'Test Venue',
                'race_type': 'flat',
                'distance': '1200m',
                'surface': 'turf'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify event was updated
        event.refresh_from_db()
        self.assertEqual(event.name, 'Updated Event')

    def test_payment_flow(self):
        """Test payment processing flow."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Initiate payment
        response = self.client.post(
            reverse('process_payment'),
            {
                'amount': '10.00',
                'currency': 'USD',
                'payment_method': 'card'
            }
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify payment was processed
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Verify subscription was updated
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_subscribed)

    def test_profile_management_flow(self):
        """Test profile management flow."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Update profile
        response = self.client.post(
            reverse('update_profile'),
            {
                'display_name': 'Updated Name',
                'bio': 'Updated bio',
                'location': 'Updated location'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify profile was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, 'Updated Name')
        self.assertEqual(self.profile.bio, 'Updated bio')
        self.assertEqual(self.profile.location, 'Updated location') 