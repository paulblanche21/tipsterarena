from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'

class AnonymousBurstRateThrottle(AnonRateThrottle):
    scope = 'anonymous_burst'

class AnonymousSustainedRateThrottle(AnonRateThrottle):
    scope = 'anonymous_sustained' 