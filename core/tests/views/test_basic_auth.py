from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile
from django.contrib.sites.models import Site
from allauth.account.models import EmailAddress
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

# Create UserProfile automatically when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            handle=f'@{instance.username}',
            full_name=instance.username,
            description='',
            location='',
            win_rate=0.0,
            total_tips=0,
            wins=0
        )

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

        # Create email address for the user (required by allauth)
        EmailAddress.objects.create(
            user=self.user,
            email=self.user_data['email'],
            primary=True,
            verified=True
        )

        # Create a site (required by allauth)
        self.site = Site.objects.get_current()

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
            'login': self.user_data['email'],  # allauth uses email for login
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful login
        
        # Verify user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_failed_login(self):
        """Test login with invalid credentials."""
        response = self.client.post(self.login_url, {
            'login': self.user_data['email'],
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Should stay on login page
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertContains(response, 'The email address and/or password you specified are not correct.')

    def test_logout(self):
        """Test user logout functionality."""
        # First login the user
        self.client.login(username=self.user_data['username'], password=self.user_data['password'])
        
        # Then logout with POST request (allauth requires POST for logout)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Should redirect after logout
        
        # Verify user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_required_fields_signup(self):
        """Test that required fields are enforced during signup."""
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
        # With enumeration prevention enabled, we should get a redirect
        # as if the signup was successful, but no new user should be created
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='differentuser').exists()) 