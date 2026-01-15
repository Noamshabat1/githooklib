# githooklib

A Python framework for creating, managing, and installing Git hooks with automatic discovery and CLI tools.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

## Features

- Simple & powerful API for creating Git hooks
- Automatic hook discovery and installation
- File pattern matching for conditional execution
- Hook chaining (sequential or parallel)
- File hash caching for performance
- Command timeout support to prevent hanging hooks
- Configuration validation with clear error messages
- Notifications (Slack, Email, Webhook, Desktop)
- Cross-platform support (Windows, Linux, macOS)
- Built-in examples ready to use

## Installation

```bash
pip install githooklib
```

## Quick Start

### 1. Create a Hook

```python
# githooks/pre_commit.py
from githooklib import GitHook, HookResult, GitHookContext

class PreCommitHook(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"
    
    @classmethod
    def get_file_patterns(cls):
        return ["*.py"]  # Only run when Python files change
    
    def execute(self, context: GitHookContext) -> HookResult:
        result = self.command_executor.run(["pytest", "-x"])
        
        if not result.success:
            return HookResult(
                success=False,
                message="Tests failed. Commit aborted.",
                exit_code=1
            )
        
        return HookResult(success=True, message="All tests passed!")
```

### 2. Install the Hook

```bash
githooklib install pre-commit
```

### 3. Use Built-in Examples

```bash
githooklib seed                    # List available examples
githooklib seed pre_commit_black   # Seed an example
githooklib install pre-commit      # Install it
```

## CLI Commands

```bash
githooklib init                    # Initialize with config file
githooklib list                    # List available hooks
githooklib show                    # Show installed hooks
githooklib install <hook-name>     # Install a hook
githooklib uninstall <hook-name>   # Uninstall a hook
githooklib run <hook-name>         # Run a hook manually
githooklib seed [example-name]     # Seed example hooks
githooklib doctor                  # Diagnose setup issues
```

## Configuration

Create `.githooklib.yaml` in your project root:

```yaml
hook_search_paths:
  - githooks

log_level: INFO  # Must be: TRACE, DEBUG, INFO, WARNING, ERROR, or CRITICAL

performance:
  caching_enabled: true
  parallel_execution: false
  max_workers: 4  # Must be between 1 and 100

notifications:
  enabled: false
  on_failure: true
  desktop:
    enabled: true

hooks:
  pre-commit:
    file_patterns: ["*.py"]
```

**Configuration is validated automatically.** Invalid values will produce clear error messages:
- `log_level` must be a valid logging level
- `max_workers` must be between 1 and 100
- `smtp_port` must be between 1 and 65535
- Enabled notifications require their configuration (e.g., `smtp_server` for email)

## Advanced: Hook Chaining

```yaml
hooks:
  pre-commit:
    chain:
      enabled: true
      chain:
        - name: format
          hook: black
        - name: lint
          hook: flake8
          parallel: true
        - name: test
          command: ["pytest", "-x"]
```

## API Reference

### GitHook Base Class

```python
class MyHook(GitHook):
    @classmethod
    def get_hook_name(cls) -> str:
        """Return hook name (e.g., 'pre-commit', 'pre-push')"""
        return "pre-commit"
    
    @classmethod
    def get_file_patterns(cls):
        """Return file patterns or None to always run"""
        return ["*.py"]
    
    def execute(self, context: GitHookContext) -> HookResult:
        """Execute hook logic"""
        # Use self.logger for logging
        self.logger.info("Running my hook...")
        
        # Use self.command_executor to run commands with optional timeout
        result = self.command_executor.run(
            ["pytest", "-x"],
            timeout=300  # Optional: timeout after 5 minutes
        )
        
        if result.exit_code == 124:
            return HookResult(
                success=False,
                message="Tests timed out!",
                exit_code=1
            )
        
        return HookResult(success=True, message="Success!")
```

### GitHookContext

Provides context when a hook is executed:

- `hook_name`: Name of the hook
- `argv`: Command-line arguments
- `project_root`: Path to project root
- `stdin_lines`: Lines from stdin (for pre-push, commit-msg)
- `get_changed_files()`: Get list of changed files

### HookResult

Return value from `execute()`:

- `success`: Whether the hook passed (bool)
- `message`: Optional message to display (str)
- `exit_code`: Exit code (0 for success, default from success)

## Built-in Examples

- `pre_commit_black` - Auto-format Python code with Black
- `pre_commit_pytest` - Run pytest before commits
- `pre_commit_flake8` - Lint Python code with flake8
- `pre_commit_isort` - Sort Python imports with isort
- `pre_push_coverage` - Check test coverage before push
- `commit_msg_conventional` - Validate conventional commit messages

## Troubleshooting

```bash
# Diagnose issues
githooklib doctor

# Check what's installed
githooklib show

# Test hook manually with debug logging
githooklib run pre-commit --debug
```

## What's New in v1.0.2

### Configuration Validation
All configuration values are now validated when loaded, providing clear error messages for invalid settings.

### Command Timeout Support
Prevent hooks from hanging indefinitely by adding an optional timeout to command execution:

```python
result = self.command_executor.run(
    ["long-running-command"],
    timeout=300  # Timeout after 5 minutes
)
```

### Improved Error Handling
CLI commands now use a centralized decorator pattern for cleaner, more maintainable code.

## Requirements

- Python 3.8+
- Git repository

## License

See [LICENSE](LICENSE) file for details.

## Links

- **Homepage**: https://github.com/Noamshabat1/githooklib
- **Issues**: https://github.com/Noamshabat1/githooklib/issues

---

**Version:** 1.0.2  
**Author:** Noam Shabat
