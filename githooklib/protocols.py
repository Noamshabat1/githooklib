from typing import Protocol, Optional, List
from pathlib import Path

from .definitions import CommandResult, HookResult
from .context import GitHookContext


class CommandExecutorProtocol(Protocol):
    def run(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        check: bool = False,
        text: bool = True,
        shell: bool = False,
    ) -> CommandResult:
        ...
    
    def python(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        check: bool = False,
        text: bool = True,
        shell: bool = False,
    ) -> CommandResult:
        ...
    
    def python_module(
        self,
        module: str,
        cmd: List[str],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        check: bool = False,
        text: bool = True,
        shell: bool = False,
    ) -> CommandResult:
        ...


class GitHookProtocol(Protocol):
    @classmethod
    def get_hook_name(cls) -> str:
        ...
    
    @classmethod
    def get_file_patterns(cls) -> Optional[List[str]]:
        ...
    
    def execute(self, context: GitHookContext) -> HookResult:
        ...
    
    def run(self) -> int:
        ...
    
    def install(self) -> bool:
        ...
    
    def uninstall(self) -> bool:
        ...


class LoggerProtocol(Protocol):
    def debug(self, message: str, *args, **kwargs) -> None:
        ...
    
    def info(self, message: str, *args, **kwargs) -> None:
        ...
    
    def warning(self, message: str, *args, **kwargs) -> None:
        ...
    
    def error(self, message: str, *args, **kwargs) -> None:
        ...
    
    def trace(self, message: str, *args, **kwargs) -> None:
        ...
    
    def success(self, message: str, *args, **kwargs) -> None:
        ...


class GatewayProtocol(Protocol):
    pass


class GitGatewayProtocol(GatewayProtocol, Protocol):
    def get_git_root_path(self) -> Optional[Path]:
        ...
    
    def get_installed_hooks(self, hooks_dir: Path) -> dict:
        ...
    
    def get_cached_index_files(self) -> List[str]:
        ...
    
    def get_diff_files_between_refs(self, remote_ref: str, local_ref: str) -> List[str]:
        ...
    
    def get_all_modified_files(self) -> List[str]:
        ...


__all__ = [
    "CommandExecutorProtocol",
    "GitHookProtocol",
    "LoggerProtocol",
    "GatewayProtocol",
    "GitGatewayProtocol",
]

