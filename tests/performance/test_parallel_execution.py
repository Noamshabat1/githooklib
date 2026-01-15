import time
import unittest

from githooklib.execution import ParallelExecutor


class TestParallelExecutionPerformance(unittest.TestCase):
    def test_parallel_execution_faster_than_sequential(self):
        def slow_task():
            time.sleep(0.1)
            return "done"
        
        tasks = {f"task_{i}": slow_task for i in range(10)}
        
        start_sequential = time.time()
        for task in tasks.values():
            task()
        sequential_time = time.time() - start_sequential
        
        executor = ParallelExecutor(max_workers=4)
        start_parallel = time.time()
        results = executor.execute_tasks(tasks, show_progress=False)
        parallel_time = time.time() - start_parallel
        
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r.success for r in results))
        
        self.assertLess(parallel_time, sequential_time * 0.5)
    
    def test_parallel_executor_handles_failures(self):
        def failing_task():
            raise ValueError("Task failed")
        
        def success_task():
            return "success"
        
        tasks = {
            "fail1": failing_task,
            "success1": success_task,
            "fail2": failing_task,
            "success2": success_task,
        }
        
        executor = ParallelExecutor(max_workers=2)
        results = executor.execute_tasks(tasks, show_progress=False)
        
        self.assertEqual(len(results), 4)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        self.assertEqual(len(successful), 2)
        self.assertEqual(len(failed), 2)


__all__ = ["TestParallelExecutionPerformance"]

