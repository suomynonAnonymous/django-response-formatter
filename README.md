# Django Response Formatter

Standardize all Django REST Framework API responses into a consistent, predictable format.

Every response — success or error — follows this structure:

```json
{
    "status": "success" | "error",
    "message": "Human-readable message",
    "data": { ... } | [ ... ] | null,
    "errors": { ... } | null,
    "metadata": { ... } | null
}
```

## Installation

```bash
pip install dj-response-formatter
```

## Quick Start

**1. Add to `INSTALLED_APPS`:**

```python
INSTALLED_APPS = [
    # ...
    "dj_response_formatter",
]
```

**2. Configure DRF settings:**

```python
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "dj_response_formatter.renderers.FormattedJSONRenderer",
    ],
    "EXCEPTION_HANDLER": "dj_response_formatter.exceptions.format_exception_handler",
}
```

**3. (Optional) Add middleware for non-DRF exception handling:**

```python
MIDDLEWARE = [
    # ... other middleware ...
    "dj_response_formatter.middleware.ResponseFormatterMiddleware",
]
```

That's it. All your API responses are now formatted consistently.

## Response Examples

### Success (2xx)

```python
# View
class UserView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return Response(UserSerializer(user).data)
```

```json
{
    "status": "success",
    "message": "Request was successful.",
    "data": {
        "id": 1,
        "username": "john",
        "email": "john@example.com"
    },
    "errors": null,
    "metadata": null
}
```

### Validation Error (400)

```json
{
    "status": "error",
    "message": "Bad request.",
    "data": null,
    "errors": {
        "email": ["This field is required."],
        "username": ["A user with that username already exists."]
    },
    "metadata": {
        "status_code": 400
    }
}
```

### Not Found (404)

```json
{
    "status": "error",
    "message": "Not found.",
    "data": null,
    "errors": null,
    "metadata": {
        "status_code": 404
    }
}
```

### Paginated Response

DRF pagination metadata is automatically extracted:

```json
{
    "status": "success",
    "message": "Request was successful.",
    "data": [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ],
    "errors": null,
    "metadata": {
        "pagination": {
            "count": 100,
            "next": "http://api.example.com/items/?page=2",
            "previous": null
        }
    }
}
```

## Helper Functions

Use the helper functions for explicit control over response messages:

```python
from dj_response_formatter.helpers import success_response, error_response, raw_response

class UserView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return success_response(
            data=UserSerializer(user).data,
            message="User retrieved successfully.",
        )

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                data=serializer.data,
                message="User created.",
                status_code=201,
            )
        return error_response(
            errors=serializer.errors,
            message="Validation failed.",
            status_code=400,
        )
```

### `success_response(data=None, message=None, status_code=200, headers=None)`

Returns a DRF `Response` that the renderer formats as a success envelope.

### `error_response(errors=None, message=None, status_code=400, headers=None)`

Returns a DRF `Response` that the renderer formats as an error envelope.

### `raw_response(data=None, status_code=200, headers=None)`

Returns a DRF `Response` that **skips formatting entirely**. Use for health checks, webhooks, or any endpoint that must return raw JSON.

## Configuration

Customize behavior via the `RESPONSE_FORMATTER` dict in your Django settings:

```python
RESPONSE_FORMATTER = {
    # Field names in the envelope
    "STATUS_FIELD": "status",
    "MESSAGE_FIELD": "message",
    "DATA_FIELD": "data",
    "ERRORS_FIELD": "errors",
    "METADATA_FIELD": "metadata",

    # Status values
    "SUCCESS_STATUS": "success",
    "ERROR_STATUS": "error",

    # Default messages
    "DEFAULT_SUCCESS_MESSAGE": "Request was successful.",
    "DEFAULT_ERROR_MESSAGE": "An error occurred.",

    # Include fields even when their value is null
    "INCLUDE_NULL_FIELDS": True,

    # Extract pagination info into metadata automatically
    "EXTRACT_PAGINATION": True,

    # Pagination field names to detect
    "PAGINATION_FIELDS": ["count", "next", "previous", "page_size", "total_pages"],
}
```

### Example: Minimal Responses

```python
RESPONSE_FORMATTER = {
    "INCLUDE_NULL_FIELDS": False,
}
```

A success response now omits null fields:

```json
{
    "status": "success",
    "message": "Request was successful.",
    "data": {"id": 1}
}
```

### Example: Custom Field Names

```python
RESPONSE_FORMATTER = {
    "STATUS_FIELD": "ok",
    "DATA_FIELD": "result",
    "SUCCESS_STATUS": True,
    "ERROR_STATUS": False,
}
```

```json
{
    "ok": true,
    "message": "Request was successful.",
    "result": {"id": 1},
    "errors": null,
    "metadata": null
}
```

## Components

| Component | Purpose |
|---|---|
| `FormattedJSONRenderer` | Wraps all DRF responses in the standardized envelope |
| `format_exception_handler` | Normalizes DRF exception data for consistent error formatting |
| `ResponseFormatterMiddleware` | Catches unhandled exceptions outside DRF views (optional) |
| `success_response` / `error_response` / `raw_response` | View helpers for explicit control |

## Requirements

- Python >= 3.9
- Django >= 4.2
- Django REST Framework >= 3.14

## License

MIT
