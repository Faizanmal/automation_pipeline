#!/usr/bin/env python3
"""
Validation script for the data pipeline project.
Checks dependencies, configuration, and directory structure.
"""

import sys
from pathlib import Path
from typing import List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
    return False, f"✗ Python 3.10+ required (found {version.major}.{version.minor})"


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required packages are installed."""
    required = [
        "httpx",
        "yaml",
        "pydantic",
        "tenacity",
        "click",
    ]
    
    messages = []
    missing = []
    
    for package in required:
        try:
            __import__(package)
            messages.append(f"✓ {package}")
        except ImportError:
            messages.append(f"✗ {package} (missing)")
            missing.append(package)
    
    return len(missing) == 0, messages


def check_project_structure() -> Tuple[bool, List[str]]:
    """Check if project structure is correct."""
    base = Path(".")
    
    required_files = [
        "main.py",
        "config.yaml",
        "requirements.txt",
        "README.md",
        "pipeline/__init__.py",
        "pipeline/config.py",
        "pipeline/discovery.py",
        "pipeline/fetcher.py",
        "pipeline/storage.py",
        "pipeline/validator.py",
        "pipeline/reporter.py",
        "pipeline/utils.py",
    ]
    
    messages = []
    for file in required_files:
        path = base / file
        if path.exists():
            size_kb = path.stat().st_size / 1024
            messages.append(f"✓ {file} ({size_kb:.1f} KB)")
        else:
            messages.append(f"✗ {file} (missing)")
    
    all_exist = all((base / f).exists() for f in required_files)
    return all_exist, messages


def check_config() -> Tuple[bool, List[str]]:
    """Check configuration file."""
    messages = []
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        return False, ["✗ config.yaml not found"]
    
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        messages.append("✓ config.yaml is valid YAML")
        
        if "companies" in config:
            count = len(config.get("companies", []))
            messages.append(f"✓ {count} companies configured")
        else:
            messages.append("⚠ No companies configured")
        
        return True, messages
    except Exception as e:
        return False, [f"✗ config.yaml error: {e}"]


def check_environment_vars() -> Tuple[bool, List[str]]:
    """Check environment variables."""
    import os
    
    messages = []
    
    brave_key = os.getenv("BRAVE_API_KEY")
    if brave_key:
        masked = brave_key[:5] + "*" * (len(brave_key) - 10) + brave_key[-5:]
        messages.append(f"✓ BRAVE_API_KEY set ({masked})")
    else:
        messages.append("⚠ BRAVE_API_KEY not set (optional)")
    
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if firecrawl_key:
        masked = firecrawl_key[:5] + "*" * (len(firecrawl_key) - 10) + firecrawl_key[-5:]
        messages.append(f"✓ FIRECRAWL_API_KEY set ({masked})")
    else:
        messages.append("⚠ FIRECRAWL_API_KEY not set (optional)")
    
    return True, messages


def check_imports() -> Tuple[bool, List[str]]:
    """Check if pipeline modules can be imported."""
    messages = []
    
    try:
        messages.append("✓ All pipeline modules import successfully")
        return True, messages
    except Exception as e:
        messages.append(f"✗ Import error: {e}")
        return False, messages


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("DATA PIPELINE VALIDATION")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Configuration", check_config),
        ("Environment Variables", check_environment_vars),
        ("Dependencies", check_dependencies),
        ("Module Imports", check_imports),
    ]
    
    all_passed = True
    
    for name, check_fn in checks:
        print(f"{name}:")
        passed, messages = check_fn()
        for msg in messages:
            print(f"  {msg}")
        print()
        
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All checks passed! Ready to run pipeline.")
        print("\nNext steps:")
        print("  1. Set API keys (if not already set):")
        print("     export BRAVE_API_KEY=your_key")
        print("     export FIRECRAWL_API_KEY=your_key")
        print("  2. Run pipeline:")
        print("     python main.py run")
        print("  3. View report:")
        print("     python main.py report")
    else:
        print("✗ Some checks failed. See above for details.")
        sys.exit(1)
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
