import tempfile
from pathlib import Path

from githooklib.config import ConfigLoader, GithooklibConfig
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


__all__ = ["TestConfigLoader"]

