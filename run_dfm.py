#!/usr/bin/env python3
"""
Digital Freight Matcher Runner
Ensures the application runs in the virtual environment
"""

import os
import subprocess
import sys
from pathlib import Path

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    return os.path.join("venv", "bin", "python")

def check_venv_exists():
    """Check if virtual environment exists"""
    venv_path = Path("venv")
    venv_python = Path(get_venv_python())
    return venv_path.exists() and venv_python.exists()

def main():
    """Main runner function"""
    if len(sys.argv) < 2:
        print("Digital Freight Matcher Runner")
        print("Usage: python run_dfm.py <script_name> [args...]")
        print()
        print("Examples:")
        print("  python run_dfm.py verify_database.py")
        print("  python run_dfm.py app/main.py")
        print("  python run_dfm.py unified_db_init.py")
        sys.exit(1)
    
    if not check_venv_exists():
        print("ERROR: Virtual environment not found!")
        print("Please run 'python setup_dfm.py' first to create the virtual environment.")
        sys.exit(1)
    
    venv_python = get_venv_python()
    script_name = sys.argv[1]
    script_args = sys.argv[2:]
    
    # Check if script exists
    if not os.path.exists(script_name):
        print(f"ERROR: Script '{script_name}' not found!")
        sys.exit(1)
    
    print(f"Running {script_name} in virtual environment...")
    
    try:
        # Run the script with the virtual environment Python
        cmd = [venv_python, script_name] + script_args
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Script execution failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()