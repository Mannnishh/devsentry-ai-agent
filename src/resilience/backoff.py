"""Resilience utilities: exponential backoff with full jitter."""

import functools
import random
import time
from collections.abc import Callable
from typing import Any


def retry_with_jitter(
    max_retries: int = 5,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator that retries a function using exponential backoff with full jitter."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    if attempt == max_retries - 1:
                        raise e

                    # Exponential backoff formula: base * 2^attempt
                    calculated_delay = min(max_delay, base_delay * (2**attempt))
                    # Full jitter: uniformly random between 0 and calculated_delay
                    sleep_time = random.uniform(0, calculated_delay)
                    time.sleep(sleep_time)

        return wrapper

    return decorator
