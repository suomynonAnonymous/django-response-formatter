"""
Middleware for catching unhandled exceptions outside DRF views.

DRF's exception handling only catches exceptions raised within DRF views.
If an exception occurs in middleware, template views, or other non-DRF code,
it won't be caught by DRF's exception handler.

This middleware provides a safety net that catches ANY unhandled exception
and returns a formatted JSON error response, ensuring consistent error
formatting across your entire application.

Usage:
    Add to your Django middleware stack::

        MIDDLEWARE = [
            # ... other middleware ...
            "django_response_formatter.middleware.ResponseFormatterMiddleware",
        ]

    Place it near the end of the middleware list so it can catch exceptions
    from all middleware above it.
"""

import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

from .utils import build_error_envelope, get_config

logger = logging.getLogger("django_response_formatter")


class ResponseFormatterMiddleware:
    """
    Middleware that catches unhandled exceptions and returns formatted JSON errors.

    This middleware acts as a safety net for exceptions that escape DRF's
    exception handler. It ensures that even unexpected server errors produce
    a consistent JSON response envelope.

    The middleware only activates for requests that expect JSON responses
    (determined by the ``Accept`` header or the URL path). This prevents it
    from interfering with Django's admin, template views, or other HTML-serving
    endpoints.

    Attributes:
        get_response: The next middleware or view in the chain.
    """

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view callable in the chain.
                         This is standard Django middleware protocol.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request/response cycle.

        Wraps the call to the next middleware/view in a try/except to catch
        any unhandled exceptions. If an exception occurs and the request
        expects JSON, returns a formatted error response.

        Args:
            request: The incoming HTTP request.

        Returns:
            HttpResponse: The response, either from the view or a formatted
                         error response if an exception was caught.
        """
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            # Only format as JSON if the client expects JSON
            if self._expects_json(request):
                return self._handle_exception(request, exc)
            # Re-raise for non-JSON requests so Django's default error
            # handling (HTML error pages) still works
            raise

    def _expects_json(self, request: HttpRequest) -> bool:
        """
        Determine if the request expects a JSON response.

        Checks the ``Accept`` header and ``Content-Type`` header for JSON
        media types. Also checks if the URL starts with ``/api/`` as a
        common convention.

        Args:
            request: The incoming HTTP request.

        Returns:
            bool: True if the request likely expects JSON.
        """
        accept = request.META.get("HTTP_ACCEPT", "")
        content_type = request.META.get("CONTENT_TYPE", "")

        # Check Accept header for JSON
        if "application/json" in accept:
            return True

        # Check Content-Type for JSON (API requests typically send JSON)
        if "application/json" in content_type:
            return True

        # Common convention: /api/ prefix indicates an API endpoint
        if request.path.startswith("/api/"):
            return True

        return False

    def _handle_exception(self, request: HttpRequest, exc: Exception) -> JsonResponse:
        """
        Format an unhandled exception into a JSON error response.

        Logs the full traceback for debugging, then returns a clean error
        envelope to the client without exposing internal details.

        Args:
            request: The incoming HTTP request.
            exc: The unhandled exception.

        Returns:
            JsonResponse: A 500 error response with the standardized envelope format.
        """
        # Log the full exception for debugging
        logger.exception(
            "Unhandled exception caught by ResponseFormatterMiddleware: %s",
            str(exc),
        )

        get_config()

        # Build the error envelope — do NOT expose exception details to the client
        envelope = build_error_envelope(
            message="An internal server error occurred.",
            status_code=500,
        )

        return JsonResponse(envelope, status=500)
