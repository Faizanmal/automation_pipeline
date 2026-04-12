"""Pytest configuration and fixtures."""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test."""
    # Store original env
    original_env = os.environ.copy()
    
    yield
    
    # Restore env
    os.environ.clear()
    os.environ.update(original_env)
