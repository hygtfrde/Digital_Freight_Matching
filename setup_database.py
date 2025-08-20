#!/usr/bin/env python3
"""
Simple setup script to install dependencies and initialize the contract database.
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_initialization():
    """Run the database initialization"""
    print("🗄️  Initializing database...")
    try:
        # Import and run safe initialization after dependencies are installed
        exec(open('safe_db_init.py').read())
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Digital Freight Matcher database...")
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Initialize database
    if not run_initialization():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("You can now run 'python verify_database.py' to check the data.")

if __name__ == "__main__":
    main()