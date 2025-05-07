"""
Performance tests for Tipster Arena caching system.
Tests cache effectiveness and performance.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from core.models import UserProfile,  Event
from django.utils import timezone
import time

User = get_user_model()

class CachePerformanceTest(TestCase):
    """Test suite for cache performance."""
    
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
            display_name='Test User',
            bio='Test bio',
            location='Test Location'
        )
        # Create test events
        self.events = [
            Event.objects.create(
                name=f'Test Event {i}',
                start_time=timezone.now(),
                status='upcoming'
            ) for i in range(10)
        ]
        # Clear cache before each test
        cache.clear()

    def test_cache_hit_performance(self):
        """Test performance of cached responses."""
        # First request (cache miss)
        start_time = time.time()
        response1 = self.client.get(reverse('event-list'))
        end_time = time.time()
        first_request_time = end_time - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = self.client.get(reverse('event-list'))
        end_time = time.time()
        second_request_time = end_time - start_time
        
        # Cache hit should be significantly faster
        self.assertLess(second_request_time, first_request_time * 0.5)
        self.assertEqual(response1.content, response2.content)

    def test_cache_invalidation(self):
        """Test cache invalidation performance."""
        # Get initial response
        response1 = self.client.get(reverse('event-list'))
        
        # Create new event
        Event.objects.create(
            name='New Event',
            start_time=timezone.now(),
            status='upcoming'
        )
        
        # Get response after cache invalidation
        start_time = time.time()
        response2 = self.client.get(reverse('event-list'))
        end_time = time.time()
        
        # Response should be different and within reasonable time
        self.assertNotEqual(response1.content, response2.content)
        self.assertLess(end_time - start_time, 0.2)

    def test_cache_storage_performance(self):
        """Test performance of cache storage operations."""
        # Test storing large data
        large_data = {
            'events': [
                {
                    'id': i,
                    'name': f'Event {i}',
                    'status': 'upcoming'
                } for i in range(1000)
            ]
        }
        
        start_time = time.time()
        cache.set('large_data', large_data, timeout=300)
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.1)
        
        # Test retrieving large data
        start_time = time.time()
        retrieved_data = cache.get('large_data')
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.1)
        self.assertEqual(retrieved_data, large_data)

    def test_cache_concurrent_access(self):
        """Test cache performance under concurrent access."""
        import threading
        
        def cache_operation():
            for i in range(10):
                cache.set(f'key_{i}', f'value_{i}')
                _ = cache.get(f'key_{i}')
        
        # Create 5 concurrent threads
        threads = [threading.Thread(target=cache_operation) for _ in range(5)]
        start_time = time.time()
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All operations should complete within reasonable time
        self.assertLess(end_time - start_time, 1.0)

    def test_cache_patterns(self):
        """Test different caching patterns."""
        # Test cache-aside pattern
        def get_event_with_cache(event_id):
            # Try cache first
            event = cache.get(f'event_{event_id}')
            if event is None:
                # Cache miss, get from database
                event = Event.objects.get(id=event_id)
                # Store in cache
                cache.set(f'event_{event_id}', event, timeout=300)
            return event
        
        # Test write-through pattern
        def create_event_with_cache(event_data):
            # Create in database
            event = Event.objects.create(**event_data)
            # Update cache
            cache.set(f'event_{event.id}', event, timeout=300)
            return event
        
        # Test write-behind pattern
        def update_event_with_cache(event_id, data):
            # Update cache immediately
            cache.set(f'event_{event_id}_pending', data, timeout=300)
            # Update database asynchronously (simulated)
            time.sleep(0.1)
            Event.objects.filter(id=event_id).update(**data)
            cache.delete(f'event_{event_id}_pending')
        
        # Test cache performance with these patterns
        start_time = time.time()
        
        # Test cache-aside
        event = get_event_with_cache(self.events[0].id)
        self.assertIsNotNone(event)
        
        # Test write-through
        new_event = create_event_with_cache({
            'name': 'New Event',
            'start_time': timezone.now(),
            'status': 'upcoming'
        })
        self.assertIsNotNone(new_event)
        
        # Test write-behind
        update_event_with_cache(new_event.id, {'name': 'Updated Event'})
        
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.5) 