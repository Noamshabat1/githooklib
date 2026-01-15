from typing import List, Dict, Type
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .hook_step import HookStep
from .chain_result import ChainResult, StepResult
from ..context import GitHookContext
from ..git_hook import GitHook
from ..logger import get_logger
from ..config.config_schema import ChainStepConfig

logger = get_logger()


class HookChain:
    def __init__(self, steps: List[HookStep], max_workers: int = 4) -> None:
        self.steps = steps
        self.max_workers = max_workers
        logger.trace("Created HookChain with %d steps", len(steps))
    
    @classmethod
    def from_config(
        cls,
        chain_config: List[ChainStepConfig],
        available_hooks: Dict[str, Type[GitHook]],
        max_workers: int = 4,
    ) -> "HookChain":
        logger.debug("Creating HookChain from config with %d steps", len(chain_config))
        steps = []
        
        for step_config in chain_config:
            hook_class = None
            if step_config.hook:
                hook_class = available_hooks.get(step_config.hook)
                if not hook_class:
                    logger.warning(
                        "Hook '%s' not found for step '%s'",
                        step_config.hook,
                        step_config.name,
                    )
            
            step = HookStep(
                name=step_config.name,
                hook_class=hook_class,
                command=step_config.command,
                continue_on_failure=step_config.continue_on_failure,
            )
            steps.append(step)
        
        return cls(steps, max_workers)
    
    def execute(self, context: GitHookContext, parallel: bool = False) -> ChainResult:
        logger.info("Executing hook chain with %d steps", len(self.steps))
        start_time = time.time()
        
        if parallel:
            results = self._execute_parallel(context)
        else:
            results = self._execute_sequential(context)
        
        duration_ms = (time.time() - start_time) * 1000
        
        success = all(result.success or result.skipped for result in results)
        
        failed_count = len([r for r in results if not r.success and not r.skipped])
        
        if success:
            message = f"All {len(results)} steps completed successfully"
        else:
            message = f"{failed_count} step(s) failed"
        
        return ChainResult(
            success=success,
            steps=results,
            message=message,
            total_duration_ms=duration_ms,
        )
    
    def _execute_sequential(self, context: GitHookContext) -> List[StepResult]:
        logger.debug("Executing steps sequentially")
        results = []
        
        for step in self.steps:
            logger.debug("Executing step: %s", step.name)
            result = step.execute(context)
            results.append(result)
            
            if not result.success and not step.continue_on_failure:
                logger.warning(
                    "Step '%s' failed, stopping chain execution", step.name
                )
                
                for remaining_step in self.steps[len(results):]:
                    logger.debug("Skipping step: %s", remaining_step.name)
                    results.append(
                        StepResult(
                            step_name=remaining_step.name,
                            success=False,
                            message="Skipped due to previous failure",
                            skipped=True,
                        )
                    )
                break
        
        return results
    
    def _execute_parallel(self, context: GitHookContext) -> List[StepResult]:
        logger.debug("Executing steps in parallel with max %d workers", self.max_workers)
        results: List[StepResult] = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_step = {
                executor.submit(step.execute, context): step for step in self.steps
            }
            
            for future in as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.debug("Step '%s' completed: %s", step.name, result.success)
                except Exception as e:
                    logger.error("Step '%s' raised exception: %s", step.name, e)
                    logger.trace("Exception details: %s", e, exc_info=True)
                    results.append(
                        StepResult(
                            step_name=step.name,
                            success=False,
                            message=f"Exception: {e}",
                            exit_code=1,
                        )
                    )
        
        results.sort(key=lambda r: [s.name for s in self.steps].index(r.step_name))
        
        return results


__all__ = ["HookChain"]

