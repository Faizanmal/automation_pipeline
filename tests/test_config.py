"""Tests for configuration module."""

import pytest
from pipeline.config import (
    CompanyConfig,
    PipelineConfig,
    ProviderConfig,
)


class TestCompanyConfig:
    """Test CompanyConfig model."""
    
    def test_company_creation(self):
        """Test basic company creation."""
        company = CompanyConfig(
            name="Test Corp",
            website="https://example.com",
            keywords=["test"],
        )
        assert company.name == "Test Corp"
        assert company.slug == "test-corp"
        assert company.website == "https://example.com"
    
    def test_company_slug_generation(self):
        """Test slug auto-generation."""
        company = CompanyConfig(
            name="Goldman Sachs",
            website="https://gs.com",
        )
        assert company.slug == "goldman-sachs"
    
    def test_company_custom_slug(self):
        """Test custom slug."""
        company = CompanyConfig(
            name="Goldman Sachs",
            slug="gs",
            website="https://gs.com",
        )
        assert company.slug == "gs"
    
    def test_company_seed_normalization(self):
        """Test seed URL normalization."""
        company = CompanyConfig(
            name="Test",
            website="https://example.com",
            seeds=["http://example.com/path", "https://example.com"],
        )
        assert len(company.seeds) == 2
        assert all(isinstance(s, str) for s in company.seeds)


class TestPipelineConfig:
    """Test PipelineConfig model."""
    
    def test_pipeline_default_values(self):
        """Test pipeline config defaults."""
        config = PipelineConfig(
            companies=[
                CompanyConfig(
                    name="Test",
                    website="https://test.com"
                )
            ]
        )
        assert config.max_concurrent_requests == 5
        assert config.request_timeout_seconds == 30
        assert config.max_retries == 3
        assert config.log_level == "INFO"
    
    def test_pipeline_validation(self):
        """Test pipeline validation."""
        with pytest.raises(ValueError):
            config = PipelineConfig(companies=[])
            config.validate_all()
    
    def test_duplicate_slug_detection(self):
        """Test duplicate slug detection."""
        with pytest.raises(ValueError):
            config = PipelineConfig(
                companies=[
                    CompanyConfig(
                        name="Test1",
                        slug="test",
                        website="https://test1.com"
                    ),
                    CompanyConfig(
                        name="Test2",
                        slug="test",
                        website="https://test2.com"
                    ),
                ]
            )
            config.validate_all()


class TestProviderConfig:
    """Test ProviderConfig model."""
    
    def test_provider_creation(self):
        """Test provider creation."""
        provider = ProviderConfig(
            name="brave",
            api_key="test-key",
            enabled=True,
            priority=1,
        )
        assert provider.name == "brave"
        assert provider.enabled is True
        assert provider.priority == 1
