"""Tests for storage module."""

import pytest
import tempfile
from pathlib import Path
from pipeline.storage import StorageManager, FileRecord


class TestStorageManager:
    """Test StorageManager."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield StorageManager(Path(tmpdir))
    
    def test_storage_initialization(self, temp_storage):
        """Test storage initialization."""
        assert temp_storage.base_dir.exists()
        assert temp_storage.base_dir.is_dir()
    
    def test_save_file(self, temp_storage):
        """Test file saving."""
        content = b"test content"
        file_path = temp_storage.save_file(
            content,
            "test-company",
            None,
            "test.txt",
            "txt",
        )
        
        assert file_path.exists()
        assert file_path.read_bytes() == content
    
    def test_manifest_operations(self, temp_storage):
        """Test manifest operations."""
        record = FileRecord(
            url="https://example.com/doc.pdf",
            file_path="test-company/pdf/doc.pdf",
            sha256="abc123",
            timestamp="2024-01-01T00:00:00",
            file_type="pdf",
            size_bytes=1024,
        )
        
        # Save manifest
        temp_storage.save_manifest("test-company", [record])
        
        # Load manifest
        records = temp_storage.load_manifest("test-company")
        
        assert len(records) > 0
        assert records[0].url == record.url


class TestFileRecord:
    """Test FileRecord model."""
    
    def test_file_record_creation(self):
        """Test file record creation."""
        record = FileRecord(
            url="https://example.com/doc.pdf",
            file_path="company/pdf/doc.pdf",
            sha256="abc123def456",
            timestamp="2024-01-01T00:00:00",
            file_type="pdf",
            size_bytes=1024,
        )
        
        assert record.url == "https://example.com/doc.pdf"
        assert record.file_type == "pdf"
        assert record.size_bytes == 1024
