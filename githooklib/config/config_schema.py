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

    def __post_init__(self) -> None:
        if self.smtp_port < 1 or self.smtp_port > 65535:
            raise ValueError(f"smtp_port must be between 1 and 65535, got {self.smtp_port}")


@dataclass
class NotificationsConfig:
    enabled: bool = False
    on_failure: bool = True
    on_success: bool = False
    slack: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)
    email: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)
    webhook: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)
    desktop: NotificationProviderConfig = field(default_factory=NotificationProviderConfig)

    def __post_init__(self) -> None:
        if self.enabled and self.email.enabled:
            if not self.email.smtp_server:
                raise ValueError("Email notifications enabled but smtp_server not configured")
            if not self.email.email_to:
                raise ValueError("Email notifications enabled but email_to not configured")
        
        if self.enabled and self.webhook.enabled:
            if not self.webhook.webhook_url:
                raise ValueError("Webhook notifications enabled but webhook_url not configured")
        
        if self.enabled and self.slack.enabled:
            if not self.slack.webhook_url:
                raise ValueError("Slack notifications enabled but webhook_url not configured")


@dataclass
class ChainStepConfig:
    name: str
    hook: Optional[str] = None
    command: Optional[List[str]] = None
    continue_on_failure: bool = False
    parallel: bool = False
    file_patterns: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if not self.hook and not self.command:
            raise ValueError(f"Chain step '{self.name}' must have either 'hook' or 'command'")
        if self.hook and self.command:
            raise ValueError(
                f"Chain step '{self.name}' cannot have both 'hook' and 'command'"
            )


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

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError(f"max_workers must be at least 1, got {self.max_workers}")
        if self.max_workers > 100:
            raise ValueError(f"max_workers should not exceed 100 (got {self.max_workers})")


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

    def __post_init__(self) -> None:
        valid_log_levels = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: '{self.log_level}'. "
                f"Must be one of: {', '.join(sorted(valid_log_levels))}"
            )
        
        if not self.hook_search_paths:
            raise ValueError("hook_search_paths cannot be empty")

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

