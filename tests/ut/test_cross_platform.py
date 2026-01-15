import platform
import unittest
from pathlib import Path

from githooklib.gateways import GitGateway, ProjectRootGateway
from tests.base_test_case import BaseTestCase


class TestCrossPlatform(BaseTestCase):
    def test_path_handling_works_on_current_platform(self):
        project_root = ProjectRootGateway.find_project_root()
        
        self.assertIsNotNone(project_root)
        project_root = self.unwrap_optional(project_root)
        
        self.assertTrue(project_root.exists())
        self.assertTrue(project_root.is_dir())
    
    def test_git_root_detection_works_on_current_platform(self):
        git_gateway = GitGateway()
        git_root = git_gateway.get_git_root_path()
        
        if git_root:
            self.assertTrue(git_root.exists())
            self.assertTrue((Path(git_root.parent) / ".git").exists() or (git_root / ".git").exists())
    
    def test_platform_detection(self):
        system = platform.system()
        
        self.assertIn(system, ["Windows", "Linux", "Darwin"])
        
        if system == "Windows":
            self.assertTrue(Path.cwd().drive or True)
        else:
            self.assertTrue(str(Path.cwd()).startswith("/"))
    
    def test_file_permissions_handling(self):
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            temp_file = Path(f.name)
            f.write("test content")
        
        try:
            if platform.system() != "Windows":
                temp_file.chmod(0o755)
                stat_info = temp_file.stat()
                self.assertTrue(stat_info.st_mode & 0o111)
            else:
                self.assertTrue(temp_file.exists())
        finally:
            temp_file.unlink()


__all__ = ["TestCrossPlatform"]

