from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile
from decimal import Decimal

User = get_user_model()

class BasicAuthenticationTests(TestCase):
    """Test suite for basic authentication functionality."""
    
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('account_signup')
        self.login_url = reverse('account_login')
        self.logout_url = reverse('account_logout')
        
        # Create a test user
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.user.set_password(self.user_data['password'])
        self.user.save()
        
        # Create user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User',
            bio='Test bio',
            location='Test Location',
            win_rate=Decimal('0.0'),
            total_tips=0,
            total_wins=0,
            total_losses=0,
            total_voids=0
        )

    def test_signup_page_access(self):
        """Test that the signup page is accessible."""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')

    def test_successful_signup(self):
        """Test successful user registration."""
        signup_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        response = self.client.post(self.signup_url, signup_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful signup
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(new_user, 'userprofile'))

    def test_login_page_access(self):
        """Test that the login page is accessible."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')

    def test_successful_login(self):
        """Test successful user login."""
        response = self.client.post(self.login_url, {
            'login': self.user_data['username'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful login
        
        # Verify user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_failed_login(self):
        """Test login with invalid credentials."""
        response = self.client.post(self.login_url, {
            'login': self.user_data['username'],
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on login page
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'Invalid username or password')

    def test_logout(self):
        """Test user logout functionality."""
        # First login the user
        self.client.login(username=self.user_data['username'], password=self.user_data['password'])
        
        # Then logout
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Should redirect after logout
        
        # Verify user is logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_required_fields_signup(self):
        """Test that required fields are enforced during signup."""
        # Test missing username
        response = self.client.post(self.signup_url, {
            'email': 'test@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

        # Test missing email
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

        # Test missing password
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')

    def test_duplicate_username(self):
        """Test that duplicate usernames are not allowed."""
        response = self.client.post(self.signup_url, {
            'username': self.user_data['username'],  # Using existing username
            'email': 'different@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists')

    def test_duplicate_email(self):
        """Test that duplicate email addresses are not allowed."""
        response = self.client.post(self.signup_url, {
            'username': 'differentuser',
            'email': self.user_data['email'],  # Using existing email
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user is already registered with this email address') 