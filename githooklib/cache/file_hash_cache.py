from pathlib import Path
from typing import Dict, Optional, Set
import hashlib
import json
import time

from ..gateways import ProjectRootGateway, GitGateway
from ..logger import get_logger

logger = get_logger()

_global_cache: Optional["FileHashCache"] = None


def _compute_file_hash(file_path: Path) -> str:
    logger.trace("Computing hash for file: %s", file_path)
    try:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()
        logger.trace("Hash for %s: %s", file_path, file_hash)
        return file_hash
    except Exception as e:
        logger.trace("Error computing hash for %s: %s", file_path, e)
        return ""


class FileHashCache:
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        if cache_dir is None:
            git_gateway = GitGateway()
            git_root = git_gateway.get_git_root_path()
            if git_root:
                cache_dir = git_root / "hooks" / ".cache"
            else:
                project_root = ProjectRootGateway.find_project_root()
                if project_root:
                    cache_dir = project_root / ".githooklib_cache"
                else:
                    cache_dir = Path.cwd() / ".githooklib_cache"
        
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "file_hashes.json"
        self._cache: Dict[str, str] = {}
        self._dirty: bool = False
        
        logger.trace("FileHashCache initialized with cache_dir: %s", cache_dir)
        self._load()
    
    def _load(self) -> None:
        logger.trace("Loading cache from: %s", self.cache_file)
        if not self.cache_file.exists():
            logger.trace("Cache file does not exist, starting with empty cache")
            return
        
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            logger.debug("Loaded %d entries from cache", len(self._cache))
        except Exception as e:
            logger.warning("Failed to load cache: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
            self._cache = {}
    
    def _save(self) -> None:
        if not self._dirty:
            logger.trace("Cache not dirty, skipping save")
            return
        
        logger.trace("Saving cache to: %s", self.cache_file)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
            self._dirty = False
            logger.debug("Saved %d entries to cache", len(self._cache))
        except Exception as e:
            logger.warning("Failed to save cache: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
    
    def get_hash(self, file_path: Path) -> Optional[str]:
        key = str(file_path.resolve())
        return self._cache.get(key)
    
    def update_hash(self, file_path: Path, file_hash: Optional[str] = None) -> str:
        key = str(file_path.resolve())
        
        if file_hash is None:
            file_hash = _compute_file_hash(file_path)
        
        old_hash = self._cache.get(key)
        if old_hash != file_hash:
            self._cache[key] = file_hash
            self._dirty = True
            logger.trace("Updated hash for %s: %s -> %s", file_path, old_hash, file_hash)
        
        return file_hash
    
    def has_changed(self, file_path: Path) -> bool:
        if not file_path.exists():
            logger.trace("File does not exist: %s", file_path)
            return True
        
        current_hash = _compute_file_hash(file_path)
        cached_hash = self.get_hash(file_path)
        
        if cached_hash is None:
            logger.trace("File not in cache: %s", file_path)
            self.update_hash(file_path, current_hash)
            return True
        
        changed = current_hash != cached_hash
        logger.trace(
            "File %s changed: %s (current: %s, cached: %s)",
            file_path,
            changed,
            current_hash[:8],
            cached_hash[:8],
        )
        
        if changed:
            self.update_hash(file_path, current_hash)
        
        return changed
    
    def get_changed_files(self, file_paths: list[Path]) -> Set[Path]:
        logger.debug("Checking %d files for changes", len(file_paths))
        changed = set()
        
        for file_path in file_paths:
            if self.has_changed(file_path):
                changed.add(file_path)
        
        logger.debug("Found %d changed files", len(changed))
        return changed
    
    def clear(self) -> None:
        logger.debug("Clearing cache")
        self._cache.clear()
        self._dirty = True
        self._save()
    
    def cleanup_stale_entries(self, max_age_days: int = 30) -> None:
        logger.debug("Cleaning up stale cache entries older than %d days", max_age_days)
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        stale_keys = []
        for key in self._cache:
            file_path = Path(key)
            if not file_path.exists():
                stale_keys.append(key)
                continue
            
            try:
                mtime = file_path.stat().st_mtime
                if current_time - mtime > max_age_seconds:
                    stale_keys.append(key)
            except Exception:
                stale_keys.append(key)
        
        for key in stale_keys:
            del self._cache[key]
        
        if stale_keys:
            self._dirty = True
            logger.debug("Removed %d stale entries from cache", len(stale_keys))
    
    def __enter__(self) -> "FileHashCache":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._save()


def get_cache(cache_dir: Optional[Path] = None) -> FileHashCache:
    global _global_cache
    
    if _global_cache is None:
        logger.trace("Creating global cache instance")
        _global_cache = FileHashCache(cache_dir)
    
    return _global_cache


__all__ = ["FileHashCache", "get_cache"]

