"""Tests for batch retry handler module."""

import pytest
import time
from unittest.mock import MagicMock, patch

from batch.retry_handler import (
    retry_with_backoff,
    retry_with_callback,
    RetryError,
    RetryContext,
    DEFAULT_MAX_RETRIES,
    DEFAULT_INITIAL_DELAY,
)


class TestRetryWithBackoff:
    """Test cases for retry_with_backoff decorator."""

    def test_successful_call_no_retry(self):
        """Test successful function call without retry."""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure_then_success(self):
        """Test retry on failure then success."""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = fail_then_succeed()

        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Test that RetryError is raised after max retries."""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            always_fail()

        assert "Max retries (2) exceeded" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries
        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_specific_exception_types(self):
        """Test retry only on specific exception types."""
        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.01,
            exceptions=(ValueError,),
        )
        def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Not a ValueError")

        with pytest.raises(TypeError):
            raise_type_error()

        assert call_count == 1  # No retry for TypeError

    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_callbacks = []

        def on_retry_callback(exc, attempt, delay):
            retry_callbacks.append((str(exc), attempt, delay))

        @retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            on_retry=on_retry_callback,
        )
        def fail_twice():
            if len(retry_callbacks) < 2:
                raise ValueError("Fail")
            return "success"

        result = fail_twice()

        assert result == "success"
        assert len(retry_callbacks) == 2
        assert retry_callbacks[0][1] == 1  # First retry attempt
        assert retry_callbacks[1][1] == 2  # Second retry attempt


class TestRetryWithCallback:
    """Test cases for retry_with_callback function."""

    def test_successful_call_with_success_callback(self):
        """Test success callback is called on success."""
        success_result = []

        def on_success(result):
            success_result.append(result)

        result = retry_with_callback(
            func=lambda: "success",
            max_retries=3,
            initial_delay=0.01,
            on_success=on_success,
        )

        assert result == "success"
        assert success_result == ["success"]

    def test_failure_callback_on_max_retries(self):
        """Test failure callback is called after max retries."""
        failure_exceptions = []

        def on_failure(exc):
            failure_exceptions.append(exc)

        with pytest.raises(RetryError):
            retry_with_callback(
                func=lambda: (_ for _ in ()).throw(ValueError("fail")),
                max_retries=2,
                initial_delay=0.01,
                on_failure=on_failure,
            )

        assert len(failure_exceptions) == 1
        assert isinstance(failure_exceptions[0], ValueError)


class TestRetryContext:
    """Test cases for RetryContext class."""

    def test_successful_first_attempt(self):
        """Test successful first attempt."""
        with RetryContext(max_retries=3) as ctx:
            attempts = 0
            while ctx.should_retry():
                attempts += 1
                try:
                    result = "success"
                    ctx.success()
                except Exception as e:
                    ctx.failed(e)

        assert attempts == 1
        assert ctx.attempts == 0  # No failed attempts

    @patch("time.sleep")
    def test_retry_then_success(self, mock_sleep):
        """Test retry then success."""
        with RetryContext(max_retries=3, initial_delay=0.01) as ctx:
            attempts = 0
            while ctx.should_retry():
                attempts += 1
                try:
                    if attempts < 3:
                        raise ValueError("Temporary failure")
                    ctx.success()
                except Exception as e:
                    ctx.failed(e)

        assert attempts == 3
        assert ctx.attempts == 2  # 2 failed attempts

    @patch("time.sleep")
    def test_max_retries_exceeded_raises(self, mock_sleep):
        """Test RetryError is raised after max retries."""
        with pytest.raises(RetryError):
            with RetryContext(max_retries=2, initial_delay=0.01) as ctx:
                while ctx.should_retry():
                    try:
                        raise ValueError("Always fails")
                    except Exception as e:
                        ctx.failed(e)

    def test_last_exception_property(self):
        """Test last_exception property."""
        with RetryContext(max_retries=1, initial_delay=0.001) as ctx:
            while ctx.should_retry():
                try:
                    raise ValueError("Test error")
                except Exception as e:
                    ctx.failed(e)
                    break

        assert ctx.last_exception is not None
        assert isinstance(ctx.last_exception, ValueError)


class TestRetryError:
    """Test cases for RetryError exception."""

    def test_retry_error_message(self):
        """Test RetryError message."""
        error = RetryError("Test message")
        assert str(error) == "Test message"

    def test_retry_error_with_last_exception(self):
        """Test RetryError with last_exception."""
        original = ValueError("Original error")
        error = RetryError("Test message", last_exception=original)

        assert error.last_exception is original
        assert str(error.last_exception) == "Original error"
