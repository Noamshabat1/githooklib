from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


@dataclass
class NotificationProviderConfig:
    enabled: bool = True
    webhook_url: Optional[str] = None
    email_to: Optional[List[str]] = None
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None


@dataclass
class NotificationsConfig:
    enabled: bool = False
    on_failure: bool = True
    on_success: bool = False
    slack: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)
    email: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)
    webhook: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)
    desktop: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)


@dataclass
class ChainStepConfig:
    name: str
    hook: Optional[str] = None
    command: Optional[List[str]] = None
    continue_on_failure: bool = False
    parallel: bool = False
    file_patterns: Optional[List[str]] = None


@dataclass
class HookChainConfig:
    enabled: bool = True
    chain: List[ChainStepConfig] = field(default_factory=list)


@dataclass
class PerformanceConfig:
    caching_enabled: bool = True
    parallel_execution: bool = False
    max_workers: int = 4
    cache_dir: Optional[Path] = None


@dataclass
class HookConfig:
    file_patterns: Optional[List[str]] = None
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    chain: Optional[HookChainConfig] = None


@dataclass
class GithooklibConfig:
    hook_search_paths: List[str] = field(default_factory=lambda: ["githooks"])
    log_level: str = "INFO"
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    hooks: Dict[str, HookConfig] = field(default_factory=dict)

    def get_log_level(self) -> int:
        level_map = {
            "TRACE": 5,
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(self.log_level.upper(), logging.INFO)


__all__ = [
    "GithooklibConfig",
    "HookConfig",
    "HookChainConfig",
    "ChainStepConfig",
    "PerformanceConfig",
    "NotificationsConfig",
    "NotificationProviderConfig",
]

