"""
Helper functions for views to set custom messages and skip formatting.

These helpers give view authors control over the response envelope without
having to manually construct the entire response.

Usage::

    from rest_framework.response import Response
    from rest_framework.views import APIView
    from django_response_formatter.helpers import success_response, error_response

    class UserView(APIView):
        def get(self, request, pk):
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(user)
            return success_response(
                data=serializer.data,
                message="User retrieved successfully."
            )

        def post(self, request):
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return success_response(
                    data=serializer.data,
                    message="User created successfully.",
                    status_code=201,
                )
            return error_response(
                errors=serializer.errors,
                message="Validation failed.",
                status_code=400,
            )
"""

from typing import Any, Optional

from rest_framework.response import Response


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200,
    headers: Optional[dict] = None,
) -> Response:
    """
    Create a DRF Response that the renderer will format as a success envelope.

    The message is attached to the response object so the renderer can extract
    it without modifying the data payload.

    Args:
        data: The response payload (dict, list, or any serializable value).
        message: A custom success message. If not provided, the renderer uses
                 the configured default.
        status_code: HTTP status code (default 200).
        headers: Optional dict of extra HTTP headers.

    Returns:
        Response: A DRF Response with the custom message attached.
    """
    response = Response(data=data, status=status_code, headers=headers)
    if message:
        response._formatter_message = message
    return response


def error_response(
    errors: Any = None,
    message: Optional[str] = None,
    status_code: int = 400,
    headers: Optional[dict] = None,
) -> Response:
    """
    Create a DRF Response that the renderer will format as an error envelope.

    Args:
        errors: Error details (dict of field errors, list, or string).
        message: A custom error message. If not provided, the renderer infers
                 one from the status code.
        status_code: HTTP status code (default 400).
        headers: Optional dict of extra HTTP headers.

    Returns:
        Response: A DRF Response with the custom message attached.
    """
    response = Response(data=errors, status=status_code, headers=headers)
    if message:
        response._formatter_message = message
    return response


def raw_response(
    data: Any = None,
    status_code: int = 200,
    headers: Optional[dict] = None,
) -> Response:
    """
    Create a DRF Response that skips the formatting envelope entirely.

    Use this when you need to return raw JSON without the standardized wrapper.
    For example, health check endpoints or third-party webhook responses that
    must match an exact schema.

    Args:
        data: The response payload (returned as-is, no envelope).
        status_code: HTTP status code (default 200).
        headers: Optional dict of extra HTTP headers.

    Returns:
        Response: A DRF Response marked to skip formatting.
    """
    response = Response(data=data, status=status_code, headers=headers)
    response._skip_formatting = True
    return response
