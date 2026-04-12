"""
Configuration loading and validation for the pipeline.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator

from .utils import generate_slug, normalize_url

logger = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    """API provider configuration."""
    
    name: str = Field(..., description="Provider name")
    api_key: Optional[str] = Field(None, description="API key")
    enabled: bool = Field(True, description="Whether provider is enabled")
    priority: int = Field(1, description="Provider priority (lower = higher priority)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional provider config")


class CompanyConfig(BaseModel):
    """Company configuration model."""
    
    name: str = Field(..., description="Company name")
    slug: Optional[str] = Field(None, description="URL-safe slug")
    website: str = Field(..., description="Company website URL")
    keywords: List[str] = Field(default_factory=list, description="Search keywords")
    seeds: List[str] = Field(default_factory=list, description="Seed URLs for discovery")
    
    @validator("website")
    def validate_website(cls, v: str) -> str:
        """Normalize website URL."""
        return normalize_url(v)
    
    @validator("slug", pre=True, always=True)
    def generate_slug_if_missing(cls, v: str, values: Dict[str, Any]) -> str:
        """Generate slug if not provided."""
        if not v and "name" in values:
            v = generate_slug(values["name"])
        return v
    
    @validator("seeds", pre=True)
    def normalize_seeds(cls, v: List[str]) -> List[str]:
        """Normalize seed URLs."""
        return [normalize_url(url) for url in v]
    
    def validate(self) -> None:
        """Validate company configuration."""
        if not self.name:
            raise ValueError("Company name is required")
        if not self.website:
            raise ValueError("Company website is required")
        if not self.slug:
            raise ValueError("Company slug is required")
        if not self.keywords:
            logger.warning(f"Company {self.name} has no keywords defined")


class PipelineConfig(BaseModel):
    """Main pipeline configuration model."""
    
    companies: List[CompanyConfig] = Field(
        default_factory=list,
        description="List of companies to process"
    )
    
    # API Configuration - Multiple providers
    discovery_providers: List[ProviderConfig] = Field(
        default_factory=list,
        description="Discovery API providers"
    )
    scraping_providers: List[ProviderConfig] = Field(
        default_factory=list,
        description="Scraping API providers"
    )
    
    # Legacy API keys for backward compatibility
    brave_api_key: Optional[str] = Field(
        None,
        description="Brave Search API key (legacy)"
    )
    firecrawl_api_key: Optional[str] = Field(
        None,
        description="Firecrawl API key (legacy)"
    )
    
    # Pipeline Configuration
    output_dir: str = Field(
        "output",
        description="Output directory"
    )
    max_concurrent_requests: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum concurrent requests"
    )
    request_timeout_seconds: int = Field(
        30,
        ge=10,
        le=120,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum retries for failed requests"
    )
    
    # Logging
    log_level: str = Field(
        "INFO",
        description="Logging level"
    )
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
    
    def validate_all(self) -> None:
        """Validate complete configuration."""
        if not self.companies:
            raise ValueError("No companies configured")
        
        for company in self.companies:
            company.validate()
        
        # Deduplicate company slugs
        slugs = [c.slug for c in self.companies]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Duplicate company slugs found")
        
        logger.info(f"Configuration validated: {len(self.companies)} companies")


_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _expand_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_VAR_PATTERN.sub(lambda match: os.environ.get(match.group(1), ""), value)
    if isinstance(value, dict):
        return {key: _expand_env_vars(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(item) for item in value]
    return value


def load_config(config_path: Union[str, Path]) -> PipelineConfig:
    """
    Load and validate pipeline configuration from YAML.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Validated PipelineConfig
        
    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        
        config_data = _expand_env_vars(config_data)
        
        if not config_data:
            raise ValueError("Config file is empty")
        
        # Parse companies
        companies_data = config_data.get("companies", [])
        companies = [CompanyConfig(**cn) for cn in companies_data]
        
        # Handle provider configuration
        discovery_providers = []
        scraping_providers = []
        
        # New provider format
        if "discovery_providers" in config_data:
            discovery_providers = [ProviderConfig(**p) for p in config_data["discovery_providers"]]
        if "scraping_providers" in config_data:
            scraping_providers = [ProviderConfig(**p) for p in config_data["scraping_providers"]]
        
        # Backward compatibility - convert legacy keys to providers
        if not discovery_providers and config_data.get("brave_api_key"):
            discovery_providers.append(ProviderConfig(
                name="brave",
                api_key=config_data["brave_api_key"],
                enabled=True,
                priority=1
            ))
        
        if not scraping_providers and config_data.get("firecrawl_api_key"):
            scraping_providers.append(ProviderConfig(
                name="firecrawl",
                api_key=config_data["firecrawl_api_key"],
                enabled=True,
                priority=1
            ))
        
        # Create config
        config_dict = {
            "companies": companies,
            "discovery_providers": discovery_providers,
            "scraping_providers": scraping_providers,
            "brave_api_key": config_data.get("brave_api_key"),
            "firecrawl_api_key": config_data.get("firecrawl_api_key"),
            "output_dir": config_data.get("output_dir", "output"),
            "max_concurrent_requests": config_data.get("max_concurrent_requests", 5),
            "request_timeout_seconds": config_data.get("request_timeout_seconds", 30),
            "max_retries": config_data.get("max_retries", 3),
            "log_level": config_data.get("log_level", "INFO"),
        }
        
        config = PipelineConfig(**config_dict)
        config.validate_all()
        
        return config
    
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


def save_config(config: PipelineConfig, output_path: Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration to save
        output_path: Output path
    """
    config_dict = {
        "companies": [
            {
                "name": c.name,
                "slug": c.slug,
                "website": c.website,
                "keywords": c.keywords,
                "seeds": c.seeds,
            }
            for c in config.companies
        ],
        "brave_api_key": config.brave_api_key,
        "firecrawl_api_key": config.firecrawl_api_key,
        "output_dir": config.output_dir,
        "max_concurrent_requests": config.max_concurrent_requests,
        "request_timeout_seconds": config.request_timeout_seconds,
        "max_retries": config.max_retries,
        "log_level": config.log_level,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Configuration saved to {output_path}")
