#!/usr/bin/env python3
"""Wrapper script for running evaluations with proper Python path."""

import sys
import os
from pathlib import Path

# Add src to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

# Now run the evaluation
from eval.runner import main

if __name__ == "__main__":
    main()