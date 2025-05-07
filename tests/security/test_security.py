"""
Security tests for Tipster Arena.
Tests authentication, authorization, and protection against common attacks.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event
from django.core import mail
import json

User = get_user_model()

class SecurityTest(TestCase):
    """Test suite for security features."""
    
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
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

    def test_authentication(self):
        """Test authentication mechanisms."""
        # Test login with correct credentials
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Test login with incorrect password
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'wrongpass'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        
        # Test login with non-existent user
        response = self.client.post(
            reverse('login'),
            {
                'username': 'nonexistent',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_authorization(self):
        """Test authorization mechanisms."""
        # Test accessing protected view without login
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test accessing admin view without admin privileges
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test accessing admin view with admin privileges
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_xss_protection(self):
        """Test XSS protection."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test XSS in profile bio
        response = self.client.post(
            reverse('update_profile'),
            {
                'display_name': 'Test User',
                'bio': '<script>alert("XSS")</script>',
                'location': 'Test Location'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify XSS was prevented
        self.profile.refresh_from_db()
        self.assertNotIn('<script>', self.profile.bio)

    def test_csrf_protection(self):
        """Test CSRF protection."""
        # Test POST request without CSRF token
        response = self.client.post(
            reverse('update_profile'),
            {
                'display_name': 'Test User',
                'bio': 'Test bio',
                'location': 'Test Location'
            },
            HTTP_X_CSRFTOKEN='invalid_token'
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_sql_injection(self):
        """Test SQL injection protection."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test SQL injection in search
        response = self.client.get(
            reverse('search'),
            {'q': "' OR '1'='1"}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify no SQL injection occurred
        self.assertNotIn("' OR '1'='1", str(response.content))

    def test_rate_limiting(self):
        """Test rate limiting protection."""
        # Test login attempts
        for _ in range(5):
            response = self.client.post(
                reverse('login'),
                {
                    'username': 'testuser',
                    'password': 'wrongpass'
                }
            )
        
        # Should be blocked after too many attempts
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 429)  # Too Many Requests

    def test_password_security(self):
        """Test password security measures."""
        # Test password reset flow
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'test@example.com'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify reset email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password reset', mail.outbox[0].subject)
        
        # Test password complexity requirements
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'weak',
                'password2': 'weak'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)  # Password too weak

    def test_session_security(self):
        """Test session security."""
        # Test session timeout
        self.client.login(username='testuser', password='testpass123')
        
        # Simulate session timeout
        self.client.session.set_expiry(0)
        self.client.session.save()
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test session hijacking protection
        self.client.login(username='testuser', password='testpass123')
        session_id = self.client.session.session_key
        
        # Try to use session from different IP
        response = self.client.get(
            reverse('profile'),
            HTTP_X_FORWARDED_FOR='1.2.3.4'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login 