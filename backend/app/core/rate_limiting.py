"""
Rate limiting implementation for HomeGuard Monitor.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class RateLimiter:
    """
    Rate limiter implementation using sliding window algorithm.
    """
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
            burst_size: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._windows: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request from client is allowed.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        
        # Clean old entries
        self._clean_old_entries(client_id, window_start)
        
        # Check current count for THIS client
        client_requests = self._windows.get(client_id, [])
        current_count = len(client_requests)
        
        if current_count >= self.requests_per_minute:
            return False
        
        # Check burst limit for THIS client
        recent_requests = self._get_recent_requests(client_id, now - timedelta(seconds=10))
        if len(recent_requests) >= self.burst_size:
            return False
        
        # Add current request
        self._windows[client_id].append(now)
        
        return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """
        Get remaining requests for client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Number of remaining requests
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        
        self._clean_old_entries(client_id, window_start)
        
        return max(0, self.requests_per_minute - len(self._windows[client_id]))
    
    def get_reset_time(self, client_id: str) -> Optional[datetime]:
        """
        Get time when rate limit resets for client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            datetime when limit resets, or None if no limit
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        
        self._clean_old_entries(client_id, window_start)
        
        if not self._windows[client_id]:
            return None
        
        oldest_request = min(self._windows[client_id])
        return oldest_request + timedelta(minutes=1)
    
    def reset(self, client_id: str) -> None:
        """
        Reset rate limit for client.
        
        Args:
            client_id: Unique identifier for the client
        """
        self._windows[client_id].clear()
    
    def reset_all(self) -> None:
        """Reset rate limits for all clients."""
        self._windows.clear()
    
    def _clean_old_entries(self, client_id: str, before: datetime) -> None:
        """
        Remove entries older than specified time.
        
        Args:
            client_id: Client identifier
            before: Remove entries older than this time
        """
        self._windows[client_id] = [
            t for t in self._windows[client_id]
            if t > before
        ]
    
    def _get_recent_requests(self, client_id: str, since: datetime) -> List[datetime]:
        """
        Get recent requests within time window.
        
        Args:
            client_id: Client identifier
            since: Get requests after this time
            
        Returns:
            List of request timestamps
        """
        return [
            t for t in self._windows[client_id]
            if t > since
        ]


class EndpointRateLimiter:
    """
    Per-endpoint rate limiter with different limits per endpoint.
    """
    
    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        self._default_limiter = RateLimiter(
            requests_per_minute=60,
            burst_size=10
        )
    
    def get_limiter(self, endpoint: str) -> RateLimiter:
        """
        Get rate limiter for endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Rate limiter for endpoint
        """
        if endpoint not in self._limiters:
            # Configure endpoint-specific limits
            if "/auth/login" in endpoint:
                self._limiters[endpoint] = RateLimiter(
                    requests_per_minute=10,
                    burst_size=3
                )
            elif "/auth/register" in endpoint:
                self._limiters[endpoint] = RateLimiter(
                    requests_per_minute=20,
                    burst_size=5
                )
            elif "/metrics/ingest" in endpoint:
                self._limiters[endpoint] = RateLimiter(
                    requests_per_minute=100,
                    burst_size=20
                )
            else:
                self._limiters[endpoint] = self._default_limiter
        
        return self._limiters[endpoint]
    
    def is_allowed(self, endpoint: str, client_id: str) -> bool:
        """
        Check if request to endpoint is allowed.
        
        Args:
            endpoint: API endpoint path
            client_id: Client identifier
            
        Returns:
            True if request is allowed
        """
        limiter = self.get_limiter(endpoint)
        return limiter.is_allowed(client_id)
    
    def get_remaining(self, endpoint: str, client_id: str) -> int:
        """
        Get remaining requests for endpoint.
        
        Args:
            endpoint: API endpoint path
            client_id: Client identifier
            
        Returns:
            Number of remaining requests
        """
        limiter = self.get_limiter(endpoint)
        return limiter.get_remaining_requests(client_id)
    
    def add_headers(self, response, endpoint: str, client_id: str) -> dict:
        """
        Add rate limit headers to response.
        
        Args:
            response: Response object to modify
            endpoint: API endpoint path
            client_id: Client identifier
            
        Returns:
            Headers dict
        """
        limiter = self.get_limiter(endpoint)
        remaining = limiter.get_remaining_requests(client_id)
        reset_time = limiter.get_reset_time(client_id)
        
        headers = {
            "X-RateLimit-Limit": str(limiter.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
        }
        
        if reset_time:
            headers["X-RateLimit-Reset"] = reset_time.isoformat()
        
        return headers


# Global rate limiter instance
rate_limiter = EndpointRateLimiter()
