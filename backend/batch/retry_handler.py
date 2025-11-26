"""Retry handler with exponential backoff.

This module provides decorators and utilities for retrying failed operations
with configurable backoff strategies.
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 60  # 1 minute
DEFAULT_MAX_DELAY = 3600  # 1 hour
DEFAULT_BACKOFF_FACTOR = 2.0


class RetryError(Exception):
    """Exception raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Callable:
    """Decorator for retrying a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called before each retry
                 Receives (exception, attempt_number, delay)

    Returns:
        Decorated function

    Example:
        @retry_with_backoff(max_retries=3, initial_delay=60)
        def sync_jira():
            # ... sync logic
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Last error: {e}"
                        )
                        raise RetryError(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}",
                            last_exception=e,
                        )

                    # Calculate next delay
                    current_delay = min(delay, max_delay)

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {current_delay:.0f} seconds..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1, current_delay)

                    # Wait before retry
                    time.sleep(current_delay)

                    # Increase delay for next retry
                    delay *= backoff_factor

            # This should never be reached
            raise RetryError(
                f"Unexpected retry loop exit for {func.__name__}",
                last_exception=last_exception,
            )

        return wrapper
    return decorator


def retry_with_callback(
    func: Callable,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_success: Optional[Callable[[Any], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Any:
    """Execute a function with retry logic and callbacks.

    Unlike the decorator, this function allows passing callbacks for
    success and failure handling.

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exception types to catch and retry
        on_success: Callback function called on success with the result
        on_failure: Callback function called on final failure with the exception
        on_retry: Callback function called before each retry

    Returns:
        Result of the function if successful

    Raises:
        RetryError: If all retry attempts fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            result = func()

            if on_success:
                on_success(result)

            return result

        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"Function failed after {max_retries + 1} attempts. "
                    f"Last error: {e}"
                )

                if on_failure:
                    on_failure(e)

                raise RetryError(
                    f"Max retries ({max_retries}) exceeded",
                    last_exception=e,
                )

            current_delay = min(delay, max_delay)

            logger.warning(
                f"Function failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                f"Retrying in {current_delay:.0f} seconds..."
            )

            if on_retry:
                on_retry(e, attempt + 1, current_delay)

            time.sleep(current_delay)
            delay *= backoff_factor

    raise RetryError("Unexpected retry loop exit", last_exception=last_exception)


class RetryContext:
    """Context manager for retry logic.

    Example:
        with RetryContext(max_retries=3) as ctx:
            while ctx.should_retry():
                try:
                    result = sync_jira()
                    ctx.success()
                except Exception as e:
                    ctx.failed(e)
    """

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

        self._attempt = 0
        self._delay = initial_delay
        self._succeeded = False
        self._last_exception: Optional[Exception] = None

    def __enter__(self) -> "RetryContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def should_retry(self) -> bool:
        """Check if another retry attempt should be made."""
        if self._succeeded:
            return False

        if self._attempt > self.max_retries:
            if self._last_exception:
                raise RetryError(
                    f"Max retries ({self.max_retries}) exceeded",
                    last_exception=self._last_exception,
                )
            return False

        return True

    def success(self) -> None:
        """Mark the operation as successful."""
        self._succeeded = True
        logger.debug(f"Operation succeeded on attempt {self._attempt + 1}")

    def failed(self, exception: Exception) -> None:
        """Mark the current attempt as failed.

        Args:
            exception: The exception that caused the failure
        """
        self._last_exception = exception
        self._attempt += 1

        if self._attempt <= self.max_retries:
            current_delay = min(self._delay, self.max_delay)

            logger.warning(
                f"Attempt {self._attempt}/{self.max_retries + 1} failed: {exception}. "
                f"Retrying in {current_delay:.0f} seconds..."
            )

            time.sleep(current_delay)
            self._delay *= self.backoff_factor

    @property
    def attempts(self) -> int:
        """Get the number of attempts made."""
        return self._attempt

    @property
    def last_exception(self) -> Optional[Exception]:
        """Get the last exception that occurred."""
        return self._last_exception
