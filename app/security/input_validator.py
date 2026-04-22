"""
Input validation for API requests
"""
import base64
import logging
from .exceptions import InvalidInputError

logger = logging.getLogger(__name__)
DEFAULT_MAX_IMAGE_SIZE_MB = 10

def validate_image_size(base64_data: str, max_size_mb: int = DEFAULT_MAX_IMAGE_SIZE_MB) -> int:
    if not base64_data:
        raise InvalidInputError("Empty image data")
    if base64_data.startswith('data:'):
        base64_data = base64_data.split(',', 1)[1]
    size_bytes = len(base64_data) * 3 / 4
    if size_bytes > max_size_mb * 1024 * 1024:
        raise InvalidInputError(f"Image size ({size_bytes/1024/1024:.2f}MB) exceeds {max_size_mb}MB")
    return int(size_bytes)

def validate_base64_image(base64_data: str) -> bytes:
    if not base64_data:
        raise InvalidInputError("Empty image data")
    if base64_data.startswith('data:'):
        base64_data = base64_data.split(',', 1)[1]
    try:
        decoded = base64.b64decode(base64_data.strip())
        if len(decoded) == 0:
            raise InvalidInputError("Decoded image is empty")
        return decoded
    except Exception as e:
        raise InvalidInputError(f"Invalid base64: {e}")