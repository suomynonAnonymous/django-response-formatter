"""Tests for the helper functions."""

from django_response_formatter.helpers import error_response, raw_response, success_response


class TestSuccessResponse:
    """Test the success_response helper."""

    def test_default_status_code(self):
        response = success_response(data={"id": 1})
        assert response.status_code == 200
        assert response.data == {"id": 1}

    def test_custom_status_code(self):
        response = success_response(data={"id": 1}, status_code=201)
        assert response.status_code == 201

    def test_custom_message_attached(self):
        response = success_response(data=None, message="Created.")
        assert response._formatter_message == "Created."

    def test_no_message_no_attribute(self):
        response = success_response(data=None)
        assert not hasattr(response, "_formatter_message")

    def test_headers(self):
        response = success_response(data=None, headers={"X-Custom": "value"})
        assert response["X-Custom"] == "value"


class TestErrorResponse:
    """Test the error_response helper."""

    def test_default_status_code(self):
        response = error_response(errors={"field": ["err"]})
        assert response.status_code == 400

    def test_custom_status_code(self):
        response = error_response(errors=None, status_code=422)
        assert response.status_code == 422

    def test_custom_message_attached(self):
        response = error_response(message="Validation failed.")
        assert response._formatter_message == "Validation failed."

    def test_errors_as_data(self):
        response = error_response(errors={"email": ["required"]})
        assert response.data == {"email": ["required"]}


class TestRawResponse:
    """Test the raw_response helper."""

    def test_skip_flag_set(self):
        response = raw_response(data={"raw": True})
        assert response._skip_formatting is True

    def test_default_status(self):
        response = raw_response(data=None)
        assert response.status_code == 200

    def test_custom_status(self):
        response = raw_response(data=None, status_code=204)
        assert response.status_code == 204
