"""
Main entry point for the data pipeline.
"""

import asyncio
import httpx
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import click

from pipeline import (
    PipelineConfig,
    load_config,
    setup_logging,
     ProviderManager,
    StorageManager,
    generate_report,
    save_report,
    compute_bytes_hash,
    url_to_filename,
    validate_file,
)

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.storage = StorageManager(Path(config.output_dir))
        self.provider_manager = ProviderManager(config)
        self.stats = {
            "companies_processed": 0,
            "urls_discovered": 0,
            "files_fetched": 0,
            "files_saved": 0,
            "duplicates_skipped": 0,
            "validation_failures": 0,
        }
    
    async def process_company(self, company):
        """
        Process a single company.
        
        Args:
            company: CompanyConfig object
        """
        logger.info(f"Processing company: {company.name}")
        
        try:
            # Step 1: Discover URLs
            discovered_urls = await self._discover_urls(company)
            self.stats["urls_discovered"] += len(discovered_urls)
            
            if not discovered_urls:
                logger.warning(f"No URLs discovered for {company.name}")
                return
            
            # Save discovery results
            self.storage.save_discovery_results(company.slug, discovered_urls)
            
            # Step 2: Fetch content
            await self._fetch_content(company, discovered_urls)
            
            logger.info(f"Completed processing: {company.name}")
        
        except Exception as e:
            logger.error(f"Failed to process {company.name}: {e}", exc_info=True)
    
    async def _discover_urls(self, company) -> List[str]:
        """
        Discover URLs for company.
        
        Args:
            company: CompanyConfig
            
        Returns:
            List of URLs
        """
        try:
            logger.info(f"Discovering URLs for {company.name}...")
            
            client = self.provider_manager.get_discovery_client()
            if not client:
                logger.warning("No discovery providers available, using seed URLs only")
                return company.seeds or []
            
            async with client:
                urls = await client.discover(
                    company.website,
                    company.keywords,
                    company.seeds,
                )
            
            logger.info(f"Discovered {len(urls)} URLs for {company.name}")
            return urls
        
        except Exception as e:
            logger.error(f"Discovery failed for {company.name}: {e}")
            return company.seeds or []
    
    async def _fetch_content(self, company, urls: List[str]):
        """
        Fetch content from URLs.
        
        Args:
            company: CompanyConfig
            urls: List of URLs
        """
        clients = self.provider_manager.get_scraping_clients()
        if not clients:
            logger.warning("No scraping providers available, skipping fetch")
            return

        logger.info(f"Fetching content from {len(urls)} URLs...")
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        async def fetch_url(url: str):
            async with semaphore:
                await self._fetch_and_store(company, url, clients)

        tasks = [fetch_url(url) for url in urls]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch_and_store(self, company, url: str, clients):
        """
        Fetch and store content from a URL.
        
        Args:
            company: CompanyConfig
            url: URL to fetch
            clients: List of FetchClient instances to try
        """
        try:
            is_pdf = url.lower().endswith(".pdf")
            html = pdf = md = None

            for client in clients:
                try:
                    async with client:
                        if is_pdf:
                            pdf = await client.fetch_pdf(url)
                            if pdf:
                                break
                        else:
                            html, pdf, md = await client.fetch_page(url)
                            if html or pdf or md:
                                break
                except Exception as exc:
                    logger.warning(f"Provider failed for {url}: {exc}")
                    continue

            if not (html or pdf or md):
                logger.info(f"Trying direct HTTP fallback for {url}")
                html, pdf, md = await self._http_fetch(url)

            if html:
                await self._store_file(company, url, html, "html")
            if pdf:
                await self._store_file(company, url, pdf, "pdf")
            if md:
                await self._store_file(company, url, md.encode("utf-8"), "md")

            if html or pdf or md:
                self.stats["files_fetched"] += 1

        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")

    async def _http_fetch(self, url: str) -> Tuple[Optional[bytes], Optional[bytes], Optional[str]]:
        """Fetch a URL directly with HTTP as a fallback."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            }
            async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.content, None, None
        except Exception as e:
            logger.warning(f"HTTP fallback failed for {url}: {e}")
            return None, None, None
    
    async def _store_file(self, company, url: str, content: bytes, file_type: str):
        """
        Store a file after validation.
        
        Args:
            company: CompanyConfig
            url: Source URL
            content: File content
            file_type: Type of file (html, pdf, md)
        """
        try:
            # Compute hash
            file_hash = compute_bytes_hash(content)
            
            # Check for duplicates
            duplicate = self.storage.find_duplicate_file(company.slug, file_hash)
            if duplicate:
                logger.debug(f"File already exists (hash match): {duplicate.file_path}")
                self.stats["duplicates_skipped"] += 1
                return
            
            # Generate filename
            filename = url_to_filename(url, file_type)
            
            # Save file
            file_path = self.storage.save_file(
                content,
                company.slug,
                None,
                filename,
                file_type,
            )
            
            # Validate file
            if not validate_file(file_path, file_type):
                logger.error(f"File validation failed: {file_path}")
                file_path.unlink(missing_ok=True)
                self.stats["validation_failures"] += 1
                return
            
            # Record in manifest
            from pipeline import FileRecord
            
            record = FileRecord(
                url=url,
                file_path=str(file_path.relative_to(self.storage.base_dir)),
                sha256=file_hash,
                timestamp=datetime.utcnow().isoformat(),
                file_type=file_type,
                size_bytes=len(content),
            )
            
            records = self.storage.load_manifest(company.slug)
            records.append(record)
            self.storage.save_manifest(company.slug, records)
            
            self.stats["files_saved"] += 1
            logger.debug(f"Stored file: {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to store file for {url}: {e}")
    
    async def run(self, company_slugs: Optional[List[str]] = None):
        """
        Run the pipeline.
        
        Args:
            company_slugs: Optional specific companies to process
        """
        logger.info("Starting pipeline...")
        logger.info(f"Output directory: {self.storage.base_dir}")
        
        # Filter companies if needed
        companies = self.config.companies
        if company_slugs:
            companies = [c for c in companies if c.slug in company_slugs]
        
        logger.info(f"Processing {len(companies)} companies")
        
        # Process each company
        for company in companies:
            await self.process_company(company)
            self.stats["companies_processed"] += 1
        
        # Generate report
        logger.info("Generating coverage report...")
        report = generate_report(
            Path(self.config.output_dir),
            [c.slug for c in companies],
        )
        
        report_path = Path(self.config.output_dir) / "coverage.json"
        save_report(report, report_path)
        
        logger.info("Pipeline complete!")
        self._print_stats()
    
    def _print_stats(self):
        """Print pipeline statistics."""
        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 60)
        for key, value in self.stats.items():
            print(f"{key}: {value}")
        print("=" * 60 + "\n")


@click.group()
def cli():
    """Data pipeline for discovering and downloading documents."""
    pass


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Configuration file path",
)
@click.option(
    "--company",
    multiple=True,
    help="Specific company slug(s) to process",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
def run(config: str, company: tuple, log_level: str):
    """Run the data pipeline."""
    try:
        # Setup logging
        setup_logging(log_level)
        
        # Load config
        config_obj = load_config(Path(config))
        
        # Create and run pipeline
        pipeline = DataPipeline(config_obj)
        
        # Run
        asyncio.run(pipeline.run(list(company) if company else None))
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    type=click.Path(),
    default="config.example.yaml",
    help="Output path for example config",
)
def example_config(output: str):
    """Generate example configuration."""
    example_config_data = """
# Data Pipeline Configuration

companies:
  - name: UBS
    slug: ubs
    website: https://www.ubs.com
    keywords:
      - annual report
      - financial statements
      - earnings
      - investor relations
    seeds:
      - https://www.ubs.com/investors
      - https://www.ubs.com/en/wm/uob/news-and-insights.html

  - name: Goldman Sachs
    slug: gs
    website: https://www.goldmansachs.com
    keywords:
      - annual report
      - quarterly earnings
      - investor updates
    seeds:
      - https://www.goldmansachs.com/investor-relations/

  - name: JP Morgan
    slug: jpm
    website: https://www.jpmorganchase.com
    keywords:
      - annual report
      - financial results
      - investor information
    seeds:
      - https://investor.jpmorganchase.com/

# API Configuration
brave_api_key: ${BRAVE_API_KEY}  # Set via environment variable
firecrawl_api_key: ${FIRECRAWL_API_KEY}  # Set via environment variable

# Pipeline Configuration
output_dir: output
max_concurrent_requests: 5
request_timeout_seconds: 30
max_retries: 3
log_level: INFO
"""
    
    output_path = Path(output)
    output_path.write_text(example_config_data.strip())
    
    click.echo(f"Example configuration saved to {output}")


@cli.command()
@click.option(
    "--output",
    type=click.Path(),
    default="output",
    help="Output directory",
)
def report(output: str):
    """Generate coverage report."""
    try:
        from pipeline import generate_report, print_report
        
        setup_logging("INFO")
        
        output_path = Path(output)
        if not output_path.exists():
            click.echo(f"Output directory not found: {output}")
            sys.exit(1)
        
        # Get company slugs from directories
        company_slugs = [
            d.name for d in output_path.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]
        
        if not company_slugs:
            click.echo("No companies found in output directory")
            sys.exit(1)
        
        # Generate report
        cov_report = generate_report(output_path, company_slugs)
        print_report(cov_report)
        
        # Save report
        report_path = output_path / "coverage.json"
        from pipeline import save_report
        save_report(cov_report, report_path)
    
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
