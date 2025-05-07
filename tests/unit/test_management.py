"""
Unit tests for Tipster Arena management commands.
Tests custom Django management commands functionality.
"""
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event
from io import StringIO

User = get_user_model()

class ManagementCommandsTest(TestCase):
    """Test suite for management commands."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )

    def test_cleanup_old_tips(self):
        """Test cleanup_old_tips command."""
        # Create old tips
        old_date = timezone.now() - timezone.timedelta(days=31)
        for i in range(5):
            Tip.objects.create(
                user=self.user,
                prediction=f'Old tip {i}',
                odds='2.0',
                stake='10.0',
                status='win',
                created_at=old_date
            )
        
        # Create recent tips
        for i in range(5):
            Tip.objects.create(
                user=self.user,
                prediction=f'Recent tip {i}',
                odds='2.0',
                stake='10.0',
                status='win'
            )
        
        out = StringIO()
        call_command('cleanup_old_tips', stdout=out)
        
        # Check that old tips are deleted
        self.assertEqual(Tip.objects.count(), 5)
        self.assertFalse(
            Tip.objects.filter(prediction__startswith='Old').exists()
        )

    def test_update_user_stats(self):
        """Test update_user_stats command."""
        # Create tips with different statuses
        for i in range(10):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test tip {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 5 else 'loss'
            )
        
        out = StringIO()
        call_command('update_user_stats', stdout=out)
        
        # Refresh profile from database
        self.profile.refresh_from_db()
        
        # Check stats are updated
        self.assertEqual(self.profile.total_tips, 10)
        self.assertEqual(self.profile.win_rate, 50.0)

    def test_sync_events(self):
        """Test sync_events command."""
        out = StringIO()
        call_command('sync_events', stdout=out)
        
        # Check that events are created
        self.assertTrue(Event.objects.exists())
        
        # Check output contains success message
        self.assertIn('Successfully synced', out.getvalue())

    def test_cleanup_inactive_users(self):
        """Test cleanup_inactive_users command."""
        # Create inactive user
        inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='testpass123',
            last_login=timezone.now() - timezone.timedelta(days=31)
        )
        UserProfile.objects.create(
            user=inactive_user,
            display_name='Inactive User'
        )
        
        out = StringIO()
        call_command('cleanup_inactive_users', stdout=out)
        
        # Check that inactive user is deleted
        self.assertFalse(
            User.objects.filter(username='inactive').exists()
        )

    def test_generate_test_data(self):
        """Test generate_test_data command."""
        out = StringIO()
        call_command('generate_test_data', stdout=out)
        
        # Check that test data is created
        self.assertTrue(User.objects.exists())
        self.assertTrue(Tip.objects.exists())
        self.assertTrue(Event.objects.exists())
        
        # Check output contains success message
        self.assertIn('Successfully generated', out.getvalue()) 