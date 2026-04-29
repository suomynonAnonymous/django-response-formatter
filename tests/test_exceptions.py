"""Tests for the custom exception handler."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


class TestExceptionHandler:
    """Test the format_exception_handler function."""

    def test_non_drf_exception_returns_none(self):
        """Non-DRF exceptions should return None (middleware handles them)."""
        from unittest.mock import MagicMock

        from dj_response_formatter.exceptions import format_exception_handler

        exc = RuntimeError("boom")
        context = {"view": MagicMock(), "request": MagicMock()}
        result = format_exception_handler(exc, context)
        assert result is None

    def test_normalize_list_data(self):
        """List error data should be normalized to non_field_errors dict."""
        from dj_response_formatter.exceptions import _normalize_error_data

        result = _normalize_error_data(["error1", "error2"], ValueError("test"))
        assert result == {"non_field_errors": ["error1", "error2"]}

    def test_normalize_string_data(self):
        """String error data should be normalized to detail dict."""
        from dj_response_formatter.exceptions import _normalize_error_data

        result = _normalize_error_data("Something went wrong", ValueError("test"))
        assert result == {"detail": "Something went wrong"}

    def test_normalize_dict_data(self):
        """Dict error data should pass through unchanged."""
        from dj_response_formatter.exceptions import _normalize_error_data

        data = {"field": ["error"]}
        result = _normalize_error_data(data, ValueError("test"))
        assert result == {"field": ["error"]}

    def test_normalize_fallback(self):
        """Unexpected data types should use exc string as detail."""
        from dj_response_formatter.exceptions import _normalize_error_data

        result = _normalize_error_data(12345, ValueError("fallback value"))
        assert result == {"detail": "fallback value"}

    def test_throttled_has_retry_after(self, client):
        """Throttled exceptions should include Retry-After header and metadata."""
        response = client.get("/api/throttled/")
        assert response.status_code == 429
        assert response["Retry-After"] == "30"

    def test_server_error_returns_none(self):
        """Non-DRF exceptions should return None from the handler."""
        from unittest.mock import MagicMock

        from dj_response_formatter.exceptions import format_exception_handler

        # RuntimeError is not an APIException, so handler returns None
        exc = RuntimeError("Something unexpected happened")
        context = {"view": MagicMock(), "request": MagicMock()}
        result = format_exception_handler(exc, context)
        assert result is None
