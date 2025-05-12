"""
Rate limiting throttles for the Tipster Arena API.

This module provides rate limiting classes that control how frequently users can make API requests.
It includes both burst (short-term) and sustained (long-term) rate limits for both authenticated
and anonymous users.

The throttles are configured in settings.py with the following scopes:
- burst: Short-term rate limit for authenticated users
- sustained: Long-term rate limit for authenticated users
- anonymous_burst: Short-term rate limit for anonymous users
- anonymous_sustained: Long-term rate limit for anonymous users
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class BurstRateThrottle(UserRateThrottle):
    """
    Rate limiting for authenticated users' burst requests.
    
    This throttle controls the maximum number of requests an authenticated user
    can make in a short time period (e.g., per minute). Used to prevent
    rapid-fire API calls while still allowing reasonable burst activity.
    """
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    """
    Rate limiting for authenticated users' sustained requests.
    
    This throttle controls the maximum number of requests an authenticated user
    can make over a longer time period (e.g., per day). Used to prevent
    excessive API usage while allowing normal usage patterns.
    """
    scope = 'sustained'

class AnonymousBurstRateThrottle(AnonRateThrottle):
    """
    Rate limiting for anonymous users' burst requests.
    
    This throttle controls the maximum number of requests an anonymous user
    can make in a short time period. Typically more restrictive than
    authenticated user limits to prevent abuse.
    """
    scope = 'anonymous_burst'

class AnonymousSustainedRateThrottle(AnonRateThrottle):
    """
    Rate limiting for anonymous users' sustained requests.
    
    This throttle controls the maximum number of requests an anonymous user
    can make over a longer time period. Used to prevent abuse while still
    allowing basic API access for unauthenticated users.
    """
    scope = 'anonymous_sustained' 