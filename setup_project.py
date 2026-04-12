"""
Setup script for quick project initialization.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print status."""
    print(f"\n📦 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False
    return True


def main():
    """Initialize project environment."""
    print("🚀 Initializing automation pipeline project...")
    
    # Create virtual environment
    if not Path("venv").exists():
        if not run_command(
            f"{sys.executable} -m venv venv",
            "Creating virtual environment"
        ):
            return
    
    # Determine pip command based on OS
    pip_cmd = "venv\\Scripts\\pip" if sys.platform == "win32" else "venv/bin/pip"
    
    # Install dependencies
    if not run_command(
        f"{pip_cmd} install -r requirements.txt",
        "Installing dependencies"
    ):
        return
    
    # Run validation
    if not run_command(
        f"{sys.executable} validate.py",
        "Running validation"
    ):
        return
    
    # Generate example config
    if not run_command(
        f"{sys.executable} main.py example-config",
        "Generating example configuration"
    ):
        return
    
    print("\n" + "="*60)
    print("✅ Project initialization complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Set API keys:")
    print("   set BRAVE_API_KEY=your_key")
    print("   set FIRECRAWL_API_KEY=your_key")
    print("\n2. Review example config:")
    print("   cat config.example.yaml")
    print("\n3. Create your config:")
    print("   copy config.example.yaml config.yaml")
    print("   # Edit config.yaml with your companies")
    print("\n4. Run pipeline:")
    print("   python main.py run")
    print("\n5. Generate report:")
    print("   python main.py report")
    print("\n6. View dashboard:")
    print("   python dashboard.py")
    print("="*60)


if __name__ == "__main__":
    main()
