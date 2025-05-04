from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import time
from concurrent.futures import ThreadPoolExecutor

from core.factories import (
    UserFactory, GolfEventFactory, FootballEventFactory,
    TennisEventFactory, TipFactory
)

class APIIntegrationTest(TestCase):
    """Test suite for API integration scenarios."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.golf_event = GolfEventFactory()
        self.football_event = FootballEventFactory()
        self.tennis_event = TennisEventFactory()
        self.tip = TipFactory(user=self.user)

    def test_cross_sport_integration(self):
        """Test interaction between different sports APIs"""
        urls = [
            reverse('golf-events-list'),
            reverse('football_events'),
            reverse('tennis-events-list')
        ]
        
        # Test sequential access
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        # Test concurrent access
        def fetch_url(url):
            return self.client.get(url)
            
        with ThreadPoolExecutor(max_workers=3) as executor:
            responses = list(executor.map(fetch_url, urls))
            
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_response_times(self):
        """Test API response times under load"""
        urls = {
            'golf': reverse('golf-events-list'),
            'football': reverse('football_events'),
            'tennis': reverse('tennis-events-list'),
            'tip': reverse('tip-detail', args=[self.tip.id])
        }
        
        for name, url in urls.items():
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertLess(
                end_time - start_time, 
                1.0,  # Response should be under 1 second
                f"{name} API took too long to respond"
            )

    def test_error_handling(self):
        """Test error handling across different APIs"""
        # Test invalid event IDs
        invalid_urls = [
            reverse('golf-events-list') + '?event_id=nonexistent',
            reverse('football_events') + '?event_id=nonexistent',
            reverse('tennis-events-list') + '?event_id=nonexistent'
        ]
        
        for url in invalid_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn('error', response.data)

        # Test invalid query parameters
        urls_with_params = [
            (reverse('golf-events-list'), {'state': 'invalid'}),
            (reverse('football_events'), {'category': 'invalid'}),
            (reverse('tennis-events-list'), {'tournament': 'invalid'})
        ]
        
        for url, params in urls_with_params:
            response = self.client.get(url, params)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_data_consistency(self):
        """Test data consistency across related endpoints"""
        # Create a tip with associated event
        tip = TipFactory(
            user=self.user,
            sport='golf',
            text='Test tip for golf event'
        )
        
        # Verify tip data
        tip_response = self.client.get(
            reverse('tip-detail', args=[tip.id])
        )
        self.assertEqual(tip_response.status_code, status.HTTP_200_OK)
        
        # Verify event data
        event_response = self.client.get(
            reverse('golf-events-list')
        )
        self.assertEqual(event_response.status_code, status.HTTP_200_OK)
        
        # Verify data consistency
        self.assertEqual(tip_response.data['sport'], 'golf')

    def test_authentication_consistency(self):
        """Test authentication behavior across endpoints"""
        # Test with unauthenticated client
        unauthenticated_client = APIClient()
        
        # Public endpoints should be accessible
        public_urls = [
            reverse('golf-events-list'),
            reverse('football_events'),
            reverse('tennis-events-list')
        ]
        
        for url in public_urls:
            response = unauthenticated_client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Protected endpoints should require authentication
        protected_urls = [
            reverse('tip-create'),
            reverse('get_notifications'),
            reverse('mark_notification_read')
        ]
        
        for url in protected_urls:
            response = unauthenticated_client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 