#!/usr/bin/env python3
"""
Virtual Environment Activation Helper
Provides instructions for activating the virtual environment
"""

import os
import sys
from pathlib import Path

def main():
    """Show virtual environment activation instructions"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("ERROR: Virtual environment not found!")
        print("Please run 'python setup_dfm.py' first to create the virtual environment.")
        sys.exit(1)
    
    print("Digital Freight Matcher - Virtual Environment")
    print("="*50)
    
    activate_script = "source venv/bin/activate"
    python_path = "venv/bin/python"
    
    print("To activate the virtual environment:")
    print(f"  {activate_script}")
    print()
    print("To run commands directly with the virtual environment:")
    print(f"  {python_path} <script_name>")
    print()
    print("Example commands:")
    print(f"  {python_path} verify_database.py")
    print(f"  {python_path} app/main.py")
    print()
    print("To deactivate the virtual environment (when active):")
    print("  deactivate")

if __name__ == "__main__":
    main()