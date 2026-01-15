import sys
from typing import Optional

from .api import API
from .constants import EXIT_SUCCESS, EXIT_FAILURE
from .logger import get_logger
from .ui import get_console
from .ui_messages import (
    UI_MESSAGE_AVAILABLE_HOOKS_HEADER,
    UI_MESSAGE_NO_HOOKS_FOUND,
    UI_MESSAGE_INSTALLED_HOOKS_HEADER,
    UI_MESSAGE_NOT_IN_GIT_REPOSITORY,
    UI_MESSAGE_NO_HOOKS_DIRECTORY_FOUND,
    UI_MESSAGE_NO_HOOKS_INSTALLED,
    UI_MESSAGE_AVAILABLE_EXAMPLE_HOOKS_HEADER,
    UI_MESSAGE_NO_EXAMPLE_HOOKS_AVAILABLE,
    UI_MESSAGE_ERROR_PREFIX,
    UI_MESSAGE_HOOK_SOURCE_GITHOOKLIB,
    UI_MESSAGE_HOOK_SOURCE_EXTERNAL,
    UI_MESSAGE_EXAMPLE_NOT_FOUND_PREFIX,
    UI_MESSAGE_EXAMPLE_NOT_FOUND_SUFFIX,
    UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_PREFIX,
    UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_SUFFIX,
    UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PREFIX,
    UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PROJECT_ROOT_NOT_FOUND,
    UI_MESSAGE_ERROR_SEEDING_EXAMPLE_PREFIX,
)

logger = get_logger()
console = get_console()


def print_error(message: str) -> None:
    console.print_error(f"{UI_MESSAGE_ERROR_PREFIX}{message}")


class CLI:
    """Command-line interface for githooklib.

    This class provides a command-line interface for managing Git hooks in Python
    projects. It enables discovery, installation, uninstallation, and execution of
    Git hooks defined in the project. Hooks are automatically discovered from the
    'githooks' directory or project root.

    When running commands manually, you may add a --debug flag to see additional
    logging information.
    """

    def __init__(self) -> None:
        logger.trace("Initializing CLI")
        self._api = API()

    def list(self) -> None:
        """List all available hooks in the project.

        You may add a --debug flag to see additional logging information.
        """
        try:
            hook_names = self._api.list_available_hook_names()
        except ValueError as e:
            logger.error("%s%s", UI_MESSAGE_ERROR_PREFIX, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return

        if not hook_names:
            logger.error(UI_MESSAGE_NO_HOOKS_FOUND)
            logger.debug("No hooks found in project")
            console.print_error(UI_MESSAGE_NO_HOOKS_FOUND)
            return

        console.print_info(UI_MESSAGE_AVAILABLE_HOOKS_HEADER)
        for hook_name in hook_names:
            console.print(f"  • {hook_name}")

    def show(self) -> None:
        """Show all installed git hooks and their installation source.

        You may add a --debug flag to see additional logging information.
        """
        logger.debug("Executing show command")
        context = self._api.get_installed_hooks_with_context()

        if not context.installed_hooks:
            if not context.git_root:
                logger.error(UI_MESSAGE_NOT_IN_GIT_REPOSITORY)
                logger.debug("Not in a git repository")
            elif not context.hooks_dir_exists:
                logger.error(UI_MESSAGE_NO_HOOKS_DIRECTORY_FOUND)
                logger.debug("Hooks directory does not exist")
            else:
                logger.error(UI_MESSAGE_NO_HOOKS_INSTALLED)
                logger.debug("No hooks installed")
            return

        logger.debug("Displaying %d installed hooks", len(context.installed_hooks))
        logger.trace("Installed hooks: %s", context.installed_hooks)
        console.print_info(UI_MESSAGE_INSTALLED_HOOKS_HEADER)
        
        rows = []
        for hook_name, installed_via_tool in sorted(context.installed_hooks.items()):
            source = (
                UI_MESSAGE_HOOK_SOURCE_GITHOOKLIB
                if installed_via_tool
                else UI_MESSAGE_HOOK_SOURCE_EXTERNAL
            )
            logger.trace("Hook '%s' source: %s", hook_name, source)
            rows.append([hook_name, source])
        
        console.print_table(["Hook Name", "Source"], rows)

    def run(self, hook_name: str) -> int:
        """Run a hook manually for testing purposes.

        You may add a --debug flag to see additional logging information.

        Args:
            hook_name: Name of the hook to run

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing run command for hook '%s'", hook_name)
        try:
            if not self._api.check_hook_exists(hook_name):
                error_msg = self._api.get_hook_not_found_error_message(hook_name)
                print_error(error_msg)
                logger.warning("Hook '%s' does not exist", hook_name)
                logger.debug("Hook '%s' not found, cannot run", hook_name)
                return EXIT_FAILURE
            exit_code = self._api.run_hook_by_name(hook_name)
            return exit_code
        except ValueError as e:
            logger.error("Error running hook '%s': %s", hook_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return EXIT_FAILURE

    def install(self, hook_name: str) -> int:
        """Install a hook to .git/hooks/.

        You may add a --debug flag to see additional logging information.

        Args:
            hook_name: Name of the hook to install

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing install command for hook '%s'", hook_name)
        try:
            if not self._api.check_hook_exists(hook_name):
                error_msg = self._api.get_hook_not_found_error_message(hook_name)
                print_error(error_msg)
                logger.warning("Hook '%s' does not exist, cannot install", hook_name)
                logger.debug("Hook '%s' not found, cannot install", hook_name)
                return EXIT_FAILURE
            logger.debug("Installing hook '%s'", hook_name)
            success = self._api.install_hook_by_name(hook_name)
            if success:
                logger.success("Installed hook '%s'", hook_name)
                logger.debug("Hook '%s' installation completed successfully", hook_name)
            else:
                logger.warning("Failed to install hook '%s'", hook_name)
                logger.debug("Hook '%s' installation failed", hook_name)
            return EXIT_SUCCESS if success else EXIT_FAILURE
        except Exception as e:
            logger.error("Error installing hook '%s': %s", hook_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return EXIT_FAILURE

    def uninstall(self, hook_name: str) -> int:
        """Uninstall a hook from .git/hooks/.

        You may add a --debug flag to see additional logging information.

        Args:
            hook_name: Name of the hook to uninstall

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing uninstall command for hook '%s'", hook_name)
        try:
            if not self._api.check_hook_exists(hook_name):
                error_msg = self._api.get_hook_not_found_error_message(hook_name)
                print_error(error_msg)
                logger.warning("Hook '%s' does not exist, cannot uninstall", hook_name)
                logger.debug("Hook '%s' not found, cannot uninstall", hook_name)
                return EXIT_FAILURE
            logger.debug("Uninstalling hook '%s'", hook_name)
            success = self._api.uninstall_hook_by_name(hook_name)
            if success:
                logger.info("Successfully uninstalled hook '%s'", hook_name)
                logger.debug(
                    "Hook '%s' uninstallation completed successfully", hook_name
                )
            else:
                logger.warning("Failed to uninstall hook '%s'", hook_name)
                logger.debug("Hook '%s' uninstallation failed", hook_name)
            return EXIT_SUCCESS if success else EXIT_FAILURE
        except ValueError as e:
            logger.error("Error uninstalling hook '%s': %s", hook_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(str(e))
            return EXIT_FAILURE

    def seed(self, example_name: Optional[str] = None) -> int:
        """Seed an example hook from the examples folder to githooks/.

        If no example_name is provided, lists all available examples.

        You may add a --debug flag to see additional logging information.

        Args:
            example_name: Name of the example to seed (filename without .py extension)

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug(
            "Executing seed command%s",
            f" for example '{example_name}'" if example_name else "",
        )
        if example_name is None:
            logger.debug("No example name provided, listing available examples")
            available_examples = self._api.list_available_example_names()
            if not available_examples:
                logger.error(UI_MESSAGE_NO_EXAMPLE_HOOKS_AVAILABLE)
                logger.debug("No examples available")
                return EXIT_FAILURE
            logger.debug("Displaying %d available examples", len(available_examples))
            console.print_info(UI_MESSAGE_AVAILABLE_EXAMPLE_HOOKS_HEADER)
            for example in available_examples:
                console.print(f"  • {example}")
            return EXIT_SUCCESS

        try:
            logger.debug("Seeding example '%s' to project", example_name)
            success = self._api.seed_example_hook_to_project(example_name)
            if success:
                logger.info(
                    "Successfully seeded example '%s' to githooks/", example_name
                )
                logger.debug(
                    "Example '%s' seeding completed successfully", example_name
                )
                return EXIT_SUCCESS

            logger.warning("Failed to seed example '%s'", example_name)
            logger.debug("Getting failure details for example '%s'", example_name)
            failure_details = self._api.get_seed_failure_details(example_name)

            if failure_details.example_not_found:
                logger.warning(
                    "Example '%s' not found. Available: %s",
                    example_name,
                    failure_details.available_examples,
                )
                logger.debug(
                    "Example '%s' not found in available examples", example_name
                )
                print_error(
                    f"{UI_MESSAGE_EXAMPLE_NOT_FOUND_PREFIX}"
                    f"{example_name}"
                    f"{UI_MESSAGE_EXAMPLE_NOT_FOUND_SUFFIX}"
                    f"{', '.join(failure_details.available_examples)}"
                )
                return EXIT_FAILURE

            if failure_details.project_root_not_found:
                logger.warning("Project root not found for example '%s'", example_name)
                logger.debug(
                    "Project root not found, cannot seed example '%s'", example_name
                )
                print_error(
                    f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PREFIX}"
                    f"{example_name}"
                    f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PROJECT_ROOT_NOT_FOUND}"
                )
                return EXIT_FAILURE

            if failure_details.target_hook_already_exists:
                target_path = failure_details.target_hook_path
                logger.warning(
                    "Example '%s' already exists at %s", example_name, target_path
                )
                logger.debug("Target hook already exists at %s", target_path)
                if target_path:
                    print_error(
                        f"{UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_PREFIX}"
                        f"{example_name}"
                        f"{UI_MESSAGE_EXAMPLE_ALREADY_EXISTS_SUFFIX}"
                        f"{target_path}"
                    )
                return EXIT_FAILURE

            logger.warning(
                "Failed to seed example '%s'. Project root not found.", example_name
            )
            logger.debug(
                "Unknown failure reason for seeding example '%s'", example_name
            )
            print_error(
                f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PREFIX}"
                f"{example_name}"
                f"{UI_MESSAGE_FAILED_TO_SEED_EXAMPLE_PROJECT_ROOT_NOT_FOUND}"
            )
            return EXIT_FAILURE
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error seeding example '%s': %s", example_name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            print_error(f"{UI_MESSAGE_ERROR_SEEDING_EXAMPLE_PREFIX}{e}")
            return EXIT_FAILURE
    
    def init(self, config_format: str = "yaml") -> int:
        """Initialize githooklib in the current project with a configuration file.
        
        You may add a --debug flag to see additional logging information.
        
        Args:
            config_format: Configuration file format ('yaml' or 'toml'). Defaults to 'yaml'.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing init command with format: %s", config_format)
        
        from pathlib import Path
        from .config import ConfigLoader
        from .gateways import ProjectRootGateway
        
        project_root = ProjectRootGateway.find_project_root()
        if not project_root:
            project_root = Path.cwd()
        
        if config_format == "yaml":
            config_file = project_root / ".githooklib.yaml"
        elif config_format == "toml":
            config_file = project_root / ".githooklib.toml"
        else:
            console.print_error(f"Invalid config format: {config_format}")
            logger.error("Invalid config format: %s", config_format)
            return EXIT_FAILURE
        
        if config_file.exists():
            console.print_warning(f"Configuration file already exists: {config_file}")
            logger.warning("Config file already exists: %s", config_file)
            return EXIT_FAILURE
        
        success = ConfigLoader.create_default_config_file(config_file)
        
        if success:
            console.print_success(f"Created configuration file: {config_file}")
            logger.success("Config file created: %s", config_file)
            return EXIT_SUCCESS
        else:
            console.print_error(f"Failed to create configuration file: {config_file}")
            logger.error("Failed to create config file: %s", config_file)
            return EXIT_FAILURE
    
    def doctor(self) -> int:
        """Diagnose potential issues with githooklib setup.
        
        Checks:
        - Git repository status
        - Project root detection
        - Hook discovery
        - Configuration file
        - Dependencies
        
        You may add a --debug flag to see additional logging information.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing doctor command")
        from pathlib import Path
        from .gateways import ProjectRootGateway, GitGateway
        from .config import ConfigLoader
        
        console.print_info("Running githooklib diagnostics...")
        print()
        
        issues_found = 0
        
        git_gateway = GitGateway()
        git_root = git_gateway.get_git_root_path()
        if git_root:
            console.print_success(f"Git repository found: {git_root}")
        else:
            console.print_error("Not in a git repository")
            issues_found += 1
        
        project_root = ProjectRootGateway.find_project_root()
        if project_root:
            console.print_success(f"Project root found: {project_root}")
        else:
            console.print_warning("Project root not found (using current directory)")
            project_root = Path.cwd()
        
        config_file = ConfigLoader.find_config_file()
        if config_file:
            console.print_success(f"Configuration file found: {config_file}")
        else:
            console.print_info("No configuration file (using defaults)")
        
        try:
            hook_names = self._api.list_available_hook_names()
            if hook_names:
                console.print_success(f"Found {len(hook_names)} hook(s): {', '.join(hook_names)}")
            else:
                console.print_warning("No hooks found in project")
        except Exception as e:
            console.print_error(f"Error discovering hooks: {e}")
            issues_found += 1
        
        try:
            import yaml
            console.print_success("PyYAML is installed")
        except ImportError:
            console.print_warning("PyYAML not installed (YAML config files not supported)")
        
        try:
            import colorama
            console.print_success("Colorama is installed")
        except ImportError:
            console.print_info("Colorama not installed (colored output disabled)")
        
        try:
            import rich
            console.print_success("Rich is installed")
        except ImportError:
            console.print_info("Rich not installed (enhanced output disabled)")
        
        print()
        if issues_found == 0:
            console.print_success("No issues found!")
            return EXIT_SUCCESS
        else:
            console.print_warning(f"Found {issues_found} issue(s)")
            return EXIT_FAILURE
    
    def status(self) -> int:
        """Show detailed status of hooks and recent execution.
        
        You may add a --debug flag to see additional logging information.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing status command")
        
        console.print_info("Hook Status")
        print()
        
        context = self._api.get_installed_hooks_with_context()
        
        if not context.installed_hooks:
            console.print_warning("No hooks installed")
            return EXIT_SUCCESS
        
        rows = []
        for hook_name, installed_via_tool in sorted(context.installed_hooks.items()):
            source = "githooklib" if installed_via_tool else "external"
            status = "✓ Installed"
            rows.append([hook_name, source, status])
        
        console.print_table(["Hook", "Source", "Status"], rows)
        
        return EXIT_SUCCESS
    
    def enable(self, hook_name: str) -> int:
        """Enable a previously disabled hook.
        
        You may add a --debug flag to see additional logging information.
        
        Args:
            hook_name: Name of the hook to enable
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing enable command for hook '%s'", hook_name)
        console.print_info(f"Enabling hook: {hook_name}")
        
        return self.install(hook_name)
    
    def disable(self, hook_name: str) -> int:
        """Disable a hook without uninstalling it.
        
        You may add a --debug flag to see additional logging information.
        
        Args:
            hook_name: Name of the hook to disable
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        logger.debug("Executing disable command for hook '%s'", hook_name)
        console.print_info(f"Disabling hook: {hook_name}")
        
        return self.uninstall(hook_name)


__all__ = ["CLI"]
