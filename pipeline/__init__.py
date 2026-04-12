"""
Data pipeline for discovering and downloading company documents.
"""

from .config import CompanyConfig, PipelineConfig, ProviderConfig, load_config, save_config
from .discovery import DiscoveryClient, BraveDiscoveryClient, GoogleDiscoveryClient, BingDiscoveryClient, discover_urls
from .fetcher import FetchClient, FirecrawlFetchClient, ScrapingBeeFetchClient, FetchError, fetch_bulk, fetch_content
from .providers import ProviderManager
from .reporter import CoverageReport, generate_report, print_report, save_report
from .storage import FileRecord, StorageManager
from .utils import (
    compute_file_hash,
    compute_string_hash,
    compute_bytes_hash,
    ensure_directory,
    extract_domain,
    generate_slug,
    normalize_url,
    setup_logging,
    url_to_filename,
)
from .validator import validate_file, validate_html, validate_pdf, validate_url

__all__ = [
    # Config
    "CompanyConfig",
    "PipelineConfig",
    "ProviderConfig",
    "load_config",
    "save_config",
    # Discovery
    "DiscoveryClient",
    "BraveDiscoveryClient",
    "GoogleDiscoveryClient", 
    "BingDiscoveryClient",
    "discover_urls",
    # Fetcher
    "FetchClient",
    "FirecrawlFetchClient",
    "ScrapingBeeFetchClient",
    "FetchError",
    "fetch_bulk",
    "fetch_content",
    # Providers
    "ProviderManager",
    # Storage
    "FileRecord",
    "StorageManager",
    # Reporter
    "CoverageReport",
    "generate_report",
    "print_report",
    "save_report",
    # Utils
    "compute_file_hash",
    "compute_string_hash",
    "compute_bytes_hash",
    "ensure_directory",
    "extract_domain",
    "generate_slug",
    "normalize_url",
    "setup_logging",
    "url_to_filename",
    # Validator
    "validate_file",
    "validate_html",
    "validate_pdf",
    "validate_url",
]

__version__ = "1.0.0"
