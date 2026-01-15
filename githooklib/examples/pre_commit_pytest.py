import sys
from typing import Optional, List

from githooklib import GitHook, GitHookContext, HookResult, get_logger
from githooklib.command import CommandExecutor

logger = get_logger(__name__, "pre-commit")


def _pytest_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.python_module("pytest", ["--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


class PytestPreCommit(GitHook):
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return ["*.py", "tests/**/*.py"]
    
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"
    
    def __init__(self, pytest_args: Optional[List[str]] = None) -> None:
        super().__init__()
        self.pytest_args = pytest_args or []
    
    def execute(self, context: GitHookContext) -> HookResult:
        if not _pytest_exists(self.command_executor):
            logger.warning("pytest not found. Skipping tests.")
            return HookResult(
                success=True,
                message="pytest not found. Check skipped.",
            )
        
        logger.info("Running pytest...")
        args = ["--tb=short", "-v"] + self.pytest_args
        result = self.command_executor.python_module("pytest", args)
        
        if not result.success:
            logger.error("Tests failed. Commit aborted.")
            if result.stdout:
                logger.error(result.stdout)
            return HookResult(
                success=False,
                message="Tests failed. Commit aborted.",
                exit_code=1,
            )
        
        logger.success("All tests passed!")
        return HookResult(success=True, message="All tests passed!")


__all__ = ["PytestPreCommit"]


if __name__ == "__main__":
    sys.exit(PytestPreCommit().run())

