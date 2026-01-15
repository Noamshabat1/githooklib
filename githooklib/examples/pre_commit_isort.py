import sys
from typing import Optional, List

from githooklib import GitHook, GitHookContext, HookResult, get_logger
from githooklib.command import CommandExecutor, CommandResult

logger = get_logger(__name__, "pre-commit")


def _isort_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.python_module("isort", ["--version"])
    if check_result.exit_code == 127:
        return False
    if not check_result.success and "No module named" in check_result.stderr:
        return False
    return True


def _get_modified_python_files(command_executor: CommandExecutor) -> List[str]:
    result = command_executor.run(["git", "diff", "--name-only", "--cached"])
    if not result.success:
        return []
    files = [
        line.strip() for line in result.stdout.strip().split("\n") if line.strip()
    ]
    return [f for f in files if f.endswith(".py")]


def _stage_files(command_executor: CommandExecutor, files: List[str]) -> CommandResult:
    return command_executor.run(["git", "add"] + files)


class IsortPreCommit(GitHook):
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return ["*.py"]
    
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-commit"
    
    def __init__(self, isort_args: Optional[List[str]] = None, stage_changes: bool = True) -> None:
        super().__init__()
        self.isort_args = isort_args or []
        self.stage_changes = stage_changes
    
    def execute(self, context: GitHookContext) -> HookResult:
        if not _isort_exists(self.command_executor):
            logger.warning("isort not found. Skipping import sorting.")
            return HookResult(
                success=True,
                message="isort not found. Check skipped.",
            )
        
        logger.info("Running isort to sort imports...")
        args = ["."] + self.isort_args
        result = self.command_executor.python_module("isort", args)
        
        if not result.success:
            logger.error("Import sorting failed.")
            if result.stderr:
                logger.error(result.stderr)
            return HookResult(
                success=False,
                message="Import sorting failed.",
                exit_code=1,
            )
        
        if self.stage_changes:
            modified_files = _get_modified_python_files(self.command_executor)
            if modified_files:
                logger.info("Staging %d sorted file(s)...", len(modified_files))
                staging_result = _stage_files(self.command_executor, modified_files)
                if not staging_result.success:
                    logger.error("Failed to stage sorted files.")
                    return HookResult(
                        success=False,
                        message="Failed to stage sorted files.",
                        exit_code=1,
                    )
        
        logger.success("Import sorting completed!")
        return HookResult(success=True, message="Import sorting completed!")


__all__ = ["IsortPreCommit"]


if __name__ == "__main__":
    sys.exit(IsortPreCommit().run())

