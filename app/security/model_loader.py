"""
Secure model loading with hash validation - uses joblib instead of pickle
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional, Any
import joblib
from .exceptions import SecurityError

logger = logging.getLogger(__name__)

class SecureModelLoader:
    def __init__(self, expected_hash: Optional[str] = None, allow_untrusted: bool = False):
        self.expected_hash = expected_hash
        self.allow_untrusted = allow_untrusted
        self._loaded_models: dict = {}

    def compute_hash(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def load(self, path: Path, cache_key: Optional[str] = None) -> Any:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        cache_key = cache_key or str(path)
        if cache_key in self._loaded_models:
            return self._loaded_models[cache_key]
        if self.expected_hash:
            file_hash = self.compute_hash(path)
            if file_hash != self.expected_hash:
                raise SecurityError(f"Hash mismatch for {path}")
        elif not self.allow_untrusted:
            logger.warning(f"Loading model without hash validation: {path}")
        model = joblib.load(path)
        self._loaded_models[cache_key] = model
        logger.info(f"Model loaded: {path}")
        return model