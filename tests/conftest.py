"""
Pytest configuration and fixtures for Digital Freight Matching tests

This file automatically sets up the Python path for all tests
so they can import modules from the parent directory.
"""

import sys
import os
from pathlib import Path

# Add the parent directory (project root) to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))