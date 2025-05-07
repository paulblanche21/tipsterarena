import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from core.models import User, HorseRacingBettingOdds, HorseRacingRunner


class HorseRacingBettingOddsBulkUpsertTest(TestCase):
    def setUp(self):
        # Create a test user and get their token
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        
        # Create a test runner
        self.runner = HorseRacingRunner.objects.create(
            name='Test Runner',
            number=1
        )
        
        # Create an existing odds record
        self.existing_odds = HorseRacingBettingOdds.objects.create(
            runner=self.runner,
            bookmaker='Test Bookmaker',
            odds=2.5
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # URL for the view
        self.url = reverse('horse_racing_betting_odds_bulk_upsert')
        
    def test_create_new_odds(self):
        """Test creating new odds records."""
        data = [{
            'runner': self.runner.id,
            'bookmaker': 'New Bookmaker',
            'odds': 3.0
        }]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['bookmaker'], 'New Bookmaker')
        self.assertEqual(float(response.data[0]['odds']), 3.0)
        
    def test_update_existing_odds(self):
        """Test updating existing odds records."""
        data = [{
            'id': self.existing_odds.id,
            'runner': self.runner.id,
            'bookmaker': 'Updated Bookmaker',
            'odds': 4.0
        }]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['bookmaker'], 'Updated Bookmaker')
        self.assertEqual(float(response.data[0]['odds']), 4.0)
        
    def test_mixed_create_and_update(self):
        """Test a mix of creating new and updating existing odds."""
        data = [
            {
                'id': self.existing_odds.id,
                'runner': self.runner.id,
                'bookmaker': 'Updated Bookmaker',
                'odds': 4.0
            },
            {
                'runner': self.runner.id,
                'bookmaker': 'New Bookmaker',
                'odds': 3.0
            }
        ]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        
    def test_invalid_data(self):
        """Test handling of invalid data."""
        data = [{
            'runner': self.runner.id,
            'bookmaker': 'Invalid Bookmaker',
            'odds': 'not a number'  # Invalid odds value
        }]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
    def test_unauthorized_access(self):
        """Test that unauthorized access is rejected."""
        client = APIClient()  # No token set
        data = [{
            'runner': self.runner.id,
            'bookmaker': 'Test Bookmaker',
            'odds': 2.0
        }]
        
        response = client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        
    def test_invalid_odds_id_format(self):
        """Test handling of invalid odds ID format."""
        data = [{
            'id': 'invalid_id_format',
            'runner': self.runner.id,
            'bookmaker': 'Test Bookmaker',
            'odds': 2.0
        }]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
    def test_nonexistent_odds_id(self):
        """Test handling of nonexistent odds ID."""
        data = [{
            'id': 999999,  # Non-existent ID
            'runner': self.runner.id,
            'bookmaker': 'Test Bookmaker',
            'odds': 2.0
        }]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)  # Should create new record
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['bookmaker'], 'Test Bookmaker') 