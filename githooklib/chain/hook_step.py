from typing import Optional, List, Type
import time

from .chain_result import StepResult
from ..context import GitHookContext
from ..definitions import HookResult
from ..git_hook import GitHook
from ..logger import get_logger
from ..command import CommandExecutor

logger = get_logger()


class HookStep:
    def __init__(
        self,
        name: str,
        hook_class: Optional[Type[GitHook]] = None,
        command: Optional[List[str]] = None,
        continue_on_failure: bool = False,
    ) -> None:
        self.name = name
        self.hook_class = hook_class
        self.command = command
        self.continue_on_failure = continue_on_failure
        
        if not hook_class and not command:
            raise ValueError(f"Step '{name}' must have either hook_class or command")
        
        logger.trace("Created HookStep: %s", name)
    
    def execute(self, context: GitHookContext) -> StepResult:
        logger.debug("Executing step: %s", self.name)
        start_time = time.time()
        
        try:
            if self.hook_class:
                result = self._execute_hook(context)
            elif self.command:
                result = self._execute_command()
            else:
                logger.error("Step '%s' has no hook or command", self.name)
                return StepResult(
                    step_name=self.name,
                    success=False,
                    message="No hook or command configured",
                    exit_code=1,
                )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return StepResult(
                step_name=self.name,
                success=result.success,
                message=result.message,
                exit_code=result.exit_code,
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.error("Error executing step '%s': %s", self.name, e)
            logger.trace("Exception details: %s", e, exc_info=True)
            duration_ms = (time.time() - start_time) * 1000
            return StepResult(
                step_name=self.name,
                success=False,
                message=f"Error: {e}",
                exit_code=1,
                duration_ms=duration_ms,
            )
    
    def _execute_hook(self, context: GitHookContext) -> HookResult:
        logger.trace("Executing hook for step: %s", self.name)
        if not self.hook_class:
            raise ValueError(f"No hook class for step: {self.name}")
        
        hook_instance = self.hook_class()
        exit_code = hook_instance.run()
        
        return HookResult(
            success=exit_code == 0,
            exit_code=exit_code,
        )
    
    def _execute_command(self) -> HookResult:
        logger.trace("Executing command for step: %s", self.name)
        if not self.command:
            raise ValueError(f"No command for step: {self.name}")
        
        executor = CommandExecutor()
        result = executor.run(self.command)
        
        return HookResult(
            success=result.success,
            message=result.stderr if not result.success else None,
            exit_code=result.exit_code,
        )


__all__ = ["HookStep"]

