"""
Custom DRF renderers that wrap responses in a standardized envelope.

Usage:
    Add to your DRF settings::

        REST_FRAMEWORK = {
            "DEFAULT_RENDERER_CLASSES": [
                "dj_response_formatter.renderers.FormattedJSONRenderer",
            ],
        }

    Or use per-view::

        from dj_response_formatter.renderers import FormattedJSONRenderer

        class MyView(APIView):
            renderer_classes = [FormattedJSONRenderer]
"""

from typing import Any, Optional

from rest_framework.renderers import JSONRenderer

from .utils import (
    build_error_envelope,
    build_success_envelope,
    extract_pagination_metadata,
    get_config,
)


class FormattedJSONRenderer(JSONRenderer):
    """
    A DRF JSON renderer that wraps all responses in a consistent envelope.

    Success responses (2xx)::

        {
            "status": "success",
            "message": "Request was successful.",
            "data": { ... },
            "errors": null,
            "metadata": null
        }

    Error responses (4xx, 5xx)::

        {
            "status": "error",
            "message": "Validation failed.",
            "data": null,
            "errors": {"field": ["error message"]},
            "metadata": {"status_code": 400}
        }

    The renderer inspects the response status code to determine whether to
    format as a success or error envelope. It also extracts pagination
    metadata from paginated DRF responses when configured to do so.

    Attributes:
        media_type: The media type this renderer handles (application/json).
        format: The format suffix for this renderer (json).
    """

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Optional[dict] = None,
    ) -> bytes:
        """
        Render the response data into a standardized JSON envelope.

        This method intercepts the normal DRF rendering pipeline, wraps the
        data in the appropriate envelope (success or error), and then delegates
        to the parent ``JSONRenderer.render()`` for actual JSON serialization.

        Args:
            data: The serialized response data from the view/serializer.
            accepted_media_type: The media type accepted by the client.
            renderer_context: Dict containing 'response', 'request', 'view', etc.

        Returns:
            bytes: The JSON-encoded response body.
        """
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")

        # If there's no response object, just render the data as-is.
        # This can happen when rendering outside of a request cycle.
        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        status_code = response.status_code

        # Check if this response was explicitly marked to skip formatting.
        # Views can set response["X-Skip-Formatting"] = "true" to bypass.
        if getattr(response, "_skip_formatting", False):
            return super().render(data, accepted_media_type, renderer_context)

        # Determine if this is a success or error response
        if 200 <= status_code < 300:
            envelope = self._build_success(data, response)
        else:
            envelope = self._build_error(data, status_code, response)

        return super().render(envelope, accepted_media_type, renderer_context)

    def _build_success(self, data: Any, response: Any) -> dict:
        """
        Build a success envelope from the response data.

        Handles pagination extraction if the response came from a paginated
        endpoint and the ``EXTRACT_PAGINATION`` config is enabled.

        Args:
            data: The serialized response data.
            response: The DRF Response object.

        Returns:
            dict: The success envelope.
        """
        config = get_config()
        metadata = None

        # Extract pagination metadata if configured and applicable
        if config["EXTRACT_PAGINATION"] and isinstance(data, dict):
            data, pagination_meta = extract_pagination_metadata(data)
            if pagination_meta:
                metadata = {"pagination": pagination_meta}

        # Check for a custom message set on the response
        message = getattr(response, "_formatter_message", None)

        return build_success_envelope(data=data, message=message, metadata=metadata)

    def _build_error(self, data: Any, status_code: int, response: Any) -> dict:
        """
        Build an error envelope from the response data and status code.

        Extracts error details from common DRF error formats:
        - ``{"detail": "Not found."}`` → uses detail as message
        - ``{"field": ["error"]}`` → uses as field-level errors
        - ``["error1", "error2"]`` → uses as non-field errors

        Args:
            data: The serialized error data.
            status_code: The HTTP status code.
            response: The DRF Response object.

        Returns:
            dict: The error envelope.
        """
        # Try to extract a meaningful message from the error data
        message = getattr(response, "_formatter_message", None)
        errors = data
        metadata = None

        if isinstance(data, dict):
            # Extract _retry_after metadata injected by exception handler
            retry_after = data.pop("_retry_after", None)
            if retry_after is not None:
                metadata = {"retry_after": retry_after}

            # DRF often puts the main message in "detail"
            if "detail" in data:
                message = message or str(data["detail"])
                # If "detail" is the only key, errors is just the message string
                if len(data) == 1:
                    errors = None
                else:
                    # Remove "detail" from errors since it's now the message
                    errors = {k: v for k, v in data.items() if k != "detail"}
            elif not message:
                # Multiple field errors — use a generic message
                message = self._infer_error_message(status_code)
        elif isinstance(data, list):
            # List of error strings
            if not message:
                message = self._infer_error_message(status_code)
            errors = {"non_field_errors": data}
        elif isinstance(data, str):
            message = message or data
            errors = None

        return build_error_envelope(
            errors=errors,
            message=message,
            status_code=status_code,
            metadata=metadata,
        )

    @staticmethod
    def _infer_error_message(status_code: int) -> str:
        """
        Return a human-readable error message based on the HTTP status code.

        Uses built-in defaults, merged with any custom overrides from the
        ``STATUS_CODE_MESSAGES`` config.

        Args:
            status_code: The HTTP status code.

        Returns:
            str: A descriptive error message.
        """
        builtin_messages = {
            400: "Bad request.",
            401: "Authentication credentials were not provided or are invalid.",
            403: "You do not have permission to perform this action.",
            404: "The requested resource was not found.",
            405: "Method not allowed.",
            406: "Not acceptable.",
            409: "Conflict.",
            415: "Unsupported media type.",
            422: "Unprocessable entity.",
            429: "Too many requests. Please try again later.",
            500: "An internal server error occurred.",
            502: "Bad gateway.",
            503: "Service temporarily unavailable.",
        }
        config = get_config()
        custom = config.get("STATUS_CODE_MESSAGES", {})
        messages = {**builtin_messages, **custom}
        return messages.get(status_code, f"An error occurred (HTTP {status_code}).")
