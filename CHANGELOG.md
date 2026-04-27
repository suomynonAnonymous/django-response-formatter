# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-24

### Added

- `FormattedJSONRenderer` — wraps all DRF responses into `{status, message, data, errors, metadata}` format
- `ResponseFormatterMiddleware` — catches unhandled exceptions and formats them consistently
- `format_exception_handler` — custom DRF exception handler with consistent error formatting
- Support for pagination metadata extraction
- Configurable via `RESPONSE_FORMATTER` Django setting
- Full test suite with 90%+ coverage
