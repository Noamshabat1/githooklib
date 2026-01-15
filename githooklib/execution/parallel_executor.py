from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Callable, TypeVar, Generic, Dict
import time

from ..logger import get_logger

logger = get_logger()

T = TypeVar("T")


class TaskResult(Generic[T]):
    def __init__(self, task_id: str, success: bool, result: T, duration_ms: float, error: Exception = None) -> None:
        self.task_id = task_id
        self.success = success
        self.result = result
        self.duration_ms = duration_ms
        self.error = error


class ParallelExecutor:
    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers
        logger.trace("ParallelExecutor initialized with max_workers: %d", max_workers)
    
    def execute_tasks(
        self,
        tasks: Dict[str, Callable[[], T]],
        show_progress: bool = True,
    ) -> List[TaskResult[T]]:
        logger.debug("Executing %d tasks in parallel with %d workers", len(tasks), self.max_workers)
        
        if not tasks:
            logger.trace("No tasks to execute")
            return []
        
        results: List[TaskResult[T]] = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_id: Dict[Future, str] = {}
            task_start_times: Dict[str, float] = {}
            
            for task_id, task_func in tasks.items():
                logger.trace("Submitting task: %s", task_id)
                future = executor.submit(self._execute_task, task_id, task_func)
                future_to_id[future] = task_id
                task_start_times[task_id] = time.time()
            
            completed_count = 0
            total_count = len(tasks)
            
            if show_progress:
                try:
                    from tqdm import tqdm
                    progress_bar = tqdm(total=total_count, desc="Executing tasks", unit="task")
                except ImportError:
                    logger.trace("tqdm not available, skipping progress bar")
                    progress_bar = None
            else:
                progress_bar = None
            
            for future in as_completed(future_to_id):
                task_id = future_to_id[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    duration_ms = (time.time() - task_start_times[task_id]) * 1000
                    
                    task_result = TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration_ms=duration_ms,
                    )
                    results.append(task_result)
                    logger.debug("Task '%s' completed successfully (%.2fms)", task_id, duration_ms)
                    
                except Exception as e:
                    duration_ms = (time.time() - task_start_times[task_id]) * 1000
                    logger.error("Task '%s' failed: %s", task_id, e)
                    logger.trace("Exception details: %s", e, exc_info=True)
                    
                    task_result = TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        duration_ms=duration_ms,
                        error=e,
                    )
                    results.append(task_result)
                
                if progress_bar:
                    progress_bar.update(1)
                    progress_bar.set_postfix(
                        completed=f"{completed_count}/{total_count}",
                        success=sum(1 for r in results if r.success),
                    )
            
            if progress_bar:
                progress_bar.close()
        
        successful = sum(1 for r in results if r.success)
        logger.debug(
            "Parallel execution complete: %d/%d tasks successful",
            successful,
            len(results),
        )
        
        return results
    
    def _execute_task(self, task_id: str, task_func: Callable[[], T]) -> T:
        logger.trace("Executing task: %s", task_id)
        return task_func()


__all__ = ["ParallelExecutor", "TaskResult"]

