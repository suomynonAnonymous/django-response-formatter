"""Tests for the FormattedJSONRenderer."""

import pytest
from django.test import RequestFactory
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def rf():
    return RequestFactory()


class TestSuccessResponses:
    """Test that success responses (2xx) are correctly formatted."""

    def test_basic_success(self, client):
        response = client.get("/api/success/")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["message"] == "Request was successful."
        assert data["data"] == {"id": 1, "name": "Test"}
        assert data["errors"] is None
        assert data["metadata"] is None

    def test_success_with_custom_message(self, client):
        response = client.get("/api/success-message/")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["message"] == "Custom success message."
        assert data["data"] == {"id": 1}

    def test_created_response(self, client):
        response = client.post("/api/created/", data={}, format="json")
        data = response.json()

        assert response.status_code == 201
        assert data["status"] == "success"
        assert data["data"] == {"id": 1, "name": "New"}

    def test_list_response(self, client):
        response = client.get("/api/list/")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["data"] == [{"id": 1}, {"id": 2}]

    def test_no_content_response(self, client):
        response = client.get("/api/empty/")
        # 204 responses have no body
        assert response.status_code == 204


class TestPagination:
    """Test pagination metadata extraction."""

    def test_paginated_response(self, client):
        response = client.get("/api/paginated/")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "success"
        # Pagination should be extracted — data is just the results list
        assert data["data"] == [{"id": 1}, {"id": 2}]
        assert data["metadata"] == {
            "pagination": {
                "count": 100,
                "next": "http://testserver/api/paginated/?page=2",
                "previous": None,
            }
        }

    def test_pagination_disabled(self, client, settings):
        settings.RESPONSE_FORMATTER = {"EXTRACT_PAGINATION": False}
        response = client.get("/api/paginated/")
        data = response.json()

        # With pagination extraction disabled, data should be the full dict
        assert data["status"] == "success"
        assert "results" in data["data"]
        assert "count" in data["data"]


class TestRawResponse:
    """Test that raw_response skips formatting."""

    def test_raw_response_bypasses_formatting(self, client):
        response = client.get("/api/raw/")
        data = response.json()

        assert response.status_code == 200
        # Should be raw data, no envelope
        assert data == {"healthy": True}
        assert "status" not in data
        assert "message" not in data


class TestErrorResponses:
    """Test that error responses are correctly formatted."""

    def test_validation_error(self, client):
        response = client.post("/api/validation-error/", data={}, format="json")
        data = response.json()

        assert response.status_code == 400
        assert data["status"] == "error"
        assert data["errors"]["email"] == ["This field is required."]
        assert data["errors"]["username"] == ["A user with that username already exists."]
        assert data["metadata"]["status_code"] == 400

    def test_not_found(self, client):
        response = client.get("/api/not-found/")
        data = response.json()

        assert response.status_code == 404
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()

    def test_permission_denied(self, client):
        response = client.get("/api/permission-denied/")
        data = response.json()

        assert response.status_code == 403
        assert data["status"] == "error"

    def test_unauthorized(self, client):
        response = client.get("/api/unauthorized/")
        data = response.json()

        assert response.status_code == 403
        assert data["status"] == "error"

    def test_throttled(self, client):
        response = client.get("/api/throttled/")
        data = response.json()

        assert response.status_code == 429
        assert data["status"] == "error"


class TestHelperResponses:
    """Test views using the helper functions."""

    def test_helper_success(self, client):
        response = client.get("/api/helper-success/")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["message"] == "User retrieved."
        assert data["data"] == {"id": 1, "name": "Test"}

    def test_helper_error(self, client):
        response = client.post("/api/helper-error/", data={}, format="json")
        data = response.json()

        assert response.status_code == 400
        assert data["status"] == "error"
        assert data["message"] == "Validation failed."
        assert data["errors"]["email"] == ["Invalid email."]


class TestThrottleRetryAfter:
    """Test that throttled responses include retry_after metadata."""

    def test_throttle_includes_retry_after(self, client):
        response = client.get("/api/throttled/")
        data = response.json()

        assert response.status_code == 429
        assert data["status"] == "error"
        # retry_after should be in metadata
        assert data["metadata"]["retry_after"] == 30
        # Retry-After header should be set
        assert response["Retry-After"] == "30"


class TestCustomStatusCodeMessages:
    """Test configurable status code messages."""

    def test_custom_status_code_messages(self, client, settings):
        settings.RESPONSE_FORMATTER = {
            "STATUS_CODE_MESSAGES": {
                400: "Oops, bad request!",
                404: "Nothing here, sorry.",
            }
        }
        response = client.post("/api/validation-error/", data={}, format="json")
        data = response.json()

        assert response.status_code == 400
        assert data["message"] == "Oops, bad request!"

    def test_custom_messages_dont_override_detail(self, client, settings):
        """If DRF provides a 'detail' message, it should still be used."""
        settings.RESPONSE_FORMATTER = {
            "STATUS_CODE_MESSAGES": {
                404: "Custom not found.",
            }
        }
        response = client.get("/api/not-found/")
        data = response.json()

        # DRF's NotFound has a 'detail' which takes priority
        assert response.status_code == 404
        assert "not found" in data["message"].lower()


class TestRendererEdgeCases:
    """Test edge cases for renderer coverage."""

    def test_no_response_object(self):
        """When there's no response object, data is rendered as-is."""
        import json

        from dj_response_formatter.renderers import FormattedJSONRenderer

        renderer = FormattedJSONRenderer()
        result = renderer.render({"key": "value"}, renderer_context={})
        assert json.loads(result) == {"key": "value"}

    def test_list_error_data_direct(self):
        """List error data should be wrapped in non_field_errors."""
        import json
        from unittest.mock import MagicMock

        from dj_response_formatter.renderers import FormattedJSONRenderer

        renderer = FormattedJSONRenderer()
        response = MagicMock()
        response.status_code = 400
        response._skip_formatting = False
        del response._formatter_message  # getattr returns default

        result = renderer.render(
            ["Error 1", "Error 2"],
            renderer_context={"response": response},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["errors"]["non_field_errors"] == ["Error 1", "Error 2"]

    def test_string_error_data_direct(self):
        """String error data should become the message."""
        import json
        from unittest.mock import MagicMock

        from dj_response_formatter.renderers import FormattedJSONRenderer

        renderer = FormattedJSONRenderer()
        response = MagicMock()
        response.status_code = 400
        response._skip_formatting = False
        del response._formatter_message

        result = renderer.render(
            "Something went wrong",
            renderer_context={"response": response},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["message"] == "Something went wrong"
        assert parsed["errors"] is None

    def test_detail_with_extra_fields(self):
        """Dict with 'detail' and other fields should separate them."""
        import json
        from unittest.mock import MagicMock

        from dj_response_formatter.renderers import FormattedJSONRenderer

        renderer = FormattedJSONRenderer()
        response = MagicMock()
        response.status_code = 403
        response._skip_formatting = False
        del response._formatter_message

        result = renderer.render(
            {"detail": "Forbidden", "code": "permission_denied"},
            renderer_context={"response": response},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert parsed["message"] == "Forbidden"
        assert parsed["errors"] == {"code": "permission_denied"}
