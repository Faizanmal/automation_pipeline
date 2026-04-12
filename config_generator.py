#!/usr/bin/env python3
"""
Utility script to generate pipeline configuration from CSV.

Usage:
    python config_generator.py --input companies.csv --output config.yaml
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any

import yaml


def parse_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Parse CSV file with company data.
    
    Expected columns:
    - name: Company name
    - slug: URL-safe slug (optional, will be generated if missing)
    - website: Company website URL
    - keywords: Keywords separated by semicolon
    - seeds: Seed URLs separated by semicolon (optional)
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of company dictionaries
    """
    companies = []
    
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Skip empty rows
            if not row.get("name"):
                continue
            
            company = {
                "name": row.get("name", "").strip(),
                "website": row.get("website", "").strip(),
                "keywords": [k.strip() for k in row.get("keywords", "").split(";") if k.strip()],
            }
            
            # Optional fields
            if row.get("slug"):
                company["slug"] = row.get("slug").strip()
            
            if row.get("seeds"):
                company["seeds"] = [s.strip() for s in row.get("seeds", "").split(";") if s.strip()]
            
            companies.append(company)
    
    return companies


def generate_config(companies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate pipeline configuration.
    
    Args:
        companies: List of company dictionaries
        
    Returns:
        Configuration dictionary
    """
    return {
        "companies": companies,
        "brave_api_key": "${BRAVE_API_KEY}",
        "firecrawl_api_key": "${FIRECRAWL_API_KEY}",
        "output_dir": "output",
        "max_concurrent_requests": 5,
        "request_timeout_seconds": 30,
        "max_retries": 3,
        "log_level": "INFO",
    }


def save_config(config: Dict[str, Any], output_path: Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Configuration saved to {output_path}")
    print(f"✓ {len(config['companies'])} companies configured")


def create_example_csv(output_path: Path) -> None:
    """
    Create example CSV file.
    
    Args:
        output_path: Path to output CSV
    """
    example_data = """name,slug,website,keywords,seeds
UBS,ubs,https://www.ubs.com,"annual report;financial statements;earnings","https://www.ubs.com/investors"
Goldman Sachs,gs,https://www.goldmansachs.com,"annual report;quarterly earnings","https://www.goldmansachs.com/investor-relations"
JP Morgan,jpm,https://www.jpmorganchase.com,"annual report;financial results","https://investor.jpmorganchase.com"
Morgan Stanley,ms,https://www.morganstanley.com,"earnings report;financial results","https://www.morganstanley.com/investor-relations"
Bank of America,bac,https://www.bankofamerica.com,"annual report;quarterly earnings","https://investor.bankofamerica.com"
Citigroup,c,https://www.citigroup.com,"earnings release;financial results","https://www.citigroup.com/en/investor-relations"
"""
    
    output_path.write_text(example_data)
    print(f"✓ Example CSV created: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate pipeline configuration from CSV"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input CSV file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="config.yaml",
        help="Output YAML config file (default: config.yaml)"
    )
    parser.add_argument(
        "--example",
        type=Path,
        help="Create example CSV at this path"
    )
    
    args = parser.parse_args()
    
    # Create example if requested
    if args.example:
        create_example_csv(args.example)
        return
    
    # Parse input CSV
    if not args.input.exists():
        print(f"✗ Input file not found: {args.input}")
        return
    
    try:
        companies = parse_csv(args.input)
        
        if not companies:
            print("✗ No companies found in CSV")
            return
        
        # Generate and save config
        config = generate_config(companies)
        save_config(config, args.output)
        
        # Print summary
        print()
        print("=" * 60)
        print("FIRST 5 COMPANIES:")
        print("=" * 60)
        for company in companies[:5]:
            print(f"  • {company['name']} ({company.get('slug', 'auto')})")
            print(f"    {company['website']}")
            print(f"    Keywords: {', '.join(company['keywords'][:2])}...")
        
        if len(companies) > 5:
            print(f"  ... and {len(companies) - 5} more")
        
        print("=" * 60)
    
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
