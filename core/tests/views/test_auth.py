from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from core.models import UserProfile
from core.factories import UserFactory
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from unittest.mock import patch

User = get_user_model()

class AuthenticationTest(TestCase):
    """Test suite for authentication-related views and functionality."""
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.kyc_url = reverse('kyc')
        self.profile_setup_url = reverse('profile_setup')
        self.payment_url = reverse('payment')  
        self.user = UserFactory()
        self.user.set_password('testpass123')
        self.user.save()
        
        # Create and assign user groups
        tipster_group, _ = Group.objects.get_or_create(name='Tipsters')
        self.user.groups.add(tipster_group)
        
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
        
        # Log in the user
        self.client.login(username=self.user.username, password='testpass123')

    def test_signup_view(self):
        """Test the signup view and form"""
        # Test GET request
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/signup.html')      
        # Test successful signup
        signup_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
            'handle': '@testuser'
        }
        response = self.client.post(self.signup_url, signup_data)
        self.assertRedirects(response, reverse('kyc')) 
        # Verify user and profile were created
        user = User.objects.get(username='testuser')
        self.assertTrue(hasattr(user, 'userprofile'))
        self.assertEqual(user.userprofile.handle, '@testuser')
        
        # Test duplicate username
        response = self.client.post(self.signup_url, signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists')
        
        # Test password mismatch
        signup_data['username'] = 'testuser2'
        signup_data['password2'] = 'differentpass123'
        response = self.client.post(self.signup_url, signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn\u2019t match")

    def test_login_view(self):
        """Test the login view and authentication"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
        # Test successful login
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('home'))
        
        # Test failed login
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_kyc_view(self):
        """Test the KYC verification process"""
        response = self.client.get(reverse('kyc'))
        self.assertEqual(response.status_code, 200)
        
        # Test KYC submission
        response = self.client.post(reverse('kyc'), {
            'document_type': 'passport',
            'document_number': '123456789',
            'document_image': self.create_test_image()
        })
        self.assertRedirects(response, reverse('profile_setup'))

    def test_profile_setup_view(self):
        """Test the profile setup process"""
        response = self.client.get(reverse('profile_setup'))
        self.assertEqual(response.status_code, 200)
        
        # Test profile setup submission
        response = self.client.post(reverse('profile_setup'), {
            'display_name': 'Test User',
            'bio': 'Test bio',
            'location': 'Test Location'
        })
        self.assertRedirects(response, reverse('payment'))

    @patch('stripe.Customer.create')
    @patch('stripe.checkout.Session.create')
    def test_payment_view(self, mock_session_create, mock_customer_create):
        """Test the payment setup process"""
        # Set up mock responses
        mock_customer_create.return_value = type('Customer', (), {'id': 'cus_test123'})()
        mock_session_create.return_value = type('Session', (), {'id': 'cs_test123'})()
        
        # Ensure KYC and profile are completed
        self.user.userprofile.kyc_completed = True
        self.user.userprofile.profile_completed = True
        self.user.userprofile.save()
        
        # Test GET request
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/payment.html')
        
        # Test creating checkout session
        payment_data = {
            'plan': 'monthly',
            'payment_method_id': 'pm_test_123'
        }
        response = self.client.post(
            reverse('create_checkout_session'),
            data=json.dumps(payment_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('session_id', data)
        self.assertEqual(data['session_id'], 'cs_test123')
        
        # Test payment success
        response = self.client.get(reverse('payment_success'))
        self.assertRedirects(response, reverse('home'))
        self.user.userprofile.refresh_from_db()
        self.assertTrue(self.user.userprofile.payment_completed)

    def test_authentication_flow(self):
        """Test the complete authentication flow from signup to payment"""
        # Test signup
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertRedirects(response, reverse('kyc'))
        
        # Test KYC
        response = self.client.post(reverse('kyc'), {
            'document_type': 'passport',
            'document_number': '123456789',
            'document_image': self.create_test_image()
        })
        self.assertRedirects(response, reverse('profile_setup'))
        
        # Test profile setup
        response = self.client.post(reverse('profile_setup'), {
            'display_name': 'New User',
            'bio': 'New bio',
            'location': 'New Location'
        })
        self.assertRedirects(response, reverse('payment'))

    def test_skip_flows(self):
        """Test skipping optional steps in the authentication flow"""
        # Test skipping KYC
        response = self.client.post(reverse('signup'), {
            'username': 'skipuser',
            'email': 'skipuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'skip_kyc': True
        })
        self.assertRedirects(response, reverse('profile_setup'))
        
        # Test skipping profile setup
        response = self.client.post(reverse('profile_setup'), {
            'skip_setup': True
        })
        self.assertRedirects(response, reverse('home'))

    def create_test_image(self):
        """Helper method to create a test image file"""
        from PIL import Image
        import io
        
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile('test.jpg', image_io.read(), content_type='image/jpeg') 