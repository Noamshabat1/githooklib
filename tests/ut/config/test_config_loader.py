import tempfile
from pathlib import Path

from githooklib.config import ConfigLoader, GithooklibConfig
from githooklib.config.config_schema import (
    PerformanceConfig,
    NotificationsConfig,
    NotificationProviderConfig,
    ChainStepConfig,
)
from tests.base_test_case import BaseTestCase


class TestConfigLoader(BaseTestCase):
    def test_load_default_config_when_no_file_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigLoader.load_config(Path(temp_dir) / "nonexistent.yaml")
            
            self.assertIsInstance(config, GithooklibConfig)
            self.assertEqual(config.hook_search_paths, ["githooks"])
            self.assertEqual(config.log_level, "INFO")
    
    def test_create_default_config_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".githooklib.yaml"
            
            success = ConfigLoader.create_default_config_file(config_path)
            
            self.assertTrue(success)
            self.assertTrue(config_path.exists())
            
            content = config_path.read_text(encoding="utf-8")
            self.assertIn("hook_search_paths", content)
            self.assertIn("log_level", content)
            self.assertIn("notifications", content)
    
    def test_load_yaml_config_with_custom_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".githooklib.yaml"
            config_path.write_text("""
hook_search_paths:
  - custom_hooks
  - another_dir

log_level: DEBUG

performance:
  caching_enabled: true
  parallel_execution: true
  max_workers: 8
""", encoding="utf-8")
            
            config = ConfigLoader.load_config(config_path)
            
            self.assertEqual(config.hook_search_paths, ["custom_hooks", "another_dir"])
            self.assertEqual(config.log_level, "DEBUG")
            self.assertTrue(config.performance.caching_enabled)
            self.assertTrue(config.performance.parallel_execution)
            self.assertEqual(config.performance.max_workers, 8)


class TestConfigValidation(BaseTestCase):
    def test_invalid_log_level_raises_error(self):
        with self.assertRaises(ValueError) as context:
            GithooklibConfig(log_level="INVALID_LEVEL")
        
        self.assertIn("Invalid log_level", str(context.exception))
        self.assertIn("INVALID_LEVEL", str(context.exception))
    
    def test_valid_log_levels_accepted(self):
        valid_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            with self.subTest(level=level):
                config = GithooklibConfig(log_level=level)
                self.assertEqual(config.log_level, level)
    
    def test_empty_hook_search_paths_raises_error(self):
        with self.assertRaises(ValueError) as context:
            GithooklibConfig(hook_search_paths=[])
        
        self.assertIn("hook_search_paths cannot be empty", str(context.exception))
    
    def test_max_workers_too_low_raises_error(self):
        with self.assertRaises(ValueError) as context:
            PerformanceConfig(max_workers=0)
        
        self.assertIn("max_workers must be at least 1", str(context.exception))
    
    def test_max_workers_too_high_raises_error(self):
        with self.assertRaises(ValueError) as context:
            PerformanceConfig(max_workers=101)
        
        self.assertIn("max_workers should not exceed 100", str(context.exception))
    
    def test_valid_max_workers_range(self):
        for workers in [1, 4, 50, 100]:
            with self.subTest(workers=workers):
                config = PerformanceConfig(max_workers=workers)
                self.assertEqual(config.max_workers, workers)
    
    def test_invalid_smtp_port_raises_error(self):
        with self.subTest("port_too_low"):
            with self.assertRaises(ValueError) as context:
                NotificationProviderConfig(smtp_port=0)
            self.assertIn("smtp_port must be between 1 and 65535", str(context.exception))
        
        with self.subTest("port_too_high"):
            with self.assertRaises(ValueError) as context:
                NotificationProviderConfig(smtp_port=70000)
            self.assertIn("smtp_port must be between 1 and 65535", str(context.exception))
    
    def test_email_notifications_without_smtp_server_raises_error(self):
        email_config = NotificationProviderConfig(enabled=True, smtp_server=None, email_to=["test@test.com"])
        
        with self.assertRaises(ValueError) as context:
            NotificationsConfig(enabled=True, email=email_config)
        
        self.assertIn("Email notifications enabled but smtp_server not configured", str(context.exception))
    
    def test_email_notifications_without_recipients_raises_error(self):
        email_config = NotificationProviderConfig(enabled=True, smtp_server="smtp.example.com", email_to=None)
        
        with self.assertRaises(ValueError) as context:
            NotificationsConfig(enabled=True, email=email_config)
        
        self.assertIn("Email notifications enabled but email_to not configured", str(context.exception))
    
    def test_webhook_notifications_without_url_raises_error(self):
        webhook_config = NotificationProviderConfig(enabled=True, webhook_url=None)
        email_config = NotificationProviderConfig(enabled=False)
        slack_config = NotificationProviderConfig(enabled=False)
        
        with self.assertRaises(ValueError) as context:
            NotificationsConfig(enabled=True, webhook=webhook_config, email=email_config, slack=slack_config)
        
        self.assertIn("Webhook notifications enabled but webhook_url not configured", str(context.exception))
    
    def test_slack_notifications_without_url_raises_error(self):
        slack_config = NotificationProviderConfig(enabled=True, webhook_url=None)
        email_config = NotificationProviderConfig(enabled=False)
        webhook_config = NotificationProviderConfig(enabled=False)
        
        with self.assertRaises(ValueError) as context:
            NotificationsConfig(enabled=True, slack=slack_config, email=email_config, webhook=webhook_config)
        
        self.assertIn("Slack notifications enabled but webhook_url not configured", str(context.exception))
    
    def test_notifications_not_validated_when_disabled(self):
        email_config = NotificationProviderConfig(enabled=True, smtp_server=None)
        config = NotificationsConfig(enabled=False, email=email_config)
        self.assertFalse(config.enabled)
    
    def test_chain_step_without_hook_or_command_raises_error(self):
        with self.assertRaises(ValueError) as context:
            ChainStepConfig(name="test_step", hook=None, command=None)
        
        self.assertIn("must have either 'hook' or 'command'", str(context.exception))
    
    def test_chain_step_with_both_hook_and_command_raises_error(self):
        with self.assertRaises(ValueError) as context:
            ChainStepConfig(name="test_step", hook="my-hook", command=["echo", "test"])
        
        self.assertIn("cannot have both 'hook' and 'command'", str(context.exception))
    
    def test_chain_step_with_hook_only_succeeds(self):
        step = ChainStepConfig(name="test_step", hook="my-hook")
        self.assertEqual(step.name, "test_step")
        self.assertEqual(step.hook, "my-hook")
        self.assertIsNone(step.command)
    
    def test_chain_step_with_command_only_succeeds(self):
        step = ChainStepConfig(name="test_step", command=["echo", "test"])
        self.assertEqual(step.name, "test_step")
        self.assertIsNone(step.hook)
        self.assertEqual(step.command, ["echo", "test"])


__all__ = ["TestConfigLoader", "TestConfigValidation"]

