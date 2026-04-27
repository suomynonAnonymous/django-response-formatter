"""Minimal Django settings for running the test suite."""

SECRET_KEY = "test-secret-key-not-for-production"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "django_response_formatter",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests.urls"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "django_response_formatter.renderers.FormattedJSONRenderer",
    ],
    "EXCEPTION_HANDLER": "django_response_formatter.exceptions.format_exception_handler",
}

MIDDLEWARE = [
    "django_response_formatter.middleware.ResponseFormatterMiddleware",
]
