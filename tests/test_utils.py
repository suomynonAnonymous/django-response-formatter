"""Tests for the utility functions."""

from django_response_formatter.utils import (
    build_error_envelope,
    build_success_envelope,
    extract_pagination_metadata,
    get_config,
)


class TestGetConfig:
    """Test configuration loading and merging."""

    def test_default_config(self):
        config = get_config()
        assert config["STATUS_FIELD"] == "status"
        assert config["MESSAGE_FIELD"] == "message"
        assert config["DATA_FIELD"] == "data"
        assert config["SUCCESS_STATUS"] == "success"
        assert config["ERROR_STATUS"] == "error"
        assert config["INCLUDE_NULL_FIELDS"] is True
        assert config["EXTRACT_PAGINATION"] is True

    def test_user_override(self, settings):
        settings.RESPONSE_FORMATTER = {
            "DEFAULT_SUCCESS_MESSAGE": "OK",
            "INCLUDE_NULL_FIELDS": False,
        }
        config = get_config()
        assert config["DEFAULT_SUCCESS_MESSAGE"] == "OK"
        assert config["INCLUDE_NULL_FIELDS"] is False
        # Defaults still present for non-overridden keys
        assert config["STATUS_FIELD"] == "status"

    def test_custom_field_names(self, settings):
        settings.RESPONSE_FORMATTER = {
            "STATUS_FIELD": "ok",
            "DATA_FIELD": "result",
        }
        config = get_config()
        assert config["STATUS_FIELD"] == "ok"
        assert config["DATA_FIELD"] == "result"


class TestBuildSuccessEnvelope:
    """Test the success envelope builder."""

    def test_basic_success(self):
        envelope = build_success_envelope(data={"id": 1})
        assert envelope["status"] == "success"
        assert envelope["message"] == "Request was successful."
        assert envelope["data"] == {"id": 1}
        assert envelope["errors"] is None
        assert envelope["metadata"] is None

    def test_custom_message(self):
        envelope = build_success_envelope(data=None, message="Created.")
        assert envelope["message"] == "Created."

    def test_with_metadata(self):
        meta = {"pagination": {"count": 10}}
        envelope = build_success_envelope(data=[], metadata=meta)
        assert envelope["metadata"] == meta

    def test_null_fields_excluded(self, settings):
        settings.RESPONSE_FORMATTER = {"INCLUDE_NULL_FIELDS": False}
        envelope = build_success_envelope(data={"id": 1})
        assert "errors" not in envelope
        assert "metadata" not in envelope

    def test_list_data(self):
        envelope = build_success_envelope(data=[1, 2, 3])
        assert envelope["data"] == [1, 2, 3]

    def test_none_data(self):
        envelope = build_success_envelope(data=None)
        assert envelope["data"] is None


class TestBuildErrorEnvelope:
    """Test the error envelope builder."""

    def test_basic_error(self):
        envelope = build_error_envelope(errors={"field": ["error"]})
        assert envelope["status"] == "error"
        assert envelope["message"] == "An error occurred."
        assert envelope["data"] is None
        assert envelope["errors"] == {"field": ["error"]}

    def test_with_message(self):
        envelope = build_error_envelope(message="Not found.")
        assert envelope["message"] == "Not found."

    def test_with_status_code(self):
        envelope = build_error_envelope(status_code=404)
        assert envelope["metadata"]["status_code"] == 404

    def test_no_status_code_no_metadata(self):
        envelope = build_error_envelope(errors={"field": ["err"]})
        assert envelope["metadata"] is None

    def test_null_fields_excluded(self, settings):
        settings.RESPONSE_FORMATTER = {"INCLUDE_NULL_FIELDS": False}
        envelope = build_error_envelope(errors={"field": ["err"]}, status_code=400)
        assert "data" not in envelope
        assert "errors" in envelope


class TestExtractPaginationMetadata:
    """Test pagination metadata extraction."""

    def test_paginated_data(self):
        data = {
            "count": 50,
            "next": "http://example.com/?page=2",
            "previous": None,
            "results": [{"id": 1}, {"id": 2}],
        }
        cleaned, meta = extract_pagination_metadata(data)
        assert cleaned == [{"id": 1}, {"id": 2}]
        assert meta["count"] == 50
        assert meta["next"] == "http://example.com/?page=2"
        assert meta["previous"] is None

    def test_non_paginated_dict(self):
        data = {"id": 1, "name": "Test"}
        cleaned, meta = extract_pagination_metadata(data)
        assert cleaned == data
        assert meta is None

    def test_list_data(self):
        data = [{"id": 1}]
        cleaned, meta = extract_pagination_metadata(data)
        assert cleaned == data
        assert meta is None

    def test_dict_with_results_but_no_pagination(self):
        data = {"results": [1, 2, 3]}
        cleaned, meta = extract_pagination_metadata(data)
        assert cleaned == data
        assert meta is None
