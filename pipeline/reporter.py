"""
Coverage reporting for the pipeline.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .storage import StorageManager

logger = logging.getLogger(__name__)


class CoverageReport:
    """Coverage report for the pipeline."""
    
    def __init__(self):
        """Initialize coverage report."""
        self.total_companies: int = 0
        self.successful_companies: int = 0
        self.failed_companies: int = 0
        self.total_files: int = 0
        self.pdf_count: int = 0
        self.html_count: int = 0
        self.md_count: int = 0
        self.total_bytes: int = 0
        self.company_stats: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated": datetime.utcnow().isoformat(),
            "total_companies": self.total_companies,
            "successful_companies": self.successful_companies,
            "failed_companies": self.failed_companies,
            "success_rate": (
                self.successful_companies / self.total_companies
                if self.total_companies > 0
                else 0
            ),
            "total_files": self.total_files,
            "pdf_count": self.pdf_count,
            "html_count": self.html_count,
            "markdown_count": self.md_count,
            "total_bytes": self.total_bytes,
            "average_files_per_company": (
                self.total_files / self.successful_companies
                if self.successful_companies > 0
                else 0
            ),
            "company_stats": self.company_stats,
            "errors": self.errors[:100],  # Limit errors
        }


def generate_report(
    base_output_dir: Path,
    company_slugs: List[str],
) -> CoverageReport:
    """
    Generate coverage report.
    
    Args:
        base_output_dir: Base output directory
        company_slugs: List of company slugs
        
    Returns:
        CoverageReport object
    """
    report = CoverageReport()
    report.total_companies = len(company_slugs)
    
    storage = StorageManager(base_output_dir)
    
    for company_slug in company_slugs:
        try:
            records = storage.load_manifest(company_slug)
            
            if not records:
                logger.warning(f"No files found for {company_slug}")
                report.company_stats[company_slug] = {
                    "files": 0,
                    "bytes": 0,
                    "pdfs": 0,
                    "htmls": 0,
                    "markdowns": 0,
                }
                report.failed_companies += 1
                continue
            
            report.successful_companies += 1
            
            company_stats = {
                "files": len(records),
                "bytes": 0,
                "pdfs": 0,
                "htmls": 0,
                "markdowns": 0,
                "types": defaultdict(int),
            }
            
            for record in records:
                report.total_files += 1
                company_stats["bytes"] += record.size_bytes
                report.total_bytes += record.size_bytes
                
                file_type = record.file_type.lower()
                if file_type == "pdf":
                    report.pdf_count += 1
                    company_stats["pdfs"] += 1
                elif file_type in ("html", "htm"):
                    report.html_count += 1
                    company_stats["htmls"] += 1
                elif file_type in ("md", "markdown"):
                    report.md_count += 1
                    company_stats["markdowns"] += 1
                
                company_stats["types"][file_type] += 1
            
            # Clean up temporary dict
            company_stats.pop("types", None)
            report.company_stats[company_slug] = company_stats
        
        except Exception as e:
            logger.error(f"Failed to generate report for {company_slug}: {e}")
            report.failed_companies += 1
            report.errors.append(f"Error processing {company_slug}: {str(e)}")
    
    return report


def save_report(report: CoverageReport, output_path: Path) -> None:
    """
    Save coverage report to file.
    
    Args:
        report: CoverageReport object
        output_path: Output path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logger.info(f"Coverage report saved to {output_path}")
    print_report(report)


def print_report(report: CoverageReport) -> None:
    """
    Print coverage report to console.
    
    Args:
        report: CoverageReport object
    """
    print("\n" + "=" * 60)
    print("COVERAGE REPORT")
    print("=" * 60)
    print(f"Companies processed: {report.total_companies}")
    print(f"Successful: {report.successful_companies}")
    print(f"Failed: {report.failed_companies}")
    print(f"Success rate: {report.successful_companies / report.total_companies * 100:.1f}%" if report.total_companies > 0 else "N/A")
    print()
    print(f"Total files: {report.total_files}")
    print(f"  PDFs: {report.pdf_count}")
    print(f"  HTML: {report.html_count}")
    print(f"  Markdown: {report.md_count}")
    print(f"Total bytes: {report.total_bytes / 1024 / 1024:.2f} MB")
    
    if report.successful_companies > 0:
        print(f"Average files per company: {report.total_files / report.successful_companies:.1f}")
    
    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for error in report.errors[:5]:
            print(f"  - {error}")
    
    print("=" * 60 + "\n")


def merge_reports(*reports: CoverageReport) -> CoverageReport:
    """
    Merge multiple coverage reports.
    
    Args:
        *reports: CoverageReport objects
        
    Returns:
        Merged CoverageReport
    """
    merged = CoverageReport()
    
    for report in reports:
        merged.total_companies += report.total_companies
        merged.successful_companies += report.successful_companies
        merged.failed_companies += report.failed_companies
        merged.total_files += report.total_files
        merged.pdf_count += report.pdf_count
        merged.html_count += report.html_count
        merged.md_count += report.md_count
        merged.total_bytes += report.total_bytes
        merged.errors.extend(report.errors)
        merged.company_stats.update(report.company_stats)
    
    return merged
