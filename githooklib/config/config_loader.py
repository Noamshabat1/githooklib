from pathlib import Path
from typing import Optional, Any, Dict
import logging

from .config_schema import (
    GithooklibConfig,
    HookConfig,
    HookChainConfig,
    ChainStepConfig,
    PerformanceConfig,
    NotificationsConfig,
    NotificationProviderConfig,
)
from ..gateways import ProjectRootGateway
from ..logger import get_logger

logger = get_logger()

_global_config: Optional[GithooklibConfig] = None


def _load_yaml(config_path: Path) -> Dict[str, Any]:
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        logger.warning("PyYAML not installed. Cannot load YAML config files.")
        logger.debug("Install with: pip install pyyaml")
        return {}
    except Exception as e:
        logger.error("Failed to load YAML config from %s: %s", config_path, e)
        logger.trace("Exception details: %s", e, exc_info=True)
        return {}


def _load_toml(config_path: Path) -> Dict[str, Any]:
    try:
        import tomllib
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        try:
            import toml
            with open(config_path, "r", encoding="utf-8") as f:
                return toml.load(f)
        except ImportError:
            logger.warning("No TOML library installed. Cannot load TOML config files.")
            logger.debug("Install with: pip install toml")
            return {}
    except Exception as e:
        logger.error("Failed to load TOML config from %s: %s", config_path, e)
        logger.trace("Exception details: %s", e, exc_info=True)
        return {}


def _parse_notification_provider(data: Dict[str, Any]) -> NotificationProviderConfig:
    return NotificationProviderConfig(
        enabled=data.get("enabled", True),
        webhook_url=data.get("webhook_url"),
        email_to=data.get("email_to"),
        smtp_server=data.get("smtp_server"),
        smtp_port=data.get("smtp_port", 587),
        smtp_username=data.get("smtp_username"),
        smtp_password=data.get("smtp_password"),
    )


def _parse_notifications(data: Dict[str, Any]) -> NotificationsConfig:
    return NotificationsConfig(
        enabled=data.get("enabled", False),
        on_failure=data.get("on_failure", True),
        on_success=data.get("on_success", False),
        slack=_parse_notification_provider(data.get("slack", {})),
        email=_parse_notification_provider(data.get("email", {})),
        webhook=_parse_notification_provider(data.get("webhook", {})),
        desktop=_parse_notification_provider(data.get("desktop", {})),
    )


def _parse_performance(data: Dict[str, Any]) -> PerformanceConfig:
    cache_dir = data.get("cache_dir")
    return PerformanceConfig(
        caching_enabled=data.get("caching_enabled", True),
        parallel_execution=data.get("parallel_execution", False),
        max_workers=data.get("max_workers", 4),
        cache_dir=Path(cache_dir) if cache_dir else None,
    )


def _parse_chain_step(data: Dict[str, Any]) -> ChainStepConfig:
    return ChainStepConfig(
        name=data["name"],
        hook=data.get("hook"),
        command=data.get("command"),
        continue_on_failure=data.get("continue_on_failure", False),
        parallel=data.get("parallel", False),
        file_patterns=data.get("file_patterns"),
    )


def _parse_hook_chain(data: Dict[str, Any]) -> HookChainConfig:
    steps = [_parse_chain_step(step) for step in data.get("chain", [])]
    return HookChainConfig(
        enabled=data.get("enabled", True),
        chain=steps,
    )


def _parse_hook_config(data: Dict[str, Any]) -> HookConfig:
    chain_data = data.get("chain")
    chain = _parse_hook_chain(chain_data) if chain_data else None
    
    return HookConfig(
        file_patterns=data.get("file_patterns"),
        enabled=data.get("enabled", True),
        settings=data.get("settings", {}),
        chain=chain,
    )


def _parse_config_data(data: Dict[str, Any]) -> GithooklibConfig:
    hooks_data = data.get("hooks", {})
    hooks = {name: _parse_hook_config(hook_data) for name, hook_data in hooks_data.items()}
    
    notifications_data = data.get("notifications", {})
    notifications = _parse_notifications(notifications_data)
    
    performance_data = data.get("performance", {})
    performance = _parse_performance(performance_data)
    
    return GithooklibConfig(
        hook_search_paths=data.get("hook_search_paths", ["githooks"]),
        log_level=data.get("log_level", "INFO"),
        notifications=notifications,
        performance=performance,
        hooks=hooks,
    )


class ConfigLoader:
    @staticmethod
    def find_config_file(start_path: Optional[Path] = None) -> Optional[Path]:
        if start_path is None:
            start_path = ProjectRootGateway.find_project_root()
            if not start_path:
                start_path = Path.cwd()
        
        logger.trace("Searching for config file starting from: %s", start_path)
        
        config_names = [".githooklib.yaml", ".githooklib.yml", ".githooklib.toml"]
        
        search_paths = [start_path] + list(start_path.parents)
        
        for search_path in search_paths:
            for config_name in config_names:
                config_path = search_path / config_name
                logger.trace("Checking for config at: %s", config_path)
                if config_path.exists():
                    logger.debug("Found config file: %s", config_path)
                    return config_path
        
        logger.debug("No config file found")
        return None
    
    @staticmethod
    def load_config(config_path: Optional[Path] = None) -> GithooklibConfig:
        if config_path is None:
            config_path = ConfigLoader.find_config_file()
        
        if config_path is None:
            logger.debug("Using default configuration")
            return GithooklibConfig()
        
        logger.info("Loading config from: %s", config_path)
        
        if config_path.suffix in [".yaml", ".yml"]:
            data = _load_yaml(config_path)
        elif config_path.suffix == ".toml":
            data = _load_toml(config_path)
        else:
            logger.warning("Unknown config file format: %s", config_path.suffix)
            return GithooklibConfig()
        
        try:
            config = _parse_config_data(data)
            logger.debug("Config loaded successfully")
            return config
        except Exception as e:
            logger.error("Failed to parse config: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
            return GithooklibConfig()
    
    @staticmethod
    def create_default_config_file(target_path: Path) -> bool:
        logger.debug("Creating default config file at: %s", target_path)
        
        default_config = """# Githooklib Configuration
# See https://github.com/danielnachumdev/githooklib for documentation

# Directories to search for hook implementations
hook_search_paths:
  - githooks

# Logging level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level: INFO

# Performance settings
performance:
  caching_enabled: true
  parallel_execution: false
  max_workers: 4

# Notification settings
notifications:
  enabled: false
  on_failure: true
  on_success: false
  
  slack:
    enabled: false
    # webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  
  desktop:
    enabled: false

# Hook-specific configuration
hooks:
  pre-commit:
    enabled: true
    file_patterns:
      - "*.py"
    
    # Example: Chain multiple tools together
    # chain:
    #   enabled: true
    #   chain:
    #     - name: format
    #       hook: black
    #       continue_on_failure: false
    #     - name: lint
    #       hook: flake8
    #       parallel: true
    #     - name: type-check
    #       hook: mypy
    #       parallel: true
"""
        
        try:
            target_path.write_text(default_config, encoding="utf-8")
            logger.success("Created default config file: %s", target_path)
            return True
        except Exception as e:
            logger.error("Failed to create config file: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
            return False


def get_config(reload: bool = False) -> GithooklibConfig:
    global _global_config
    
    if _global_config is None or reload:
        logger.trace("Loading global config")
        _global_config = ConfigLoader.load_config()
    
    return _global_config


__all__ = ["ConfigLoader", "get_config"]

