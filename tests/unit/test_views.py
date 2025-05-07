"""
Unit tests for Tipster Arena views.
Tests view functionality, permissions, and responses.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event

User = get_user_model()

class TipViewsTest(TestCase):
    """Test suite for tip-related views."""
    
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
        self.event = Event.objects.create(
            name='Test Event',
            start_time='2024-01-01 12:00:00',
            status='upcoming'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_tip(self):
        """Test tip creation view."""
        response = self.client.post(
            reverse('create_tip'),
            {
                'event': self.event.id,
                'prediction': 'Test prediction',
                'odds': '2.0',
                'stake': '10.0',
                'reasoning': 'Test reasoning'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Tip.objects.filter(user=self.user).exists())

    def test_tip_list(self):
        """Test tip list view."""
        # Create some tips
        for i in range(3):
            Tip.objects.create(
                user=self.user,
                event=self.event,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0'
            )
        
        response = self.client.get(reverse('tip_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tips']), 3)

class ProfileViewsTest(TestCase):
    """Test suite for profile-related views."""
    
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
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view(self):
        """Test profile view."""
        response = self.client.get(
            reverse('profile', kwargs={'username': 'testuser'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.profile)

    def test_profile_edit(self):
        """Test profile edit view."""
        response = self.client.post(
            reverse('edit_profile'),
            {
                'display_name': 'Updated Name',
                'bio': 'Updated bio'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, 'Updated Name')

class AuthViewsTest(TestCase):
    """Test suite for authentication views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_login(self):
        """Test login view."""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success

    def test_register(self):
        """Test registration view."""
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
        self.assertTrue(User.objects.filter(username='newuser').exists())

class APIViewsTest(TestCase):
    """Test suite for API views."""
    
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
        self.client.login(username='testuser', password='testpass123')

    def test_tip_verification(self):
        """Test tip verification API."""
        tip = Tip.objects.create(
            user=self.user,
            prediction='Test prediction',
            odds='2.0',
            stake='10.0'
        )
        
        response = self.client.post(
            reverse('verify_tip', kwargs={'tip_id': tip.id}),
            {'status': 'win'}
        )
        self.assertEqual(response.status_code, 200)
        tip.refresh_from_db()
        self.assertEqual(tip.status, 'win')

    def test_user_stats(self):
        """Test user stats API."""
        response = self.client.get(
            reverse('user_stats', kwargs={'username': 'testuser'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('win_rate', response.json())
        self.assertIn('total_tips', response.json()) 