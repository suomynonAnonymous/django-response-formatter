"""Test views used by the test suite."""

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from dj_response_formatter.helpers import error_response, raw_response, success_response


class SuccessView(APIView):
    def get(self, request):
        return Response({"id": 1, "name": "Test"})


class SuccessWithMessageView(APIView):
    def get(self, request):
        return success_response(data={"id": 1}, message="Custom success message.")


class CreatedView(APIView):
    def post(self, request):
        return Response({"id": 1, "name": "New"}, status=status.HTTP_201_CREATED)


class ListView(APIView):
    def get(self, request):
        return Response([{"id": 1}, {"id": 2}])


class PaginatedView(APIView):
    def get(self, request):
        return Response(
            {
                "count": 100,
                "next": "http://testserver/api/paginated/?page=2",
                "previous": None,
                "results": [{"id": 1}, {"id": 2}],
            }
        )


class EmptyView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class RawView(APIView):
    def get(self, request):
        return raw_response(data={"healthy": True})


class ValidationErrorView(APIView):
    def post(self, request):
        raise exceptions.ValidationError(
            {
                "email": ["This field is required."],
                "username": ["A user with that username already exists."],
            }
        )


class NotFoundView(APIView):
    def get(self, request):
        raise exceptions.NotFound()


class PermissionDeniedView(APIView):
    def get(self, request):
        raise exceptions.PermissionDenied()


class UnauthorizedView(APIView):
    def get(self, request):
        raise exceptions.NotAuthenticated()


class ThrottledView(APIView):
    def get(self, request):
        raise exceptions.Throttled(wait=30)


class ServerErrorView(APIView):
    def get(self, request):
        raise RuntimeError("Something unexpected happened")


class HelperSuccessView(APIView):
    def get(self, request):
        return success_response(
            data={"id": 1, "name": "Test"},
            message="User retrieved.",
        )


class HelperErrorView(APIView):
    def post(self, request):
        return error_response(
            errors={"email": ["Invalid email."]},
            message="Validation failed.",
            status_code=400,
        )


