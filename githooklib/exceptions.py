class GithooklibException(Exception):
    pass


class HookNotFoundException(GithooklibException):
    def __init__(self, hook_name: str) -> None:
        self.hook_name = hook_name
        super().__init__(f"Hook not found: {hook_name}")


class HookInstallationError(GithooklibException):
    def __init__(self, hook_name: str, reason: str) -> None:
        self.hook_name = hook_name
        self.reason = reason
        super().__init__(f"Failed to install hook '{hook_name}': {reason}")


class HookUninstallationError(GithooklibException):
    def __init__(self, hook_name: str, reason: str) -> None:
        self.hook_name = hook_name
        self.reason = reason
        super().__init__(f"Failed to uninstall hook '{hook_name}': {reason}")


class HookExecutionError(GithooklibException):
    def __init__(self, hook_name: str, reason: str) -> None:
        self.hook_name = hook_name
        self.reason = reason
        super().__init__(f"Failed to execute hook '{hook_name}': {reason}")


class GitRepositoryNotFoundError(GithooklibException):
    def __init__(self) -> None:
        super().__init__("Not in a git repository")


class ProjectRootNotFoundError(GithooklibException):
    def __init__(self) -> None:
        super().__init__("Could not find project root")


class ConfigurationError(GithooklibException):
    def __init__(self, message: str) -> None:
        super().__init__(f"Configuration error: {message}")


class DuplicateHookError(GithooklibException):
    def __init__(self, hook_name: str, locations: list) -> None:
        self.hook_name = hook_name
        self.locations = locations
        super().__init__(
            f"Duplicate implementations found for hook '{hook_name}' in: {', '.join(str(l) for l in locations)}"
        )


class InvalidHookNameError(GithooklibException):
    def __init__(self, hook_name: str) -> None:
        self.hook_name = hook_name
        super().__init__(f"Invalid hook name: {hook_name}")


class CommandExecutionError(GithooklibException):
    def __init__(self, command: str, exit_code: int, stderr: str = "") -> None:
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(
            f"Command failed with exit code {exit_code}: {command}\n{stderr}"
        )


__all__ = [
    "GithooklibException",
    "HookNotFoundException",
    "HookInstallationError",
    "HookUninstallationError",
    "HookExecutionError",
    "GitRepositoryNotFoundError",
    "ProjectRootNotFoundError",
    "ConfigurationError",
    "DuplicateHookError",
    "InvalidHookNameError",
    "CommandExecutionError",
]
