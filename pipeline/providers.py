"""
Provider management for discovery and scraping APIs.
"""

import logging
from typing import List, Optional

from .config import PipelineConfig, ProviderConfig
from .discovery import BraveDiscoveryClient, GoogleDiscoveryClient, BingDiscoveryClient, DiscoveryClient
from .fetcher import FirecrawlFetchClient, ScrapingBeeFetchClient, FetchClient

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages multiple API providers with fallback support."""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize provider manager.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.discovery_providers = self._load_discovery_providers()
        self.scraping_providers = self._load_scraping_providers()
    
    def _load_discovery_providers(self) -> List[ProviderConfig]:
        """Load and sort discovery providers by priority."""
        providers = [p for p in self.config.discovery_providers if p.enabled]
        return sorted(providers, key=lambda p: p.priority)
    
    def _load_scraping_providers(self) -> List[ProviderConfig]:
        """Load and sort scraping providers by priority."""
        providers = [p for p in self.config.scraping_providers if p.enabled]
        return sorted(providers, key=lambda p: p.priority)
    
    def get_discovery_client(self, provider_name: Optional[str] = None) -> Optional[DiscoveryClient]:
        """
        Get a discovery client, optionally by name.
        
        Args:
            provider_name: Specific provider name, or None for highest priority
            
        Returns:
            Discovery client instance or None if no suitable provider
        """
        if provider_name:
            provider = next((p for p in self.discovery_providers if p.name == provider_name), None)
            if not provider:
                logger.warning(f"Discovery provider '{provider_name}' not found or disabled")
                return None
            providers = [provider]
        else:
            providers = self.discovery_providers
        
        for provider in providers:
            try:
                client = self._create_discovery_client(provider)
                if client:
                    logger.info(f"Using discovery provider: {provider.name}")
                    return client
            except Exception as e:
                logger.warning(f"Failed to create discovery client for {provider.name}: {e}")
                continue
        
        logger.error("No working discovery providers available")
        return None
    
    def get_scraping_client(self, provider_name: Optional[str] = None) -> Optional[FetchClient]:
        """
        Get a scraping client, optionally by name.
        
        Args:
            provider_name: Specific provider name, or None for highest priority
            
        Returns:
            Scraping client instance or None if no suitable provider
        """
        if provider_name:
            provider = next((p for p in self.scraping_providers if p.name == provider_name), None)
            if not provider:
                logger.warning(f"Scraping provider '{provider_name}' not found or disabled")
                return None
            providers = [provider]
        else:
            providers = self.scraping_providers
        
        for provider in providers:
            try:
                client = self._create_scraping_client(provider)
                if client:
                    logger.info(f"Using scraping provider: {provider.name}")
                    return client
            except Exception as e:
                logger.warning(f"Failed to create scraping client for {provider.name}: {e}")
                continue
        
        logger.error("No working scraping providers available")
        return None

    def get_scraping_clients(self) -> list[FetchClient]:
        """
        Get all configured scraping clients, ordered by priority.

        Returns:
            List of scraping clients
        """
        clients = []
        for provider in self.scraping_providers:
            try:
                client = self._create_scraping_client(provider)
                if client:
                    clients.append(client)
            except Exception as e:
                logger.warning(f"Failed to create scraping client for {provider.name}: {e}")
                continue
        return clients
    
    def _create_discovery_client(self, provider: ProviderConfig) -> Optional[DiscoveryClient]:
        """Create a discovery client for the given provider."""
        if not provider.api_key:
            logger.warning(f"No API key for discovery provider {provider.name}")
            return None
        
        if provider.name == "brave":
            return BraveDiscoveryClient(provider.api_key)
        elif provider.name == "google":
            cx = provider.config.get("cx")
            if not cx:
                logger.warning("Google provider requires 'cx' (custom search engine ID) in config")
                return None
            return GoogleDiscoveryClient(provider.api_key, cx)
        elif provider.name == "bing":
            return BingDiscoveryClient(provider.api_key)
        else:
            logger.warning(f"Unknown discovery provider: {provider.name}")
            return None
    
    def _create_scraping_client(self, provider: ProviderConfig) -> Optional[FetchClient]:
        """Create a scraping client for the given provider."""
        if not provider.api_key:
            logger.warning(f"No API key for scraping provider {provider.name}")
            return None
        
        if provider.name == "firecrawl":
            return FirecrawlFetchClient(provider.api_key)
        elif provider.name == "scrapingbee":
            return ScrapingBeeFetchClient(provider.api_key)
        else:
            logger.warning(f"Unknown scraping provider: {provider.name}")
            return None
    
    def get_available_providers(self) -> dict:
        """
        Get information about available providers.
        
        Returns:
            Dict with discovery and scraping provider info
        """
        return {
            "discovery": [
                {"name": p.name, "priority": p.priority, "enabled": p.enabled}
                for p in self.discovery_providers
            ],
            "scraping": [
                {"name": p.name, "priority": p.priority, "enabled": p.enabled}
                for p in self.scraping_providers
            ]
        }