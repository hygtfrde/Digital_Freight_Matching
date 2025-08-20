#!/usr/bin/env python3
"""
Digital Freight Matcher Setup Script
Creates virtual environment, installs dependencies, and initializes database with starter data from PDF sheets
"""

import os
import subprocess
import sys
import venv
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
        print("Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    return os.path.join("venv", "bin", "python")

def get_venv_pip():
    """Get the path to the pip executable in the virtual environment"""
    return os.path.join("venv", "bin", "pip")

def check_venv_active():
    """Check if we're running in the virtual environment"""
    venv_python = get_venv_python()
    current_python = sys.executable
    
    # Normalize paths for comparison
    venv_python_abs = os.path.abspath(venv_python)
    current_python_abs = os.path.abspath(current_python)
    
    return venv_python_abs == current_python_abs

def install_dependencies():
    """Install required dependencies in virtual environment"""
    print("Installing dependencies in virtual environment...")
    
    venv_python = get_venv_python()
    
    # Use python -m pip instead of direct pip executable
    # Upgrade pip first
    try:
        subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        print("Upgraded pip in virtual environment")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to upgrade pip: {e}")
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("WARNING: requirements.txt not found, installing core dependencies...")
        dependencies = [
            "sqlmodel>=0.0.8",
            "pandas>=1.5.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6"
        ]
        
        for dep in dependencies:
            try:
                subprocess.check_call([venv_python, "-m", "pip", "install", dep])
                print(f"Installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to install {dep}: {e}")
                return False
    else:
        try:
            subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Dependencies installed from requirements.txt")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install dependencies: {e}")
            return False
    
    return True

def initialize_database():
    """Initialize database with starter data using virtual environment"""
    print("Initializing database with starter data...")
    
    venv_python = get_venv_python()
    
    try:
        # Run the safe initialization script with venv python
        subprocess.check_call([venv_python, "safe_db_init.py"])
        print("Database initialized successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to initialize database: {e}")
        return False

def verify_setup():
    """Verify the setup was successful using virtual environment"""
    print("Verifying setup...")
    
    venv_python = get_venv_python()
    
    try:
        # Run the verification script with venv python
        result = subprocess.run([venv_python, "verify_database.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Setup verification passed!")
            # Print the verification output
            print(result.stdout)
            return True
        else:
            print(f"ERROR: Setup verification failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Setup verification failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Digital Freight Matcher Setup")
    print("="*50)
    print("This script will:")
    print("1. Check Python version")
    print("2. Create virtual environment")
    print("3. Install required dependencies")
    print("4. Initialize database with starter data from PDF")
    print("5. Verify the setup")
    print("="*50)
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create virtual environment
    if not create_virtual_environment():
        print("ERROR: Virtual environment creation failed")
        sys.exit(1)
    
    # Check if we're running in the virtual environment
    if not check_venv_active():
        print("\nContinuing setup using virtual environment Python...")
        # Re-run this script with the virtual environment Python
        venv_python = get_venv_python()
        try:
            subprocess.check_call([venv_python] + sys.argv)
            return  # Exit this instance, the venv version will continue
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to run setup in virtual environment: {e}")
            sys.exit(1)
    
    # Step 3: Install dependencies
    if not install_dependencies():
        print("ERROR: Dependency installation failed")
        sys.exit(1)
    
    # Step 4: Initialize database
    if not initialize_database():
        print("ERROR: Database initialization failed")
        sys.exit(1)
    
    # Step 5: Verify setup
    if not verify_setup():
        print("ERROR: Setup verification failed")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("Your Digital Freight Matcher is ready!")
    print("\nTo use the application:")
    print("1. Activate virtual environment: source venv/bin/activate")
    print("2. Run 'python app/main.py' to start the API server")
    print("3. Open http://localhost:8000/docs for API documentation")
    print("4. Begin matching orders to optimize routes")
    print("\nDatabase file: logistics.db")
    print("Contains:")
    print("- Too-Big-To-Fail contract data")
    print("- 5 specialized trucks")
    print("- 5 loss-making routes")
    print("- Example orders for testing")
    print("- All Georgia locations")

if __name__ == "__main__":
    main()