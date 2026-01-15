# Changelog

All notable changes to githooklib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-01-15

### Added
- Configuration validation with `__post_init__` methods
  - Validates `log_level` against allowed values
  - Validates `max_workers` is between 1 and 100
  - Validates `smtp_port` is within valid range (1-65535)
  - Validates notification providers have required configuration when enabled
  - Validates chain steps have either hook or command (not both)
  - Validates `hook_search_paths` is not empty
- Command timeout support
  - Added `timeout` parameter to `CommandExecutor.run()` method
  - Handles `subprocess.TimeoutExpired` exceptions gracefully
  - Returns proper error codes (124) for timed-out commands
  - Provides clear timeout error messages

### Changed
- Refactored CLI error handling using `@require_hook_exists` decorator
  - Eliminated ~40 lines of duplicated code across `run`, `install`, and `uninstall` methods
  - Improved code maintainability and readability
  - Centralized hook existence validation logic
- Improved configuration validation to only check when notifications are globally enabled

### Fixed
- Windows Unicode encoding issues with console output
- Import errors in `project_root_gateway.py` and `__main__.py`

## [1.0.1] - 2026-01-15

### Fixed
- Windows Unicode encoding issues with emoji characters in console output
- Import errors: `GithooklibException` case mismatch
- Import errors: `FireGetResultMock` incorrect path
- E2E test failures related to console output format changes
- Unit test failures related to error output redirection

### Changed
- Updated console system to use platform-specific symbols on Windows

## [1.0.0] - 2026-01-15

### Added
- Initial release of githooklib
- Git hook framework with automatic discovery
- CLI commands: `list`, `show`, `install`, `uninstall`, `run`, `seed`, `doctor`, `status`, `init`
- File pattern matching for conditional hook execution
- Hook chaining (sequential and parallel)
- File hash caching for performance
- Multi-provider notifications (Slack, Email, Webhook, Desktop)
- Cross-platform support (Windows, Linux, macOS)
- Rich CLI with colored output and progress bars
- YAML/TOML configuration support
- Built-in example hooks
