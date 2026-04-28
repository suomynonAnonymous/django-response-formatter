"""URL configuration for the test suite."""

from django.urls import path

from . import views

urlpatterns = [
    path("api/success/", views.SuccessView.as_view(), name="success"),
    path("api/success-message/", views.SuccessWithMessageView.as_view(), name="success-message"),
    path("api/created/", views.CreatedView.as_view(), name="created"),
    path("api/list/", views.ListView.as_view(), name="list"),
    path("api/paginated/", views.PaginatedView.as_view(), name="paginated"),
    path("api/empty/", views.EmptyView.as_view(), name="empty"),
    path("api/raw/", views.RawView.as_view(), name="raw"),
    path("api/validation-error/", views.ValidationErrorView.as_view(), name="validation-error"),
    path("api/not-found/", views.NotFoundView.as_view(), name="not-found"),
    path("api/permission-denied/", views.PermissionDeniedView.as_view(), name="permission-denied"),
    path("api/unauthorized/", views.UnauthorizedView.as_view(), name="unauthorized"),
    path("api/throttled/", views.ThrottledView.as_view(), name="throttled"),
    path("api/server-error/", views.ServerErrorView.as_view(), name="server-error"),
    path("api/helper-success/", views.HelperSuccessView.as_view(), name="helper-success"),
    path("api/helper-error/", views.HelperErrorView.as_view(), name="helper-error"),
]
