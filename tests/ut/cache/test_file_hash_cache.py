import tempfile
from pathlib import Path

from githooklib.cache import FileHashCache
from tests.base_test_case import BaseTestCase


class TestFileHashCache(BaseTestCase):
    def test_file_hash_computed_correctly(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            temp_file = Path(f.name)
            f.write("test content")
        
        try:
            with tempfile.TemporaryDirectory() as cache_dir:
                cache = FileHashCache(cache_dir=Path(cache_dir))
                
                file_hash = cache.update_hash(temp_file)
                
                self.assertIsNotNone(file_hash)
                self.assertTrue(len(file_hash) > 0)
                
                cached_hash = cache.get_hash(temp_file)
                self.assertEqual(file_hash, cached_hash)
        finally:
            temp_file.unlink()
    
    def test_file_change_detected(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            temp_file = Path(f.name)
            f.write("original content")
        
        try:
            with tempfile.TemporaryDirectory() as cache_dir:
                cache = FileHashCache(cache_dir=Path(cache_dir))
                
                original_hash = cache.update_hash(temp_file)
                
                self.assertFalse(cache.has_changed(temp_file))
                
                temp_file.write_text("modified content", encoding="utf-8")
                
                self.assertTrue(cache.has_changed(temp_file))
                
                new_hash = cache.get_hash(temp_file)
                self.assertNotEqual(original_hash, new_hash)
        finally:
            temp_file.unlink()
    
    def test_cache_persistence(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            temp_file = Path(f.name)
            f.write("test content")
        
        try:
            with tempfile.TemporaryDirectory() as cache_dir:
                cache_dir_path = Path(cache_dir)
                
                cache1 = FileHashCache(cache_dir=cache_dir_path)
                original_hash = cache1.update_hash(temp_file)
                cache1._save()
                
                cache2 = FileHashCache(cache_dir=cache_dir_path)
                loaded_hash = cache2.get_hash(temp_file)
                
                self.assertEqual(original_hash, loaded_hash)
        finally:
            temp_file.unlink()


__all__ = ["TestFileHashCache"]

