"""
Utility functions for django_response_formatter.

Provides helper functions for building standardized response envelopes
and reading user configuration from Django settings.
"""

from typing import Any, Optional

from django.conf import settings

# ────────────────────────────────────────────────────────────────────
# Default configuration — users override these via Django settings
# ────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    # Field names in the response envelope
    "STATUS_FIELD": "status",
    "MESSAGE_FIELD": "message",
    "DATA_FIELD": "data",
    "ERRORS_FIELD": "errors",
    "METADATA_FIELD": "metadata",
    # Status values
    "SUCCESS_STATUS": "success",
    "ERROR_STATUS": "error",
    # Default messages when none is provided
    "DEFAULT_SUCCESS_MESSAGE": "Request was successful.",
    "DEFAULT_ERROR_MESSAGE": "An error occurred.",
    # Whether to include null fields in the response
    "INCLUDE_NULL_FIELDS": True,
    # Whether to extract pagination info into metadata
    "EXTRACT_PAGINATION": True,
    # Pagination field names to look for in the response data
    "PAGINATION_FIELDS": ["count", "next", "previous", "page_size", "total_pages"],
}


def get_config() -> dict:
    """
    Retrieve the merged configuration dictionary.

    Merges DEFAULT_CONFIG with any overrides the user has specified in
    their Django settings under the ``RESPONSE_FORMATTER`` key.

    Returns:
        dict: The final configuration dictionary with user overrides
              applied on top of defaults.

    Example::

        # In settings.py
        RESPONSE_FORMATTER = {
            "DEFAULT_SUCCESS_MESSAGE": "OK",
            "INCLUDE_NULL_FIELDS": False,
        }
    """
    user_config = getattr(settings, "RESPONSE_FORMATTER", {})
    # Start with defaults, then overlay user overrides
    merged = {**DEFAULT_CONFIG, **user_config}
    return merged


def build_success_envelope(
    data: Any = None,
    message: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Build a standardized success response envelope.

    Args:
        data: The response payload. Can be a dict, list, or any serializable value.
        message: A human-readable success message. Falls back to the configured default.
        metadata: Optional metadata dict (pagination info, request timing, etc.).

    Returns:
        dict: A response envelope with the structure::

            {
                "status": "success",
                "message": "...",
                "data": ...,
                "errors": null,
                "metadata": {...} or null
            }
    """
    config = get_config()

    envelope = {
        config["STATUS_FIELD"]: config["SUCCESS_STATUS"],
        config["MESSAGE_FIELD"]: message or config["DEFAULT_SUCCESS_MESSAGE"],
        config["DATA_FIELD"]: data,
        config["ERRORS_FIELD"]: None,
        config["METADATA_FIELD"]: metadata,
    }

    # Optionally strip null fields from the response
    if not config["INCLUDE_NULL_FIELDS"]:
        envelope = {k: v for k, v in envelope.items() if v is not None}

    return envelope


def build_error_envelope(
    errors: Any = None,
    message: Optional[str] = None,
    status_code: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Build a standardized error response envelope.

    Args:
        errors: Error details. Can be a dict of field-level errors, a list of
                error strings, or a single error string.
        message: A human-readable error message. Falls back to the configured default.
        status_code: The HTTP status code (included in metadata if provided).
        metadata: Optional additional metadata.

    Returns:
        dict: A response envelope with the structure::

            {
                "status": "error",
                "message": "...",
                "data": null,
                "errors": {...},
                "metadata": {...} or null
            }
    """
    config = get_config()

    # Build metadata, including the status code if provided
    meta = metadata or {}
    if status_code is not None:
        meta["status_code"] = status_code
    # Only include metadata if there's something in it
    final_metadata = meta if meta else None

    envelope = {
        config["STATUS_FIELD"]: config["ERROR_STATUS"],
        config["MESSAGE_FIELD"]: message or config["DEFAULT_ERROR_MESSAGE"],
        config["DATA_FIELD"]: None,
        config["ERRORS_FIELD"]: errors,
        config["METADATA_FIELD"]: final_metadata,
    }

    # Optionally strip null fields from the response
    if not config["INCLUDE_NULL_FIELDS"]:
        envelope = {k: v for k, v in envelope.items() if v is not None}

    return envelope


def extract_pagination_metadata(data: dict) -> tuple[dict, Optional[dict]]:
    """
    Extract pagination fields from a paginated DRF response.

    DRF's default pagination wraps results like this::

        {
            "count": 100,
            "next": "http://api.example.com/items/?page=2",
            "previous": null,
            "results": [...]
        }

    This function pulls the pagination fields into a separate metadata dict
    and returns just the ``results`` list as the data.

    Args:
        data: The original response data dict from a paginated DRF response.

    Returns:
        tuple: A 2-tuple of (cleaned_data, pagination_metadata).
               - cleaned_data: The ``results`` list (or original data if not paginated).
               - pagination_metadata: Dict of pagination fields, or None if not paginated.
    """
    config = get_config()
    pagination_fields = config["PAGINATION_FIELDS"]

    # Check if this looks like a paginated response (has 'results' key and
    # at least one recognized pagination field)
    if not isinstance(data, dict):
        return data, None

    has_results = "results" in data
    has_pagination = any(field in data for field in pagination_fields)

    if not (has_results and has_pagination):
        return data, None

    # Extract pagination metadata
    pagination_meta = {}
    for field in pagination_fields:
        if field in data:
            pagination_meta[field] = data[field]

    # Return the results list as data, pagination info as metadata
    return data["results"], pagination_meta
