"""Tests for utility functions."""

from pipeline.utils import (
    compute_file_hash,
    compute_string_hash,
    compute_bytes_hash,
    generate_slug,
    normalize_url,
    extract_domain,
    url_to_filename,
)


class TestHashFunctions:
    """Test hashing utilities."""
    
    def test_compute_bytes_hash(self):
        """Test bytes hash computation."""
        content = b"test content"
        hash_value = compute_bytes_hash(content)
        
        # SHA256 produces 64 character hex string
        assert len(hash_value) == 64
        assert isinstance(hash_value, str)
    
    def test_compute_string_hash(self):
        """Test string hash computation."""
        text = "test string"
        hash_value = compute_string_hash(text)
        
        assert len(hash_value) == 64
        assert isinstance(hash_value, str)
    
    def test_hash_consistency(self):
        """Test hash consistency."""
        content = b"same content"
        hash1 = compute_bytes_hash(content)
        hash2 = compute_bytes_hash(content)
        
        assert hash1 == hash2
    
    def test_compute_file_hash(self, tmp_path):
        """Test file hash computation."""
        # Create a temporary file
        test_file = tmp_path / "test.txt"
        content = b"test file content"
        test_file.write_bytes(content)
        
        hash_value = compute_file_hash(test_file)
        
        # SHA256 produces 64 character hex string
        assert len(hash_value) == 64
        assert isinstance(hash_value, str)
        
        # Hash should match direct bytes hash
        expected_hash = compute_bytes_hash(content)
        assert hash_value == expected_hash


class TestStringUtils:
    """Test string manipulation utilities."""
    
    def test_generate_slug(self):
        """Test slug generation."""
        assert generate_slug("Goldman Sachs") == "goldman-sachs"
        assert generate_slug("JP Morgan") == "jp-morgan"
        assert generate_slug("Test-Company") == "test-company"
    
    def test_normalize_url(self):
        """Test URL normalization."""
        url = "http://example.com"
        normalized = normalize_url(url)
        
        assert normalized.startswith("http")
        assert "example.com" in normalized
    
    def test_extract_domain(self):
        """Test domain extraction."""
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("https://subdomain.example.com") == "example.com"
    
    def test_url_to_filename(self):
        """Test URL to filename conversion."""
        url = "https://example.com/document.pdf"
        filename = url_to_filename(url, "pdf")
        
        assert filename.endswith(".pdf")
        assert isinstance(filename, str)
