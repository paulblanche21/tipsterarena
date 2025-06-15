"""Integration tests for tip views."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Tip, UserProfile
import json

class TipViewsTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        # No need to manually create UserProfile; it is auto-created.
        # Create a test tip
        self.tip = Tip.objects.create(
            user=self.user1,
            text='Test tip content',
            sport='football'
        )
        # Set up client
        self.client = Client()
        
    def test_edit_tip_success(self):
        """Test successful tip editing."""
        # Login as tip owner
        self.client.login(username='testuser1', password='testpass123')
        
        # Edit the tip
        response = self.client.post(
            reverse('edit_tip'),
            {
                'tip_id': self.tip.id,
                'text': 'Updated tip content'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['tip']['text'], 'Updated tip content')
        
        # Verify tip was updated in database
        updated_tip = Tip.objects.get(id=self.tip.id)
        self.assertEqual(updated_tip.text, 'Updated tip content')
        
    def test_edit_tip_unauthorized(self):
        """Test editing tip as non-owner."""
        # Login as different user
        self.client.login(username='testuser2', password='testpass123')
        
        # Try to edit the tip
        response = self.client.post(
            reverse('edit_tip'),
            {
                'tip_id': self.tip.id,
                'text': 'Updated tip content'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
        # Verify tip was not updated
        unchanged_tip = Tip.objects.get(id=self.tip.id)
        self.assertEqual(unchanged_tip.text, 'Test tip content')
        
    def test_delete_tip_success(self):
        """Test successful tip deletion."""
        # Login as tip owner
        self.client.login(username='testuser1', password='testpass123')
        
        # Delete the tip
        response = self.client.post(
            reverse('delete_tip'),
            {'tip_id': self.tip.id}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify tip was deleted
        self.assertFalse(Tip.objects.filter(id=self.tip.id).exists())
        
    def test_delete_tip_unauthorized(self):
        """Test deleting tip as non-owner."""
        # Login as different user
        self.client.login(username='testuser2', password='testpass123')
        
        # Try to delete the tip
        response = self.client.post(
            reverse('delete_tip'),
            {'tip_id': self.tip.id}
        )
        
        # Check response
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
        # Verify tip was not deleted
        self.assertTrue(Tip.objects.filter(id=self.tip.id).exists())
        
    def test_edit_tip_missing_fields(self):
        """Test editing tip with missing required fields."""
        # Login as tip owner
        self.client.login(username='testuser1', password='testpass123')
        
        # Try to edit without required fields
        response = self.client.post(
            reverse('edit_tip'),
            {'tip_id': self.tip.id}  # Missing text field
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        
    def test_delete_tip_missing_id(self):
        """Test deleting tip with missing tip_id."""
        # Login as tip owner
        self.client.login(username='testuser1', password='testpass123')
        
        # Try to delete without tip_id
        response = self.client.post(
            reverse('delete_tip'),
            {}  # Missing tip_id
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success']) 