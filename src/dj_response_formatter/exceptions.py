"""
Custom DRF exception handler that formats errors consistently.

Usage:
    Add to your DRF settings::

        REST_FRAMEWORK = {
            "EXCEPTION_HANDLER": "dj_response_formatter.exceptions.format_exception_handler",
        }

    This replaces DRF's default exception handler. The custom handler ensures
    all DRF-caught exceptions produce responses that the FormattedJSONRenderer
    can wrap into a consistent envelope.
"""

from typing import Any, Optional

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def format_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    """
    Custom exception handler that ensures all errors are formatted consistently.

    This handler extends DRF's default ``exception_handler`` by:

    1. Normalizing all error data into a dict with a ``detail`` or field-level structure.
    2. Converting Django's ``Http404`` into a DRF-style response.
    3. Handling ``ValidationError`` with both field-level and non-field errors.

    The resulting response is then processed by ``FormattedJSONRenderer`` to produce
    the final standardized envelope.

    Args:
        exc: The exception that was raised.
        context: Dict containing ``view``, ``args``, ``kwargs``, and ``request``.

    Returns:
        Response or None: A DRF Response with error data, or None if the exception
                         is not a type that DRF handles (e.g., unhandled server errors).
                         When None is returned, Django's default 500 handling takes over.
    """
    # Let DRF handle the exception first — this covers APIException subclasses,
    # Http404, and PermissionDenied
    response = drf_exception_handler(exc, context)

    if response is not None:
        # DRF handled it — normalize the error data structure
        response.data = _normalize_error_data(response.data, exc)

        # Include Retry-After for throttled responses
        if hasattr(exc, "wait") and exc.wait:
            response["Retry-After"] = str(int(exc.wait))
            response.data["_retry_after"] = exc.wait

        return response

    # DRF did not handle the exception (it's not an APIException).
    # Return None to let Django's default error handling take over.
    # The ResponseFormatterMiddleware will catch these if installed.
    return None


def _normalize_error_data(data: Any, exc: Exception) -> dict:
    """
    Normalize DRF error data into a consistent dict format.

    DRF can return errors in various formats depending on the exception type:
    - ``{"detail": "Not found."}`` — from NotFound, PermissionDenied, etc.
    - ``{"field_name": ["Error message."]}`` — from ValidationError with field errors
    - ``["Error message."]`` — from ValidationError with non-field errors
    - ``"Error message."`` — from ValidationError with a single string

    This function normalizes all of these into a predictable dict.

    Args:
        data: The raw error data from DRF's exception handler.
        exc: The original exception.

    Returns:
        dict: Normalized error data.
    """
    if isinstance(data, dict):
        # Already a dict — this is the most common case.
        # DRF returns {"detail": "..."} or {"field": ["error"]}
        return data

    if isinstance(data, list):
        # Non-field errors from ValidationError
        # Turn ["error1", "error2"] into {"non_field_errors": ["error1", "error2"]}
        return {"non_field_errors": data}

    if isinstance(data, str):
        # Single string error
        return {"detail": data}

    # Fallback — shouldn't normally happen, but be safe
    return {"detail": str(exc)}
