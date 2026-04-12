"""
Utility functions for the data pipeline.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("pipeline.log"),
        ],
    )


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing trailing slashes and query params.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    url = url.rstrip("/")
    if "?" in url:
        url = url.split("?")[0]
    return url


def generate_slug(text: str) -> str:
    """
    Generate a URL-safe slug from text.
    
    Args:
        text: Text to slugify
        
    Returns:
        Slugified text
    """
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 hash as hex string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_string_hash(text: str) -> str:
    """
    Compute SHA256 hash of a string.
    
    Args:
        text: String to hash
        
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def compute_bytes_hash(content: bytes) -> str:
    """
    Compute SHA256 hash of bytes content.
    
    Args:
        content: Bytes to hash
        
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(content).hexdigest()


def url_to_filename(url: str, file_type: str = "html", prefix: str = "") -> str:
    """
    Convert URL to a safe filename based on content type.
    
    Args:
        url: URL to convert
        file_type: Content type (html, md, pdf)
        prefix: Optional prefix for filename
        
    Returns:
        Safe filename
    """
    # Extract domain and path
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    
    # Create base filename
    if path:
        filename = path.split("/")[-1] or parsed.netloc
    else:
        filename = parsed.netloc
    
    # Remove query params and fragments
    filename = filename.split("?")[0].split("#")[0]
    
    extension = Path(filename).suffix.lower()
    target_ext = ".html"
    if file_type.lower() in {"md", "markdown"}:
        target_ext = ".md"
    elif file_type.lower() == "pdf":
        target_ext = ".pdf"
    
    if not extension:
        filename += target_ext
    elif target_ext and extension != target_ext:
        filename = filename[: -len(extension)] + target_ext
    
    # If we still don't have a good name, use a hash of the URL
    if not filename or filename == target_ext:
        filename = compute_string_hash(url)[:16] + target_ext
    
    if prefix:
        filename = f"{prefix}_{filename}"
    
    # Limit filename length
    if len(filename) > 200:
        name, ext = Path(filename).name, Path(filename).suffix
        base = compute_string_hash(name)[:12]
        filename = f"{base}{ext}"
    
    return filename.replace(" ", "_").replace("/", "_")


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The directory path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_domain(url: str) -> Optional[str]:
    """
    Extract root domain from URL (removes www. and subdomains).
    
    Args:
        url: URL
        
    Returns:
        Root domain or None if invalid
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Extract root domain (remove subdomains)
        parts = domain.split(".")
        if len(parts) >= 2:
            # For .com, .org, .net, etc. - take last 2 parts
            if len(parts[-1]) <= 3:  # TLD like com, org, net
                domain = ".".join(parts[-2:])
            else:  # For longer TLDs like co.uk, take last 3 parts
                domain = ".".join(parts[-3:])
        
        return domain
    except Exception as e:
        logger.error(f"Failed to extract domain from {url}: {e}")
        return None


def safe_join_path(*parts: str) -> Path:
    """
    Safely join path parts, preventing directory traversal.
    
    Args:
        *parts: Path parts
        
    Returns:
        Joined path
    """
    result = Path()
    for part in parts:
        part = part.lstrip("/").lstrip(".")
        result = result / part
    return result
