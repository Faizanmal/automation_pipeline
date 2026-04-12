"""
File validation for downloaded content.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Constants
MIN_PDF_SIZE = 10 * 1024  # 10 KB
MIN_HTML_SIZE = 100  # 100 bytes
PDF_MAGIC = b"%PDF"
HTML_MAGIC1 = b"<html"
HTML_MAGIC2 = b"<!DOCTYPE"


class ValidationError(Exception):
    """File validation error."""
    pass


def validate_pdf(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate a PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, "File does not exist"
    
    file_size = file_path.stat().st_size
    
    if file_size < MIN_PDF_SIZE:
        return False, f"File too small ({file_size} bytes, minimum {MIN_PDF_SIZE} bytes)"
    
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
        
        if not header.startswith(PDF_MAGIC):
            return False, "File does not start with PDF magic bytes"
        
        return True, None
    
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def validate_html(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate an HTML file.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, "File does not exist"
    
    file_size = file_path.stat().st_size
    
    if file_size < MIN_HTML_SIZE:
        return False, f"File too small ({file_size} bytes, minimum {MIN_HTML_SIZE} bytes)"
    
    try:
        with open(file_path, "rb") as f:
            content = f.read(100)
        
        content_lower = content.lower()
        is_valid = HTML_MAGIC1 in content_lower or HTML_MAGIC2 in content_lower
        
        if not is_valid:
            return False, "File does not appear to be valid HTML"
        
        return True, None
    
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def validate_markdown(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate a Markdown file.
    
    Args:
        file_path: Path to Markdown file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, "File does not exist"
    
    file_size = file_path.stat().st_size
    
    if file_size < 100:
        return False, f"File too small ({file_size} bytes)"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(100)
        
        if not content.strip():
            return False, "File is empty"
        
        return True, None
    
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def validate_file(file_path: Path, file_type: str) -> bool:
    """
    Validate a file based on its type.
    
    Args:
        file_path: Path to file
        file_type: File type (pdf, html, md, markdown)
        
    Returns:
        True if valid, False otherwise
    """
    file_type = file_type.lower()
    
    if file_type == "pdf":
        is_valid, error = validate_pdf(file_path)
    elif file_type in ("html", "htm"):
        is_valid, error = validate_html(file_path)
    elif file_type in ("md", "markdown"):
        is_valid, error = validate_markdown(file_path)
    else:
        logger.warning(f"Unknown file type for validation: {file_type}")
        return True
    
    if not is_valid:
        logger.error(f"File validation failed for {file_path}: {error}")
        return False
    
    logger.debug(f"File validation passed for {file_path}")
    return True


def validate_url(url: str) -> bool:
    """
    Basic URL validation.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    if not url.startswith(("http://", "https://")):
        return False
    
    # Check minimum length
    if len(url) < 10:
        return False
    
    return True
