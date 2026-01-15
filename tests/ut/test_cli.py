import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from githooklib.cli import CLI, print_error
from githooklib.constants import EXIT_SUCCESS, EXIT_FAILURE
from githooklib.services.hook_management_service import InstalledHooksContext
from tests.base_test_case import BaseTestCase


class TestCLI(BaseTestCase):
    def setUp(self):
        self.cli = CLI()

    def test_list_with_hooks_prints_hooks(self):
        with patch.object(
            self.cli._api, "list_available_hook_names", return_value=["hook1", "hook2"]
        ):
            with patch("githooklib.ui.console.Console.print") as mock_print:
                self.cli.list()
                mock_print.assert_called()
                calls = [str(call) for call in mock_print.call_args_list]
                self.assertTrue(any("hook1" in str(call) for call in calls))
                self.assertTrue(any("hook2" in str(call) for call in calls))

    def test_list_without_hooks_does_not_print(self):
        with patch.object(self.cli._api, "list_available_hook_names", return_value=[]):
            with patch("githooklib.ui.console.Console.print") as mock_print:
                self.cli.list()
                # Error is printed, not the hook list
                mock_print.assert_not_called()

    def test_list_handles_value_error(self):
        with patch.object(
            self.cli._api,
            "list_available_hook_names",
            side_effect=ValueError("Error message"),
        ):
            with patch("githooklib.cli.console.print_error") as mock_error:
                self.cli.list()
                mock_error.assert_called()
                call_args = str(mock_error.call_args)
                self.assertIn("Error message", call_args)

    def test_show_with_installed_hooks_prints_hooks(self):
        context = InstalledHooksContext(
            {"pre-commit": True, "pre-push": False}, Path("/test"), True
        )
        with patch.object(
            self.cli._api,
            "get_installed_hooks_with_context",
            return_value=context,
        ):
            with patch("githooklib.ui.console.Console.print_table") as mock_table:
                self.cli.show()
                mock_table.assert_called()
                call_args = str(mock_table.call_args)
                self.assertIn("pre-commit", call_args)

    def test_show_without_git_root_does_not_print(self):
        context = InstalledHooksContext({}, None, False)
        with patch.object(
            self.cli._api,
            "get_installed_hooks_with_context",
            return_value=context,
        ):
            with patch("githooklib.ui.console.Console.print_table") as mock_table:
                self.cli.show()
                mock_table.assert_not_called()

    def test_show_without_hooks_directory_does_not_print(self):
        context = InstalledHooksContext({}, Path("/test"), False)
        with patch.object(
            self.cli._api,
            "get_installed_hooks_with_context",
            return_value=context,
        ):
            with patch("githooklib.ui.console.Console.print_table") as mock_table:
                self.cli.show()
                mock_table.assert_not_called()

    def test_show_without_installed_hooks_does_not_print(self):
        context = InstalledHooksContext({}, Path("/test"), True)
        with patch.object(
            self.cli._api,
            "get_installed_hooks_with_context",
            return_value=context,
        ):
            with patch("githooklib.ui.console.Console.print_table") as mock_table:
                self.cli.show()
                mock_table.assert_not_called()

    def test_run_success_returns_exit_success(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=True):
            with patch.object(self.cli._api, "run_hook_by_name", return_value=0):
                result = self.cli.run("test-hook")
                self.assertEqual(result, EXIT_SUCCESS)

    def test_run_failure_returns_exit_failure(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=True):
            with patch.object(self.cli._api, "run_hook_by_name", return_value=1):
                result = self.cli.run("test-hook")
                self.assertEqual(result, EXIT_FAILURE)

    def test_run_hook_not_found_returns_exit_failure(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=False):
            with patch.object(
                self.cli._api,
                "get_hook_not_found_error_message",
                return_value="Hook not found",
            ):
                with patch("githooklib.cli.console.print_error") as mock_error:
                    result = self.cli.run("non-existent-hook")
                    self.assertEqual(result, EXIT_FAILURE)
                    mock_error.assert_called()
                    call_args = str(mock_error.call_args)
                    self.assertIn("Hook not found", call_args)

    def test_run_handles_value_error(self):
        with patch.object(
            self.cli._api, "check_hook_exists", side_effect=ValueError("Error")
        ):
            with patch("githooklib.cli.console.print_error") as mock_error:
                result = self.cli.run("test-hook")
                self.assertEqual(result, EXIT_FAILURE)
                mock_error.assert_called()
                call_args = str(mock_error.call_args)
                self.assertIn("Error", call_args)

    def test_install_success_returns_exit_success(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=True):
            with patch.object(self.cli._api, "install_hook_by_name", return_value=True):
                result = self.cli.install("test-hook")
                self.assertEqual(result, EXIT_SUCCESS)

    def test_install_failure_returns_exit_failure(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=True):
            with patch.object(
                self.cli._api, "install_hook_by_name", return_value=False
            ):
                result = self.cli.install("test-hook")
                self.assertEqual(result, EXIT_FAILURE)

    def test_install_hook_not_found_returns_exit_failure(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=False):
            with patch.object(
                self.cli._api,
                "get_hook_not_found_error_message",
                return_value="Hook not found",
            ):
                with patch("githooklib.cli.console.print_error") as mock_error:
                    result = self.cli.install("non-existent-hook")
                    self.assertEqual(result, EXIT_FAILURE)
                    mock_error.assert_called()
                    call_args = str(mock_error.call_args)
                    self.assertIn("Hook not found", call_args)

    def test_install_handles_exception(self):
        with patch.object(
            self.cli._api, "check_hook_exists", side_effect=Exception("Error")
        ):
            with patch("githooklib.cli.console.print_error") as mock_error:
                result = self.cli.install("test-hook")
                self.assertEqual(result, EXIT_FAILURE)
                mock_error.assert_called()
                call_args = str(mock_error.call_args)
                self.assertIn("Error", call_args)

    def test_uninstall_success_returns_exit_success(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=True):
            with patch.object(
                self.cli._api, "uninstall_hook_by_name", return_value=True
            ):
                result = self.cli.uninstall("test-hook")
                self.assertEqual(result, EXIT_SUCCESS)

    def test_uninstall_failure_returns_exit_failure(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=True):
            with patch.object(
                self.cli._api, "uninstall_hook_by_name", return_value=False
            ):
                result = self.cli.uninstall("test-hook")
                self.assertEqual(result, EXIT_FAILURE)

    def test_uninstall_hook_not_found_returns_exit_failure(self):
        with patch.object(self.cli._api, "check_hook_exists", return_value=False):
            with patch.object(
                self.cli._api,
                "get_hook_not_found_error_message",
                return_value="Hook not found",
            ):
                with patch("githooklib.cli.console.print_error") as mock_error:
                    result = self.cli.uninstall("non-existent-hook")
                    self.assertEqual(result, EXIT_FAILURE)
                    mock_error.assert_called()
                    call_args = str(mock_error.call_args)
                    self.assertIn("Hook not found", call_args)

    def test_uninstall_handles_value_error(self):
        with patch.object(
            self.cli._api, "check_hook_exists", side_effect=ValueError("Error")
        ):
            with patch("githooklib.cli.console.print_error") as mock_error:
                result = self.cli.uninstall("test-hook")
                self.assertEqual(result, EXIT_FAILURE)
                mock_error.assert_called()
                call_args = str(mock_error.call_args)
                self.assertIn("Error", call_args)

    def test_seed_without_example_name_lists_examples(self):
        with patch.object(
            self.cli._api,
            "list_available_example_names",
            return_value=["example1", "example2"],
        ):
            with patch("githooklib.ui.console.Console.print") as mock_print:
                result = self.cli.seed(None)
                self.assertEqual(result, EXIT_SUCCESS)
                mock_print.assert_called()

    def test_seed_without_example_name_no_examples_returns_failure(self):
        with patch.object(
            self.cli._api, "list_available_example_names", return_value=[]
        ):
            result = self.cli.seed(None)
            self.assertEqual(result, EXIT_FAILURE)

    def test_seed_success_returns_exit_success(self):
        with patch.object(
            self.cli._api, "seed_example_hook_to_project", return_value=True
        ):
            result = self.cli.seed("test-example")
            self.assertEqual(result, EXIT_SUCCESS)

    def test_seed_example_not_found_returns_exit_failure(self):
        from githooklib.definitions import SeedFailureDetails

        with patch.object(
            self.cli._api, "seed_example_hook_to_project", return_value=False
        ):
            with patch.object(
                self.cli._api,
                "get_seed_failure_details",
                return_value=SeedFailureDetails(
                    example_not_found=True,
                    project_root_not_found=False,
                    target_hook_already_exists=False,
                    target_hook_path=None,
                    available_examples=["example1"],
                ),
            ):
                with patch("githooklib.cli.console.print_error") as mock_error:
                    result = self.cli.seed("non-existent-example")
                    self.assertEqual(result, EXIT_FAILURE)
                    mock_error.assert_called()

    def test_seed_project_root_not_found_returns_exit_failure(self):
        from githooklib.definitions import SeedFailureDetails

        with patch.object(
            self.cli._api, "seed_example_hook_to_project", return_value=False
        ):
            with patch.object(
                self.cli._api,
                "get_seed_failure_details",
                return_value=SeedFailureDetails(
                    example_not_found=False,
                    project_root_not_found=True,
                    target_hook_already_exists=False,
                    target_hook_path=None,
                    available_examples=[],
                ),
            ):
                with patch("githooklib.cli.console.print_error") as mock_error:
                    result = self.cli.seed("test-example")
                    self.assertEqual(result, EXIT_FAILURE)
                    mock_error.assert_called()

    def test_seed_target_already_exists_returns_exit_failure(self):
        from githooklib.definitions import SeedFailureDetails

        with patch.object(
            self.cli._api, "seed_example_hook_to_project", return_value=False
        ):
            with patch.object(
                self.cli._api,
                "get_seed_failure_details",
                return_value=SeedFailureDetails(
                    example_not_found=False,
                    project_root_not_found=False,
                    target_hook_already_exists=True,
                    target_hook_path=Path("/test/path"),
                    available_examples=[],
                ),
            ):
                with patch("githooklib.cli.console.print_error") as mock_error:
                    result = self.cli.seed("test-example")
                    self.assertEqual(result, EXIT_FAILURE)
                    mock_error.assert_called()

    def test_seed_handles_exception(self):
        with patch.object(
            self.cli._api,
            "seed_example_hook_to_project",
            side_effect=Exception("Error"),
        ):
            with patch("githooklib.cli.console.print_error") as mock_error:
                result = self.cli.seed("test-example")
                self.assertEqual(result, EXIT_FAILURE)
                mock_error.assert_called()
                call_args = str(mock_error.call_args)
                self.assertIn("Error", call_args)

    def test_print_error_writes_to_stderr(self):
        with patch("githooklib.cli.console.print_error") as mock_error:
            print_error("Test error message")
            mock_error.assert_called()
            call_args = str(mock_error.call_args)
            self.assertIn("Test error message", call_args)


if __name__ == "__main__":
    unittest.main()
