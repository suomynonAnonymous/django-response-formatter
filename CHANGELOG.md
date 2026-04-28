# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-04-28

### Security
- Pin all GitHub Actions to commit SHAs
- Add SECURITY.md, dependabot.yml, py.typed marker
- Replace personal email with GitHub noreply address
- Add top-level `permissions: contents: read` to CI workflow

### Removed
- Remove deprecated `default_app_config` (Django 3.2+)

## [0.1.2] - 2026-04-28

### Changed
- Fix author display name on PyPI

## [0.1.1] - 2026-04-28

### Changed
- Renamed Python import from `django_response_formatter` to `dj_response_formatter` to match PyPI package name
- Added Django 6.0 classifier

## [0.1.0] - 2026-04-24

### Added
- `FormattedJSONRenderer` — wraps all DRF responses into `{status, message, data, errors, metadata}` format
- `ResponseFormatterMiddleware` — catches unhandled exceptions and formats them consistently
- `format_exception_handler` — custom DRF exception handler with consistent error formatting
- Support for pagination metadata extraction
- Configurable via `RESPONSE_FORMATTER` Django setting
- Full test suite with 90%+ coverage
