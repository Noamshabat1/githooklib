import sys
import re
from typing import Optional, List
from pathlib import Path

from githooklib import GitHook, GitHookContext, HookResult, get_logger

logger = get_logger(__name__, "commit-msg")


CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"(\(.+\))?"
    r"!?:"
    r" .{1,}"
)


COMMIT_TYPES = {
    "feat": "A new feature",
    "fix": "A bug fix",
    "docs": "Documentation only changes",
    "style": "Changes that do not affect the meaning of the code",
    "refactor": "A code change that neither fixes a bug nor adds a feature",
    "perf": "A code change that improves performance",
    "test": "Adding missing tests or correcting existing tests",
    "build": "Changes that affect the build system or external dependencies",
    "ci": "Changes to CI configuration files and scripts",
    "chore": "Other changes that don't modify src or test files",
    "revert": "Reverts a previous commit",
}


class ConventionalCommitMsg(GitHook):
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        return None
    
    @classmethod
    def get_hook_name(cls) -> str:
        return "commit-msg"
    
    def execute(self, context: GitHookContext) -> HookResult:
        if len(context.argv) < 2:
            logger.error("No commit message file provided")
            return HookResult(
                success=False,
                message="No commit message file provided",
                exit_code=1,
            )
        
        commit_msg_file = Path(context.argv[1])
        
        if not commit_msg_file.exists():
            logger.error("Commit message file not found: %s", commit_msg_file)
            return HookResult(
                success=False,
                message=f"Commit message file not found: {commit_msg_file}",
                exit_code=1,
            )
        
        commit_msg = commit_msg_file.read_text(encoding="utf-8").strip()
        
        first_line = commit_msg.split("\n")[0]
        
        if not CONVENTIONAL_COMMIT_PATTERN.match(first_line):
            logger.error("Commit message does not follow Conventional Commits format")
            logger.error("Current message: %s", first_line)
            logger.error("")
            logger.error("Expected format: <type>[optional scope]: <description>")
            logger.error("")
            logger.error("Valid types:")
            for commit_type, description in COMMIT_TYPES.items():
                logger.error("  - %s: %s", commit_type, description)
            logger.error("")
            logger.error("Examples:")
            logger.error("  - feat: add user authentication")
            logger.error("  - fix(api): resolve null pointer exception")
            logger.error("  - docs: update README with installation steps")
            
            return HookResult(
                success=False,
                message="Commit message must follow Conventional Commits format",
                exit_code=1,
            )
        
        logger.success("Commit message follows Conventional Commits format")
        return HookResult(success=True, message="Valid commit message")


__all__ = ["ConventionalCommitMsg"]


if __name__ == "__main__":
    sys.exit(ConventionalCommitMsg().run())

