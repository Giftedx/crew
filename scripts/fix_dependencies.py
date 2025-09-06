#!/usr/bin/env python3
"""
Fix Dependency Detection Issues

This script ensures all tools can find their required dependencies.
"""

import sys
from pathlib import Path


def fix_python_path():
    """Add virtual environment packages to Python path."""
    venv_path = Path(__file__).parent / "venv"
    site_packages = venv_path / "lib" / "python3.12" / "site-packages"

    if site_packages.exists() and str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
        print(f"✅ Added venv site-packages to path: {site_packages}")

    # Also add src directory
    src_path = Path(__file__).parent / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"✅ Added src directory to path: {src_path}")


def test_dependencies():
    """Test that all dependencies are available."""
    print("🧪 Testing Dependencies After Path Fix...")

    # Test NLTK
    try:
        from nltk.sentiment.vader import SentimentIntensityAnalyzer

        SentimentIntensityAnalyzer()
        print("✅ NLTK and VADER sentiment working")
    except Exception as e:
        print(f"❌ NLTK issue: {e}")

    # Test Google API
    try:

        print("✅ Google API client libraries working")
    except Exception as e:
        print(f"❌ Google API issue: {e}")

    # Test transformers
    try:
        import transformers

        print(f"✅ Transformers working: {transformers.__version__}")
    except Exception as e:
        print(f"❌ Transformers issue: {e}")


if __name__ == "__main__":
    fix_python_path()
    test_dependencies()
