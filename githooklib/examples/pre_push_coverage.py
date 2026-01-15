import sys
from typing import Optional, List
import re

from githooklib import GitHook, GitHookContext, HookResult, get_logger
from githooklib.command import CommandExecutor

logger = get_logger(__name__, "pre-push")


def _pytest_cov_exists(command_executor: CommandExecutor) -> bool:
    check_result = command_executor.python_module("pytest", ["--version"])
    if not check_result.success:
        return False
    
    cov_result = command_executor.run(["python", "-c", "import pytest_cov"])
    return cov_result.success


def _extract_coverage_percentage(output: str) -> Optional[float]:
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if match:
        return float(match.group(1))
    
    match = re.search(r"(\d+)%", output)
    if match:
        return float(match.group(1))
    
    return None


class CoveragePrePush(GitHook):
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return ["*.py", "tests/**/*.py"]
    
    @classmethod
    def get_hook_name(cls) -> str:
        return "pre-push"
    
    def __init__(self, min_coverage: float = 80.0) -> None:
        super().__init__()
        self.min_coverage = min_coverage
    
    def execute(self, context: GitHookContext) -> HookResult:
        if not _pytest_cov_exists(self.command_executor):
            logger.warning("pytest-cov not found. Skipping coverage check.")
            return HookResult(
                success=True,
                message="pytest-cov not found. Check skipped.",
            )
        
        logger.info("Running tests with coverage (minimum: %.1f%%)...", self.min_coverage)
        result = self.command_executor.python_module(
            "pytest",
            ["--cov=.", "--cov-report=term-missing", "--tb=short"],
        )
        
        if not result.success:
            logger.error("Tests failed. Push aborted.")
            return HookResult(
                success=False,
                message="Tests failed. Push aborted.",
                exit_code=1,
            )
        
        coverage = _extract_coverage_percentage(result.stdout)
        
        if coverage is None:
            logger.warning("Could not extract coverage percentage from output")
            return HookResult(
                success=True,
                message="Coverage check skipped (could not parse output)",
            )
        
        logger.info("Current coverage: %.1f%%", coverage)
        
        if coverage < self.min_coverage:
            logger.error(
                "Coverage %.1f%% is below minimum threshold of %.1f%%. Push aborted.",
                coverage,
                self.min_coverage,
            )
            return HookResult(
                success=False,
                message=f"Coverage {coverage:.1f}% below minimum {self.min_coverage:.1f}%",
                exit_code=1,
            )
        
        logger.success("Coverage check passed (%.1f%%)!", coverage)
        return HookResult(success=True, message=f"Coverage: {coverage:.1f}%")


__all__ = ["CoveragePrePush"]


if __name__ == "__main__":
    sys.exit(CoveragePrePush().run())

