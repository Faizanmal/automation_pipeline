# Data Pipeline: Document Discovery & Download

A production-grade, config-driven Python pipeline for discovering and downloading public documents (PDFs and HTML pages) from financial sector company websites. Designed for scalability, re-runnable without duplication, and comprehensive logging.

## Features

✅ **Config-Driven**: YAML-based configuration for companies and search keywords
✅ **Async/Concurrent**: Multi-threaded downloading with configurable concurrency
✅ **Multi-Provider Discovery**: Brave, Google Custom Search, and Bing API support with automatic fallback
✅ **Multi-Provider Scraping**: Firecrawl and ScrapingBee API support with automatic fallback
✅ **Smart Scraping**: JavaScript-rendered content support
✅ **De-duplication**: SHA256-based duplicate detection and skipping
✅ **File Validation**: Automatic validation of PDFs and HTML files
✅ **Metadata Tracking**: Complete manifest with timestamps, hashes, and sizes
✅ **Coverage Reporting**: JSON-based coverage reports with statistics
✅ **Error Resilience**: Graceful error handling with retry logic
✅ **CLI Interface**: Simple command-line interface for running and reporting

---

## Project Structure

```
automation_pipeline/
├── main.py                      # Entry point with CLI
├── config.yaml                  # Configuration file
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── pipeline.log                 # Pipeline logs (generated)
├── output/                      # Output directory (generated)
│   ├── {company-slug}/
│   │   ├── Q1-2024/
│   │   │   ├── _raw/           # Raw content
│   │   │   ├── html/           # HTML files
│   │   │   ├── pdf/            # PDF files
│   │   │   └── md/             # Markdown files
│   │   └── _meta/
│   │       ├── manifest.json    # File manifest
│   │       └── discovery.json   # Discovery results
│   └── coverage.json            # Coverage report
└── pipeline/
    ├── __init__.py
    ├── config.py                # Configuration management
    ├── discovery.py             # URL discovery (Brave API)
    ├── fetcher.py               # Content fetching (Firecrawl)
    ├── storage.py               # Storage management
    ├── validator.py             # File validation
    ├── reporter.py              # Coverage reporting
    └── utils.py                 # Utility functions
```

---

## Setup

### 1. Install Python 3.10+

```bash
python --version  # Ensure 3.10 or higher
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

The pipeline supports multiple API providers with automatic fallback. Set environment variables for your APIs:

```bash
# Required (at least one discovery and one scraping provider)
export BRAVE_API_KEY=your_brave_key_here
export FIRECRAWL_API_KEY=your_firecrawl_key_here

# Optional additional providers
export GOOGLE_API_KEY=your_google_key_here
export GOOGLE_SEARCH_CX=your_custom_search_engine_id
export BING_API_KEY=your_bing_key_here
export SCRAPINGBEE_API_KEY=your_scrapingbee_key_here
```

#### Supported Providers

**Discovery APIs:**
- **Brave Search** - Fast, privacy-focused search
- **Google Custom Search** - Comprehensive search with custom engines
- **Bing Web Search** - Microsoft's search API

**Scraping APIs:**
- **Firecrawl** - Advanced scraping with JavaScript support
- **ScrapingBee** - Reliable scraping with anti-detection

The pipeline will automatically use the highest priority enabled provider, with fallback to others if one fails.

---

## Configuration

### Basic Example (`config.yaml`)

```yaml
companies:
  - name: UBS
    slug: ubs
    website: https://www.ubs.com
    keywords:
      - annual report
      - financial statements
      - earnings
    seeds:
      - https://www.ubs.com/investors

  - name: Goldman Sachs
    slug: gs
    website: https://www.goldmansachs.com
    keywords:
      - annual report
      - quarterly earnings
    seeds:
      - https://www.goldmansachs.com/investor-relations/

# API Configuration - Multiple Providers (Recommended)
discovery_providers:
  - name: brave
    api_key: ${BRAVE_API_KEY}
    enabled: true
    priority: 1
  - name: google
    api_key: ${GOOGLE_API_KEY}
    enabled: true
    priority: 2
    config:
      cx: ${GOOGLE_SEARCH_CX}
  - name: bing
    api_key: ${BING_API_KEY}
    enabled: false
    priority: 3

scraping_providers:
  - name: firecrawl
    api_key: ${FIRECRAWL_API_KEY}
    enabled: true
    priority: 1
  - name: scrapingbee
    api_key: ${SCRAPINGBEE_API_KEY}
    enabled: false
    priority: 2

# Legacy API Configuration (for backward compatibility)
brave_api_key: ${BRAVE_API_KEY}
firecrawl_api_key: ${FIRECRAWL_API_KEY}

# Pipeline Configuration
output_dir: output
max_concurrent_requests: 5
request_timeout_seconds: 30
max_retries: 3
log_level: INFO
```

### Adding Companies

1. Open `config.yaml`
2. Add a new entry under `companies`:

```yaml
  - name: Morgan Stanley
    slug: ms
    website: https://www.morganstanley.com
    keywords:
      - earnings report
      - financial results
      - investor updates
    seeds:
      - https://www.morganstanley.com/investor-relations/
```

3. Run the pipeline (see below)

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Company name |
| `slug` | string | URL-safe identifier (auto-generated if omitted) |
| `website` | string | Company website URL |
| `keywords` | list | Search keywords for document discovery |
| `seeds` | list | Seed URLs to always include |
| `output_dir` | string | Where to save downloaded files |
| `max_concurrent_requests` | int | Max parallel requests (1-20) |
| `request_timeout_seconds` | int | Request timeout in seconds |
| `max_retries` | int | Retry count for failed requests |
| `log_level` | string | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## Running the Pipeline

### Basic Run

```bash
python main.py run
```

This processes all companies in `config.yaml`.

### Run Specific Company

```bash
python main.py run --company ubs --company gs
```

### With Custom Config

```bash
python main.py run --config my_config.yaml
```

### With Debug Logging

```bash
python main.py run --log-level DEBUG
```

### Generate Example Config

```bash
python main.py example-config
```

Creates `config.example.yaml` with sample companies.

### Generate Coverage Report

```bash
python main.py report
```

Generates `output/coverage.json` and prints summary.

---

## Output Structure

### File Storage

After running the pipeline:

```
output/
├── ubs/
│   ├── Q1-2024/
│   │   ├── html/
│   │   │   ├── investors_annual_report.html
│   │   │   └── financial_statements.html
│   │   ├── pdf/
│   │   │   ├── 2024_annual_report.pdf
│   │   │   └── financial_results.pdf
│   │   └── md/
│   │       ├── quarterly_earnings.md
│   │       └── press_releases.md
│   └── _meta/
│       ├── manifest.json
│       └── discovery.json
└── coverage.json
```

### Manifest Format (`_meta/manifest.json`)

```json
{
  "generated": "2024-04-12T10:30:00.123456",
  "files": [
    {
      "url": "https://www.ubs.com/investors/annual-report",
      "file_path": "ubs/Q1-2024/html/annual_report_2024.html",
      "sha256": "abc123def456...",
      "timestamp": "2024-04-12T10:30:05.123456",
      "file_type": "html",
      "size_bytes": 524288
    }
  ]
}
```

### Discovery Results (`_meta/discovery.json`)

```json
{
  "generated": "2024-04-12T10:30:00.123456",
  "urls": [
    "https://www.ubs.com/investors",
    "https://www.ubs.com/research/reports",
    ...
  ],
  "count": 42
}
```

### Coverage Report (`coverage.json`)

```json
{
  "generated": "2024-04-12T10:45:00.123456",
  "total_companies": 3,
  "successful_companies": 3,
  "failed_companies": 0,
  "success_rate": 1.0,
  "total_files": 347,
  "pdf_count": 156,
  "html_count": 145,
  "markdown_count": 46,
  "total_bytes": 1536000000,
  "average_files_per_company": 115.7,
  "company_stats": {
    "ubs": {
      "files": 120,
      "bytes": 512000000,
      "pdfs": 52,
      "htmls": 48,
      "markdowns": 20
    }
  }
}
```

---

## Re-Runnable Pipeline

The pipeline is designed to be **idempotent** — running it multiple times does not duplicate work:

### How De-duplication Works

1. **Hash Tracking**: Every file is hashed with SHA256
2. **Manifest Checking**: Before saving, the manifest is checked for matching hashes
3. **Automatic Skipping**: Files with identical hashes are logged but not re-downloaded
4. **Change Detection**: If a URL returns changed content, the new file is versioned instead of overwriting the old one
5. **URL Logging**: All discovered URLs are logged for audit trail

### Example

```bash
# First run - downloads files
python main.py run

# Second run - skips duplicates, discovers new URLs
python main.py run
# Output: "File already exists (hash match): ubs/Q1-2024/html/report.html"
```

---

## Logging

Logs are written to `pipeline.log` and console:

```
2024-04-12 10:30:00 - pipeline - INFO - Starting pipeline...
2024-04-12 10:30:01 - pipeline.discovery - INFO - Discovering URLs for UBS...
2024-04-12 10:30:05 - pipeline.discovery - INFO - Discovered 42 URLs for UBS
2024-04-12 10:30:06 - pipeline.fetcher - INFO - Fetching content from 42 URLs...
2024-04-12 10:30:45 - pipeline.storage - DEBUG - Stored file: ubs/Q1-2024/html/report.html
2024-04-12 10:30:46 - pipeline - INFO - Coverage report generated
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General pipeline progress
- **WARNING**: Non-fatal issues (skipped files, missing APIs)
- **ERROR**: Fatal issues requiring attention

---

## Error Handling

### API Failures

- **Rate Limiting (429)**: Automatic exponential backoff retry
- **Timeout**: Retries up to `max_retries` times
- **Invalid Response**: Logged and skipped gracefully

### File Issues

- **Invalid PDFs**: Validation fails if not starting with `%PDF` or <10KB
- **Empty HTML**: Rejected if <100 bytes or missing HTML tags
- **Network Error**: Retried with exponential backoff

### Pipeline Resilience

- One company failure doesn't stop the pipeline
- Failed URLs are logged but don't block other companies
- Coverage report includes error statistics

---

## Performance Tuning

### Concurrency

```yaml
max_concurrent_requests: 10  # Increase for faster downloads
```

**Note**: Respect API rate limits (Brave: 2400/day, Firecrawl: plan-dependent)

### Timeouts

```yaml
request_timeout_seconds: 60  # Increase for slow networks
```

### Retries

```yaml
max_retries: 5  # More retries for unreliable networks
```

---

## API Requirements

### Brave Search API

- Get key: https://api.search.brave.com/
- Rate limit: ~2400 requests/day (free tier)
- Cost: Pay-as-you-go or subscription

### Firecrawl API

- Get key: https://www.firecrawl.dev/
- Features: JavaScript rendering, crawler mode
- Cost: See pricing page

---

## Troubleshooting

### "Config file not found"

```bash
# Ensure config.yaml exists in current directory
ls -la config.yaml
python main.py run --config ./config.yaml
```

### "Brave API key not configured"

```bash
# Set environment variable
export BRAVE_API_KEY=your_key_here
python main.py run
```

### "No URLs discovered"

1. Check keywords in config
2. Verify company website is accessible
3. Run with DEBUG logging: `python main.py run --log-level DEBUG`

### "Files not saving"

1. Check output directory permissions: `ls -la output/`
2. Ensure enough disk space
3. Check for validation errors in logs

### "Rate limit errors"

1. Reduce `max_concurrent_requests`
2. Wait before re-running
3. Check API quota limits

---

## Development

### Project Architecture

```
ConfigModule
    ↓
DiscoveryModule (Brave API) → URLs
    ↓
FetcherModule (Firecrawl) → Content
    ↓
ValidatorModule → Valid?
    ↓
StorageModule → Save + Manifest
    ↓
ReporterModule → Coverage Report
```

### Key Classes

- `PipelineConfig`: Configuration model with validation
- `DiscoveryClient`: Brave Search API wrapper
- `FetchClient`: Firecrawl API wrapper
- `StorageManager`: File and metadata management
- `DataPipeline`: Main orchestrator

### Extending the Pipeline

1. **Add New Content Type**: Update `validator.py` and `storage.py`
2. **Add New Discovery Method**: Extend `discovery.py` with new client
3. **Add New Fetcher**: Subclass `FetchClient` in `fetcher.py`

---

## Testing Locally

Without API keys (mock mode):

```yaml
companies:
  - name: Example
    slug: example
    website: https://example.com
    keywords:
      - test
    seeds:
      - https://example.com
```

Run with DEBUG to see what would happen:

```bash
python main.py run --log-level DEBUG
# Will skip fetching without API keys, uses seed URLs only
```

---

## License

MIT

---

## Support

For issues or questions:
1. Check logs: `tail -f pipeline.log`
2. Run with DEBUG: `python main.py run --log-level DEBUG`
3. Validate config: `python -m yaml config.yaml`

---

## Version History

- **v1.0.0** (2024-04-12): Initial release
  - Brave Search integration
  - Firecrawl integration
  - SHA256 de-duplication
  - Coverage reporting
  - CLI interface
