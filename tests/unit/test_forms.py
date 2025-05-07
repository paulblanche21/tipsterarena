"""
Unit tests for Tipster Arena forms.
Tests form validation and data processing.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from core.forms import (
    UserProfileForm,
    KYCForm
)

User = get_user_model()

class UserProfileFormTest(TestCase):
    """Test suite for UserProfileForm."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.form_data = {
            'avatar': SimpleUploadedFile(
                'test.jpg',
                b'fake image content',
                content_type='image/jpeg'
            ),
            'banner': SimpleUploadedFile(
                'test_banner.jpg',
                b'fake image content',
                content_type='image/jpeg'
            )
        }

    def test_valid_form(self):
        """Test form with valid data."""
        form = UserProfileForm(data={}, files=self.form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_file_size(self):
        """Test form with invalid file size."""
        # Create a file larger than 5MB
        large_file = SimpleUploadedFile(
            'large.jpg',
            b'x' * (6 * 1024 * 1024),  # 6MB
            content_type='image/jpeg'
        )
        form_data = {'avatar': large_file}
        form = UserProfileForm(data={}, files=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)

    def test_invalid_file_type(self):
        """Test form with invalid file type."""
        # Create a non-image file
        text_file = SimpleUploadedFile(
            'test.txt',
            b'not an image',
            content_type='text/plain'
        )
        form_data = {'avatar': text_file}
        form = UserProfileForm(data={}, files=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)

class KYCFormTest(TestCase):
    """Test suite for KYCForm."""
    
    def setUp(self):
        """Set up test data."""
        self.form_data = {
            'full_name': 'John Doe',
            'dob_day': 1,
            'dob_month': 1,
            'dob_year': 1990,
            'street_address': '123 Test St',
            'city': 'Test City',
            'postal_code': '12345',
            'country': 'Test Country'
        }

    def test_valid_form(self):
        """Test form with valid data."""
        form = KYCForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['date_of_birth'].year, 1990)
        self.assertEqual(
            form.cleaned_data['address'],
            '123 Test St, Test City, 12345, Test Country'
        )

    def test_invalid_date(self):
        """Test form with invalid date."""
        form_data = self.form_data.copy()
        form_data['dob_day'] = 32  # Invalid day
        form = KYCForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_future_date(self):
        """Test form with future date."""
        form_data = self.form_data.copy()
        form_data['dob_year'] = 2100  # Future year
        form = KYCForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_underage(self):
        """Test form with underage user."""
        form_data = self.form_data.copy()
        form_data['dob_year'] = 2020  # Too young
        form = KYCForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors) 