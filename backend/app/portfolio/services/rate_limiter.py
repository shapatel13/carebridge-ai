"""Rate limiting for API calls with exponential backoff."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    calls_per_second: float = 2.0  # Default: 2 calls per second
    burst_size: int = 5  # Allow burst of 5 calls
    retry_attempts: int = 3
    retry_base_delay: float = 1.0  # Base delay for exponential backoff
    retry_max_delay: float = 60.0
    circuit_failure_threshold: int = 5  # Failures before opening circuit
    circuit_recovery_timeout: float = 30.0  # Seconds before half-open
    circuit_success_threshold: int = 2  # Successes to close circuit


@dataclass
class ServiceMetrics:
    """Metrics for a rate-limited service."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    retried_calls: int = 0
    rate_limited_calls: int = 0
    circuit_opened_count: int = 0
    last_failure_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class RateLimiter:
    """
    Async rate limiter with token bucket algorithm and circuit breaker.
    
    Features:
    - Token bucket for smooth rate limiting
    - Exponential backoff with jitter
    - Circuit breaker pattern for fault tolerance
    - Per-service metrics tracking
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration
        """
        self.config = config or RateLimitConfig()
        self._tokens: Dict[str, float] = {}
        self._last_update: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._circuit_states: Dict[str, CircuitState] = {}
        self._circuit_opened_at: Dict[str, float] = {}
        self._metrics: Dict[str, ServiceMetrics] = {}
        
    def _get_lock(self, service: str) -> asyncio.Lock:
        """Get or create lock for service."""
        if service not in self._locks:
            self._locks[service] = asyncio.Lock()
        return self._locks[service]
    
    def _get_metrics(self, service: str) -> ServiceMetrics:
        """Get or create metrics for service."""
        if service not in self._metrics:
            self._metrics[service] = ServiceMetrics()
        return self._metrics[service]
    
    def _update_tokens(self, service: str) -> float:
        """
        Update token bucket for service.
        
        Returns:
            Current token count
        """
        now = time.monotonic()
        
        if service not in self._tokens:
            self._tokens[service] = self.config.burst_size
            self._last_update[service] = now
            return self._tokens[service]
        
        elapsed = now - self._last_update[service]
        tokens_to_add = elapsed * self.config.calls_per_second
        
        self._tokens[service] = min(
            self.config.burst_size,
            self._tokens[service] + tokens_to_add
        )
        self._last_update[service] = now
        
        return self._tokens[service]
    
    async def acquire(self, service: str = "default") -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            service: Service identifier
            
        Returns:
            True if request should proceed
        """
        async with self._get_lock(service):
            # Check circuit breaker
            if not self._check_circuit(service):
                self._get_metrics(service).rate_limited_calls += 1
                return False
            
            # Update and check tokens
            tokens = self._update_tokens(service)
            
            if tokens >= 1:
                self._tokens[service] -= 1
                return True
            else:
                # Calculate wait time for next token
                wait_time = (1 - tokens) / self.config.calls_per_second
                logger.debug(f"Rate limit hit for {service}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                return await self.acquire(service)
    
    def _check_circuit(self, service: str) -> bool:
        """
        Check if circuit breaker allows request.
        
        Returns:
            True if request can proceed
        """
        state = self._circuit_states.get(service, CircuitState.CLOSED)
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.OPEN:
            opened_at = self._circuit_opened_at.get(service, 0)
            if time.monotonic() - opened_at > self.config.circuit_recovery_timeout:
                logger.info(f"Circuit for {service} entering half-open state")
                self._circuit_states[service] = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN - allow test request
        return True
    
    def record_success(self, service: str = "default") -> None:
        """Record successful request."""
        metrics = self._get_metrics(service)
        metrics.total_calls += 1
        metrics.successful_calls += 1
        metrics.consecutive_failures = 0
        metrics.consecutive_successes += 1
        
        # Check if we should close circuit
        if self._circuit_states.get(service) == CircuitState.HALF_OPEN:
            if metrics.consecutive_successes >= self.config.circuit_success_threshold:
                logger.info(f"Circuit for {service} closed after recovery")
                self._circuit_states[service] = CircuitState.CLOSED
                metrics.consecutive_successes = 0
    
    def record_failure(self, service: str = "default", is_retryable: bool = True) -> None:
        """
        Record failed request.
        
        Args:
            service: Service identifier
            is_retryable: Whether this failure type can be retried
        """
        metrics = self._get_metrics(service)
        metrics.total_calls += 1
        metrics.failed_calls += 1
        metrics.consecutive_failures += 1
        metrics.consecutive_successes = 0
        metrics.last_failure_time = time.monotonic()
        
        # Check if we should open circuit
        if metrics.consecutive_failures >= self.config.circuit_failure_threshold:
            if self._circuit_states.get(service) != CircuitState.OPEN:
                logger.warning(
                    f"Circuit opened for {service} after "
                    f"{metrics.consecutive_failures} consecutive failures"
                )
                self._circuit_states[service] = CircuitState.OPEN
                self._circuit_opened_at[service] = time.monotonic()
                metrics.circuit_opened_count += 1
    
    async def call_with_retry(
        self,
        func: Callable[..., Any],
        service: str = "default",
        *args,
        **kwargs
    ) -> Any:
        """
        Call function with rate limiting and retry logic.
        
        Args:
            func: Async function to call
            service: Service identifier for rate limiting
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries exhausted or circuit open
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(self.config.retry_attempts):
            # Acquire rate limit permission
            if not await self.acquire(service):
                raise Exception(f"Circuit breaker open for service: {service}")
            
            try:
                result = await func(*args, **kwargs)
                self.record_success(service)
                return result
                
            except Exception as e:
                last_exception = e
                self.record_failure(service, is_retryable=self._is_retryable(e))
                
                if attempt < self.config.retry_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Request to {service} failed (attempt {attempt + 1}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception or Exception(f"Max retries exceeded for {service}")
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        import random
        
        # Exponential backoff: base * 2^attempt
        delay = self.config.retry_base_delay * (2 ** attempt)
        
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay += jitter
        
        # Cap at max delay
        return min(delay, self.config.retry_max_delay)
    
    def _is_retryable(self, exception: Exception) -> bool:
        """
        Determine if exception type is retryable.
        
        Args:
            exception: The exception that occurred
            
        Returns:
            True if request should be retried
        """
        # Network errors are typically retryable
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
        
        # Check for HTTP status codes that suggest retry
        if hasattr(exception, 'status'):
            retryable_statuses = {429, 500, 502, 503, 504}
            return exception.status in retryable_statuses
        
        return isinstance(exception, retryable_exceptions)
    
    def get_metrics(self, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for service(s).
        
        Args:
            service: Service identifier (None for all services)
            
        Returns:
            Metrics dictionary
        """
        if service:
            m = self._get_metrics(service)
            return {
                "service": service,
                "total_calls": m.total_calls,
                "successful_calls": m.successful_calls,
                "failed_calls": m.failed_calls,
                "success_rate": (
                    m.successful_calls / m.total_calls * 100 
                    if m.total_calls > 0 else 0
                ),
                "retried_calls": m.retried_calls,
                "rate_limited_calls": m.rate_limited_calls,
                "circuit_opened_count": m.circuit_opened_count,
                "circuit_state": self._circuit_states.get(service, CircuitState.CLOSED).value,
                "consecutive_failures": m.consecutive_failures,
            }
        else:
            return {
                service: self.get_metrics(service)
                for service in self._metrics.keys()
            }
    
    def reset_circuit(self, service: str = "default") -> None:
        """Manually reset circuit breaker for a service."""
        self._circuit_states[service] = CircuitState.CLOSED
        metrics = self._get_metrics(service)
        metrics.consecutive_failures = 0
        metrics.consecutive_successes = 0
        logger.info(f"Circuit for {service} manually reset")


# Decorator for rate-limited functions
def rate_limited(
    limiter: RateLimiter,
    service: str = "default",
    retry: bool = True
):
    """
    Decorator to apply rate limiting to async functions.
    
    Args:
        limiter: RateLimiter instance
        service: Service identifier
        retry: Whether to retry on failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if retry:
                return await limiter.call_with_retry(func, service, *args, **kwargs)
            else:
                if await limiter.acquire(service):
                    try:
                        result = await func(*args, **kwargs)
                        limiter.record_success(service)
                        return result
                    except Exception as e:
                        limiter.record_failure(service)
                        raise
                else:
                    raise Exception(f"Circuit breaker open for service: {service}")
        return wrapper
    return decorator


# Global rate limiter instance
_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = RateLimiter(config)
    return _limiter_instance
