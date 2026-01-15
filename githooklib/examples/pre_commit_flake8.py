import sys
from typing import Optional, List

from githooklib import GitHook, GitHookContext, HookResult, get_logger
from githooklib.command import CommandExecutor

logger = get_logger(__name__, "pre-commit")


def _flake8_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.python_module("flake8", ["--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


class Flake8PreCommit(GitHook):
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return ["*.py"]
    
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"
    
    def __init__(self, flake8_args: Optional[List[str]] = None) -> None:
        super().__init__()
        self.flake8_args = flake8_args or []
    
    def execute(self, context: GitHookContext) -> HookResult:
        if not _flake8_exists(self.command_executor):
            logger.warning("flake8 not found. Skipping linting.")
            return HookResult(
                success=True,
                message="flake8 not found. Check skipped.",
            )
        
        logger.info("Running flake8 linting...")
        args = ["."] + self.flake8_args
        result = self.command_executor.python_module("flake8", args)
        
        if not result.success:
            logger.error("Linting failed. Commit aborted.")
            if result.stdout:
                logger.error(result.stdout)
            return HookResult(
                success=False,
                message="Linting failed. Commit aborted.",
                exit_code=1,
            )
        
        logger.success("Linting passed!")
        return HookResult(success=True, message="Linting passed!")


__all__ = ["Flake8PreCommit"]


if __name__ == "__main__":
    sys.exit(Flake8PreCommit().run())

