"""
Performance tests for Tipster Arena.
Tests load, stress, and performance characteristics.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile, Tip, Event
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueries
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

User = get_user_model()

class PerformanceTest(TestCase):
    """Test suite for performance characteristics."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_database_query_performance(self):
        """Test database query performance."""
        # Create test data
        for i in range(100):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 50 else 'loss'
            )
        
        # Test query performance
        with CaptureQueries(connection) as queries:
            start_time = time.time()
            response = self.client.get(reverse('user_tips'))
            end_time = time.time()
        
        # Check response time
        self.assertLess(end_time - start_time, 1.0)  # Should be under 1 second
        
        # Check number of queries
        self.assertLess(len(queries), 5)  # Should use less than 5 queries

    def test_api_response_time(self):
        """Test API endpoint response times."""
        endpoints = [
            'api:user_profile',
            'api:user_tips',
            'api:events',
            'api:search'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.client.get(reverse(endpoint))
            end_time = time.time()
            
            # Check response time
            self.assertLess(end_time - start_time, 0.5)  # Should be under 500ms
            self.assertEqual(response.status_code, 200)

    def test_concurrent_requests(self):
        """Test concurrent request handling."""
        def make_request():
            self.client.get(reverse('user_tips'))
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            for future in futures:
                future.result()
            end_time = time.time()
        
        # Check total time for concurrent requests
        self.assertLess(end_time - start_time, 2.0)  # Should be under 2 seconds

    def test_cache_performance(self):
        """Test cache performance."""
        # First request (cache miss)
        start_time = time.time()
        response = self.client.get(reverse('user_tips'))
        first_request_time = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response = self.client.get(reverse('user_tips'))
        second_request_time = time.time() - start_time
        
        # Cache hit should be significantly faster
        self.assertLess(second_request_time, first_request_time * 0.5)

    def test_memory_usage(self):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large dataset
        for i in range(1000):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win' if i < 500 else 'loss'
            )
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # Less than 50MB

    def test_stress_test(self):
        """Test system under stress."""
        def create_tip():
            Tip.objects.create(
                user=self.user,
                prediction=f'Stress test tip {random.randint(1, 1000)}',
                odds='2.0',
                stake='10.0',
                status='win'
            )
        
        # Create 100 tips concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(create_tip) for _ in range(100)]
            for future in futures:
                future.result()
            end_time = time.time()
        
        # Check total time for stress test
        self.assertLess(end_time - start_time, 5.0)  # Should be under 5 seconds
        
        # Verify all tips were created
        self.assertEqual(Tip.objects.count(), 100)

    def test_search_performance(self):
        """Test search performance."""
        # Create test data
        for i in range(100):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win'
            )
        
        # Test search performance
        start_time = time.time()
        response = self.client.get(
            reverse('search'),
            {'q': 'Test prediction'}
        )
        end_time = time.time()
        
        # Check response time
        self.assertLess(end_time - start_time, 1.0)  # Should be under 1 second
        self.assertEqual(response.status_code, 200)

    def test_pagination_performance(self):
        """Test pagination performance."""
        # Create test data
        for i in range(100):
            Tip.objects.create(
                user=self.user,
                prediction=f'Test prediction {i}',
                odds='2.0',
                stake='10.0',
                status='win'
            )
        
        # Test pagination performance
        start_time = time.time()
        response = self.client.get(
            reverse('user_tips'),
            {'page': 1, 'page_size': 10}
        )
        end_time = time.time()
        
        # Check response time
        self.assertLess(end_time - start_time, 0.5)  # Should be under 500ms
        self.assertEqual(response.status_code, 200) 