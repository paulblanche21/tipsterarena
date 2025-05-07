"""
Unit tests for Tipster Arena admin interface.
Tests admin model registrations and custom admin actions.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from core.admin import (
    UserProfileAdmin,
    TipAdmin,
    EventAdmin
)
from core.models import UserProfile, Tip, Event

User = get_user_model()

class MockRequest:
    pass

class MockSuperUser:
    def has_perm(self, perm):
        return True

class UserProfileAdminTest(TestCase):
    """Test suite for UserProfile admin."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = UserProfileAdmin(UserProfile, self.site)
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Admin User'
        )
        self.request = MockRequest()
        self.request.user = MockSuperUser()

    def test_list_display(self):
        """Test list display fields."""
        self.assertIn('user', self.admin.list_display)
        self.assertIn('display_name', self.admin.list_display)
        self.assertIn('win_rate', self.admin.list_display)

    def test_search_fields(self):
        """Test search functionality."""
        self.assertIn('user__username', self.admin.search_fields)
        self.assertIn('display_name', self.admin.search_fields)

    def test_list_filter(self):
        """Test list filters."""
        self.assertIn('subscription_status', self.admin.list_filter)
        self.assertIn('kyc_verified', self.admin.list_filter)

class TipAdminTest(TestCase):
    """Test suite for Tip admin."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = TipAdmin(Tip, self.site)
        self.user = User.objects.create_user(
            username='tipster',
            email='tipster@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            name='Test Event',
            start_time='2024-01-01 12:00:00',
            status='upcoming'
        )
        self.tip = Tip.objects.create(
            user=self.user,
            event=self.event,
            prediction='Test prediction',
            odds='2.0',
            stake='10.0'
        )
        self.request = MockRequest()
        self.request.user = MockSuperUser()

    def test_list_display(self):
        """Test list display fields."""
        self.assertIn('user', self.admin.list_display)
        self.assertIn('event', self.admin.list_display)
        self.assertIn('prediction', self.admin.list_display)
        self.assertIn('status', self.admin.list_display)

    def test_list_filter(self):
        """Test list filters."""
        self.assertIn('status', self.admin.list_filter)
        self.assertIn('created_at', self.admin.list_filter)

    def test_verify_tip_action(self):
        """Test verify tip admin action."""
        self.admin.verify_tip(self.request, Tip.objects.all())
        self.tip.refresh_from_db()
        self.assertEqual(self.tip.status, 'verified')

class EventAdminTest(TestCase):
    """Test suite for Event admin."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = EventAdmin(Event, self.site)
        self.event = Event.objects.create(
            name='Test Event',
            start_time='2024-01-01 12:00:00',
            status='upcoming'
        )
        self.request = MockRequest()
        self.request.user = MockSuperUser()

    def test_list_display(self):
        """Test list display fields."""
        self.assertIn('name', self.admin.list_display)
        self.assertIn('start_time', self.admin.list_display)
        self.assertIn('status', self.admin.list_display)

    def test_list_filter(self):
        """Test list filters."""
        self.assertIn('status', self.admin.list_filter)
        self.assertIn('start_time', self.admin.list_filter)

    def test_search_fields(self):
        """Test search functionality."""
        self.assertIn('name', self.admin.search_fields)
        self.assertIn('description', self.admin.search_fields) 