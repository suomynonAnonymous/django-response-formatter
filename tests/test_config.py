"""Tests for custom configuration options applied end-to-end."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


class TestCustomConfig:
    """Test that RESPONSE_FORMATTER settings are respected end-to-end."""

    def test_custom_field_names(self, client, settings):
        settings.RESPONSE_FORMATTER = {
            "STATUS_FIELD": "ok",
            "DATA_FIELD": "result",
            "SUCCESS_STATUS": True,
            "ERROR_STATUS": False,
        }
        response = client.get("/api/success/")
        data = response.json()

        assert data["ok"] is True
        assert data["result"] == {"id": 1, "name": "Test"}
        assert "status" not in data
        assert "data" not in data

    def test_custom_messages(self, client, settings):
        settings.RESPONSE_FORMATTER = {
            "DEFAULT_SUCCESS_MESSAGE": "All good!",
        }
        response = client.get("/api/success/")
        data = response.json()

        assert data["message"] == "All good!"

    def test_null_fields_excluded(self, client, settings):
        settings.RESPONSE_FORMATTER = {
            "INCLUDE_NULL_FIELDS": False,
        }
        response = client.get("/api/success/")
        data = response.json()

        assert "errors" not in data
        assert "metadata" not in data
        assert data["status"] == "success"
        assert data["data"] == {"id": 1, "name": "Test"}
