from dataclasses import dataclass, field
from typing import List, Optional
from ..constants import EXIT_SUCCESS, EXIT_FAILURE


@dataclass
class StepResult:
    step_name: str
    success: bool
    message: Optional[str] = None
    exit_code: int = EXIT_SUCCESS
    skipped: bool = False
    duration_ms: float = 0.0
    
    def __post_init__(self) -> None:
        if self.exit_code == EXIT_SUCCESS and not self.success:
            self.exit_code = EXIT_FAILURE
        elif self.exit_code != EXIT_SUCCESS and self.success:
            self.exit_code = EXIT_SUCCESS


@dataclass
class ChainResult:
    success: bool
    steps: List[StepResult] = field(default_factory=list)
    message: Optional[str] = None
    exit_code: int = EXIT_SUCCESS
    total_duration_ms: float = 0.0
    
    def __post_init__(self) -> None:
        if not self.steps:
            return
        
        if self.exit_code == EXIT_SUCCESS and not self.success:
            self.exit_code = EXIT_FAILURE
        elif self.exit_code != EXIT_SUCCESS and self.success:
            self.exit_code = EXIT_SUCCESS
        
        self.total_duration_ms = sum(step.duration_ms for step in self.steps)
    
    def get_failed_steps(self) -> List[StepResult]:
        return [step for step in self.steps if not step.success and not step.skipped]
    
    def get_successful_steps(self) -> List[StepResult]:
        return [step for step in self.steps if step.success and not step.skipped]
    
    def get_skipped_steps(self) -> List[StepResult]:
        return [step for step in self.steps if step.skipped]


__all__ = ["StepResult", "ChainResult"]

