from abc import ABC, abstractmethod
from typing import Optional


class BaseNotifier(ABC):
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
    
    @abstractmethod
    def send(
        self,
        hook_name: str,
        success: bool,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ) -> bool:
        pass
    
    def is_enabled(self) -> bool:
        return self.enabled


__all__ = ["BaseNotifier"]

