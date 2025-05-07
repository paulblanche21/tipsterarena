"""
Security tests for Tipster Arena.
Tests authentication, authorization, and protection against common attacks.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile



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
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.full_name = 'Test User'
        self.profile.save()
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
        self.assertEqual(response.status_code, 302)  # Redirect to home
        
        # Test login with incorrect password
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'wrongpass'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect back to login
        
        # Test login with non-existent user
        response = self.client.post(
            reverse('login'),
            {
                'username': 'nonexistent',
                'password': 'testpass123'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect back to login

    def test_authorization(self):
        """Test authorization mechanisms."""
        # Test accessing protected view without login
        response = self.client.get(reverse('profile', kwargs={'username': 'testuser'}))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test accessing admin view without admin privileges
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test accessing admin view with admin privileges
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_xss_protection(self):
        """Test XSS protection."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test XSS in profile edit
        response = self.client.post(
            reverse('profile_edit', kwargs={'username': 'testuser'}),
            {
                'full_name': '<script>alert("XSS")</script>',
                'description': '<script>alert("XSS")</script>',
                'location': '<script>alert("XSS")</script>'
            }
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify XSS was prevented
        self.profile.refresh_from_db()
        self.assertNotIn('<script>', self.profile.full_name)
        self.assertNotIn('<script>', self.profile.description)
        self.assertNotIn('<script>', self.profile.location)

    def test_csrf_protection(self):
        """Test CSRF protection."""
        self.client = Client(enforce_csrf_checks=True)
        self.client.login(username='testuser', password='testpass123')
        
        # Test POST request without CSRF token
        response = self.client.post(
            reverse('profile_edit', kwargs={'username': 'testuser'}),
            {
                'full_name': 'Test User',
                'description': 'Test bio',
                'location': 'Test Location'
            }
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_rate_limiting(self):
        """Test rate limiting protection."""
        # Test login rate limiting
        for _ in range(10):
            response = self.client.post(
                reverse('login'),
                {
                    'username': 'testuser',
                    'password': 'wrongpass'
                }
            )
        
        # Next attempt should be rate limited
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'wrongpass'
            }
        )
        self.assertEqual(response.status_code, 200)  # Show login form with error

    def test_session_security(self):
        """Test session security."""
        # Test session timeout
        self.client.login(username='testuser', password='testpass123')
        session_id = self.client.session.session_key
        
        # Try to use session from different IP
        response = self.client.get(
            reverse('profile', kwargs={'username': 'testuser'}),
            HTTP_X_FORWARDED_FOR='1.2.3.4'
        )
        self.assertEqual(response.status_code, 200)  # Allow access from different IP
        
        # Verify session was not invalidated
        self.assertEqual(self.client.session.session_key, session_id)

    def test_sql_injection(self):
        """Test SQL injection protection."""
        # Test SQL injection in username
        response = self.client.post(
            reverse('login'),
            {
                'username': "' OR '1'='1",
                'password': "' OR '1'='1"
            }
        )
        self.assertEqual(response.status_code, 200)  # Show login form with error

    def test_password_security(self):
        """Test password security measures."""
        # Test password complexity requirements
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'password1': 'weak',
                'password2': 'weak',
                'handle': '@newuser'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This password is too short')  # Password too weak 