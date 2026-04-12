"""
Storage management for downloaded files and metadata.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import ensure_directory

logger = logging.getLogger(__name__)


@dataclass
class FileRecord:
    """Record of a downloaded file."""
    
    url: str
    file_path: str
    sha256: str
    timestamp: str
    file_type: str  # pdf, html, md
    size_bytes: int
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if data.get("metadata") is None:
            data.pop("metadata", None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileRecord":
        """Create from dictionary."""
        return cls(**data)


class StorageManager:
    """Manages file storage and metadata."""
    
    def __init__(self, base_output_dir: Path):
        """
        Initialize storage manager.
        
        Args:
            base_output_dir: Base output directory
        """
        self.base_dir = Path(base_output_dir)
        ensure_directory(self.base_dir)
    
    def get_company_dir(self, company_slug: str) -> Path:
        """
        Get company directory.
        
        Args:
            company_slug: Company slug
            
        Returns:
            Path to company directory
        """
        company_dir = self.base_dir / company_slug
        ensure_directory(company_dir)
        return company_dir
    
    def get_quarter_dir(
        self,
        company_slug: str,
        quarter: Optional[str] = None
    ) -> Path:
        """
        Get quarter directory within company.
        
        Args:
            company_slug: Company slug
            quarter: Quarter identifier (e.g., "Q1-2024")
            
        Returns:
            Path to quarter directory
        """
        if not quarter:
            now = datetime.now()
            q = (now.month - 1) // 3 + 1
            quarter = f"Q{q}-{now.year}"
        
        quarter_dir = self.get_company_dir(company_slug) / quarter
        ensure_directory(quarter_dir)
        return quarter_dir
    
    def get_content_subdirs(self, quarter_dir: Path) -> Dict[str, Path]:
        """
        Get content subdirectories for a quarter.
        
        Args:
            quarter_dir: Quarter directory
            
        Returns:
            Dictionary of content type to path
        """
        subdirs = {
            "raw": quarter_dir / "_raw",
            "html": quarter_dir / "html",
            "pdf": quarter_dir / "pdf",
            "md": quarter_dir / "md",
        }
        
        for subdir in subdirs.values():
            ensure_directory(subdir)
        
        return subdirs
    
    def get_meta_dir(self, company_slug: str) -> Path:
        """
        Get metadata directory for company.
        
        Args:
            company_slug: Company slug
            
        Returns:
            Path to metadata directory
        """
        meta_dir = self.get_company_dir(company_slug) / "_meta"
        ensure_directory(meta_dir)
        return meta_dir
    
    def save_file(
        self,
        content: bytes,
        company_slug: str,
        quarter: Optional[str],
        filename: str,
        content_type: str,
    ) -> Path:
        """
        Save file to storage.
        
        Args:
            content: File content
            company_slug: Company slug
            quarter: Quarter identifier
            filename: Filename
            content_type: Content type (html, pdf, md)
            
        Returns:
            Path to saved file
        """
        quarter_dir = self.get_quarter_dir(company_slug, quarter)
        subdirs = self.get_content_subdirs(quarter_dir)
        
        # Map content type to subdir
        type_map = {
            "html": "html",
            "pdf": "pdf",
            "md": "md",
            "markdown": "md",
        }
        
        subdir_key = type_map.get(content_type.lower(), "raw")
        target_dir = subdirs[subdir_key]
        
        file_path = target_dir / filename
        file_path = self._make_unique_path(file_path)
        
        # Write file
        if isinstance(content, str):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(file_path, "wb") as f:
                f.write(content)
        
        logger.debug(f"Saved file: {file_path}")
        return file_path

    def _make_unique_path(self, file_path: Path) -> Path:
        """
        Ensure a unique file path by appending a counter if the path already exists.

        Args:
            file_path: Desired file path

        Returns:
            Unique file path
        """
        if not file_path.exists():
            return file_path

        base = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent
        counter = 1
        while True:
            candidate = parent / f"{base}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
    
    def check_file_exists(
        self,
        company_slug: str,
        quarter: Optional[str],
        filename: str,
        content_type: str,
    ) -> Optional[Path]:
        """
        Check if file already exists.
        
        Args:
            company_slug: Company slug
            quarter: Quarter identifier
            filename: Filename
            content_type: Content type
            
        Returns:
            Path if exists, None otherwise
        """
        queue_dir = self.get_quarter_dir(company_slug, quarter)
        subdirs = self.get_content_subdirs(queue_dir)
        
        type_map = {
            "html": "html",
            "pdf": "pdf",
            "md": "md",
            "markdown": "md",
        }
        
        subdir_key = type_map.get(content_type.lower(), "raw")
        target_dir = subdirs[subdir_key]
        file_path = target_dir / filename
        
        return file_path if file_path.exists() else None
    
    def load_manifest(self, company_slug: str) -> List[FileRecord]:
        """
        Load file manifest for company.
        
        Args:
            company_slug: Company slug
            
        Returns:
            List of file records
        """
        meta_dir = self.get_meta_dir(company_slug)
        manifest_path = meta_dir / "manifest.json"
        
        if not manifest_path.exists():
            return []
        
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, dict):
                records = data.get("files", [])
            else:
                records = data
            
            return [FileRecord.from_dict(record) for record in records]
        
        except Exception as e:
            logger.warning(f"Failed to load manifest for {company_slug}: {e}")
            return []
    
    def save_manifest(self, company_slug: str, records: List[FileRecord]) -> None:
        """
        Save file manifest for company.
        
        Args:
            company_slug: Company slug
            records: List of file records
        """
        meta_dir = self.get_meta_dir(company_slug)
        manifest_path = meta_dir / "manifest.json"
        
        data = {
            "generated": datetime.utcnow().isoformat(),
            "files": [record.to_dict() for record in records],
        }
        
        with open(manifest_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved manifest for {company_slug}: {len(records)} files")
    
    def find_duplicate_file(
        self,
        company_slug: str,
        file_hash: str,
    ) -> Optional[FileRecord]:
        """
        Find if file with same hash already exists.
        
        Args:
            company_slug: Company slug
            file_hash: SHA256 hash
            
        Returns:
            FileRecord if found, None otherwise
        """
        records = self.load_manifest(company_slug)
        
        for record in records:
            if record.sha256 == file_hash:
                return record
        
        return None
    
    def save_discovery_results(
        self,
        company_slug: str,
        urls: List[str],
    ) -> None:
        """
        Save discovery results.
        
        Args:
            company_slug: Company slug
            urls: List of discovered URLs
        """
        meta_dir = self.get_meta_dir(company_slug)
        discovery_path = meta_dir / "discovery.json"
        
        data = {
            "generated": datetime.utcnow().isoformat(),
            "urls": urls,
            "count": len(urls),
        }
        
        with open(discovery_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved discovery results for {company_slug}: {len(urls)} URLs")
    
    def load_discovery_results(self, company_slug: str) -> List[str]:
        """
        Load discovery results.
        
        Args:
            company_slug: Company slug
            
        Returns:
            List of discovered URLs
        """
        meta_dir = self.get_meta_dir(company_slug)
        discovery_path = meta_dir / "discovery.json"
        
        if not discovery_path.exists():
            return []
        
        try:
            with open(discovery_path, "r") as f:
                data = json.load(f)
            return data.get("urls", [])
        except Exception as e:
            logger.warning(f"Failed to load discovery results for {company_slug}: {e}")
            return []
