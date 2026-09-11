import time
from typing import Dict, Tuple

class RateLimiter:
    """
    Sliding window rate limiter to restrict WASM executions per tenant.
    Default: 60 executions per minute per tenant.
    """
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._tenant_history: Dict[str, list] = {}

    def check_rate_limit(self, tenant_id: str) -> Tuple[bool, int]:
        """
        Returns (is_allowed, remaining_requests).
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        history = self._tenant_history.get(tenant_id, [])
        # Evict old requests outside window
        valid_history = [t for t in history if t > cutoff]
        
        if len(valid_history) >= self.max_requests:
            self._tenant_history[tenant_id] = valid_history
            return False, 0
            
        valid_history.append(now)
        self._tenant_history[tenant_id] = valid_history
        remaining = self.max_requests - len(valid_history)
        return True, remaining

rate_limiter = RateLimiter()
