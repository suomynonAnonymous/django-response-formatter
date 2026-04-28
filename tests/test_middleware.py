"""Tests for the ResponseFormatterMiddleware."""

import json

import pytest
from django.test import RequestFactory

from dj_response_formatter.middleware import ResponseFormatterMiddleware


@pytest.fixture
def rf():
    return RequestFactory()


class TestMiddleware:
    """Test the middleware catches unhandled exceptions."""

    def _make_middleware(self, view_func):
        return ResponseFormatterMiddleware(view_func)

    def test_normal_response_passes_through(self, rf):
        from django.http import JsonResponse

        def view(request):
            return JsonResponse({"ok": True})

        middleware = self._make_middleware(view)
        request = rf.get("/api/test/", HTTP_ACCEPT="application/json")
        response = middleware(request)

        assert response.status_code == 200

    def test_catches_unhandled_exception_for_json_request(self, rf):
        def view(request):
            raise RuntimeError("boom")

        middleware = self._make_middleware(view)
        request = rf.get("/api/test/", HTTP_ACCEPT="application/json")
        response = middleware(request)

        assert response.status_code == 500
        data = json.loads(response.content)
        assert data["status"] == "error"
        assert "internal server error" in data["message"].lower()
        # Should NOT expose exception details
        assert "boom" not in data["message"]

    def test_reraises_for_non_json_request(self, rf):
        def view(request):
            raise RuntimeError("boom")

        middleware = self._make_middleware(view)
        request = rf.get("/page/", HTTP_ACCEPT="text/html")

        with pytest.raises(RuntimeError, match="boom"):
            middleware(request)

    def test_json_content_type_triggers_handling(self, rf):
        def view(request):
            raise ValueError("oops")

        middleware = self._make_middleware(view)
        request = rf.get("/some/path/", CONTENT_TYPE="application/json")
        response = middleware(request)

        assert response.status_code == 500
        assert json.loads(response.content)["status"] == "error"

    def test_api_prefix_triggers_handling(self, rf):
        def view(request):
            raise ValueError("oops")

        middleware = self._make_middleware(view)
        request = rf.get("/api/something/")
        response = middleware(request)

        assert response.status_code == 500
        assert json.loads(response.content)["status"] == "error"
