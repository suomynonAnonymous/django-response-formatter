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
