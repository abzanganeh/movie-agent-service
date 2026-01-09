"""
File upload validation for security.

OOP: Single Responsibility - Only handles file validation.
"""

from pathlib import Path
from typing import Tuple, Optional
import imghdr

from .exceptions import FileValidationError


class FileValidator:
    """
    Validates uploaded files for security.
    
    Prevents malicious file uploads by validating type, size, and content.
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}

    @staticmethod
    def validate_image_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file for security.
        
        :param file_path: Path to the file to validate
        :return: Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, "File does not exist"

        if path.suffix.lower() not in FileValidator.ALLOWED_EXTENSIONS:
            return False, f"File extension '{path.suffix}' not allowed. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"

        try:
            file_size = path.stat().st_size
        except OSError as e:
            return False, f"Cannot read file size: {str(e)}"

        if file_size > FileValidator.MAX_FILE_SIZE:
            return False, f"File size {file_size} bytes exceeds maximum {FileValidator.MAX_FILE_SIZE} bytes"

        if file_size == 0:
            return False, "File is empty"

        try:
            detected_type = imghdr.what(file_path)
            if not detected_type:
                return False, "File is not a valid image"

            if detected_type not in {"jpeg", "png"}:
                return False, f"Image type '{detected_type}' not allowed. Allowed: jpeg, png"

        except Exception as e:
            return False, f"File type detection failed: {str(e)}"

        try:
            from PIL import Image

            with Image.open(file_path) as img:
                img.verify()

            with Image.open(file_path) as img:
                if img.width > 10000 or img.height > 10000:
                    return False, "Image dimensions too large (max 10000x10000)"

                if img.width == 0 or img.height == 0:
                    return False, "Image has invalid dimensions"

        except ImportError:
            pass
        except Exception as e:
            return False, f"Image validation failed: {str(e)}"

        return True, None

    @staticmethod
    def validate_file_path(file_path: str) -> str:
        """
        Validate file path to prevent path traversal attacks.
        
        :param file_path: File path to validate
        :return: Validated absolute path
        :raises FileValidationError: If path is invalid
        """
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileValidationError("File path does not exist")

        if ".." in str(path):
            raise FileValidationError("Path traversal detected in file path")

        return str(path)

