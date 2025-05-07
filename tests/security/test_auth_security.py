from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from core.models import UserProfile
import time

class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            date_of_birth='1990-01-01',
            location='Test Location'
        )

    def test_password_reset_flow(self):
        """Test the complete password reset flow"""
        # Request password reset
        response = self.client.post(reverse('password_reset'), {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to password_reset_done
        self.assertEqual(len(mail.outbox), 1)  # Check email was sent

        # Extract token from email
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Access password reset confirm page
        response = self.client.get(reverse('password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        }))
        self.assertEqual(response.status_code, 302)  # Redirect to password_reset_confirm

        # Submit new password
        response = self.client.post(reverse('password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        }), {
            'new_password1': 'newpass123!',
            'new_password2': 'newpass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to password_reset_complete

        # Verify new password works
        self.assertTrue(self.client.login(username='testuser', password='newpass123!'))

    def test_login_rate_limiting(self):
        """Test rate limiting for login attempts"""
        # Make multiple failed login attempts
        for _ in range(5):
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'wrongpass'
            })
            self.assertEqual(response.status_code, 200)

        # Next attempt should be rate limited
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 429)  # Too Many Requests
        self.assertContains(response, 'Too many login attempts')

    def test_session_security(self):
        """Test session security features"""
        # Login and get session ID
        self.client.login(username='testuser', password='testpass123')
        session_id = self.client.session.session_key

        # Test session timeout
        settings.SESSION_COOKIE_AGE = 1  # Set session age to 1 second
        time.sleep(2)  # Wait for session to expire

        # Try to access protected page
        response = self.client.get(reverse('profile', args=['testuser']))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        # Test session hijacking prevention
        self.client.login(username='testuser', password='testpass123')
        new_session_id = self.client.session.session_key
        self.assertNotEqual(session_id, new_session_id)  # Session ID should change

    def test_password_validation(self):
        """Test password strength validation"""
        # Test weak password
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': '123',
            'password2': '123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This password is too short')
        self.assertContains(response, 'This password is too common')

        # Test password mismatch
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The two password fields didn&#39;t match')

        # Test strong password
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect on success

    def test_csrf_protection(self):
        """Test CSRF protection"""
        # Try to submit form without CSRF token
        self.client = Client(enforce_csrf_checks=True)
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 403)  # Forbidden

        # Try to submit form with invalid CSRF token
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
            'csrfmiddlewaretoken': 'invalid_token'
        })
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_xss_protection(self):
        """Test XSS protection"""
        # Try to inject XSS in profile
        xss_payload = '<script>alert("XSS")</script>'
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('profile_edit', args=['testuser']), {
            'full_name': xss_payload,
            'description': xss_payload,
            'location': xss_payload
        })
        self.assertEqual(response.status_code, 200)
        
        # Check if XSS was escaped
        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertNotIn('<script>', updated_profile.full_name)
        self.assertNotIn('<script>', updated_profile.description) 