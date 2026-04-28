"""
Django Response Formatter
=========================

Standardize all Django REST Framework API responses into a consistent,
predictable format.

Every response — success or error — follows this structure:

    {
        "status": "success" | "error",
        "message": "Human-readable message",
        "data": { ... } | [ ... ] | null,
        "errors": { ... } | null,
        "metadata": { "page": 1, "total": 100, ... } | null
    }

Quick Start:
    1. Add 'dj_response_formatter' to INSTALLED_APPS
    2. Set the renderer in REST_FRAMEWORK settings
    3. Optionally add the middleware for non-DRF exception handling

See README.md for full documentation.
"""

__version__ = "0.1.2"

from .exceptions import format_exception_handler
from .renderers import FormattedJSONRenderer

__all__ = [
    "__version__",
    "FormattedJSONRenderer",
    "format_exception_handler",
]

# Default app config for Django
default_app_config = "dj_response_formatter.apps.DjangoResponseFormatterConfig"
