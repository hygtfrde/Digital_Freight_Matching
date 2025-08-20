#!/usr/bin/env python3
"""
Database Management CLI for Digital Freight Matcher
Provides commands to safely initialize, reset, and verify the database
"""

import argparse
import os
import sys
from sqlmodel import Session

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import create_tables, engine
from safe_db_init import SafeDataIngestion

def init_database(force: bool = False):
    """Initialize database with contract data"""
    print("Initializing database...")
    create_tables()
    
    with Session(engine) as session:
        ingestion = SafeDataIngestion(session)
        ingestion.initialize_safely(force_reinit=force)

def verify_database():
    """Verify database contents"""
    try:
        from verify_database import verify_database as verify_func
        return verify_func()
    except ImportError:
        print("Error: verify_database.py not found")
        return False

def reset_database():
    """Reset database by removing the file"""
    db_file = "logistics.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed {db_file}")
    else:
        print(f"{db_file} does not exist")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Digital Freight Matcher Database Management")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database with contract data')
    init_parser.add_argument('--force', '-f', action='store_true', 
                           help='Force initialization even if data exists (may create duplicates)')
    
    # Verify command
    subparsers.add_parser('verify', help='Verify database contents')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database (removes all data)')
    reset_parser.add_argument('--confirm', action='store_true', 
                            help='Confirm database reset')
    
    # Status command
    subparsers.add_parser('status', help='Show database status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'init':
            init_database(force=args.force)
            
        elif args.command == 'verify':
            verify_database()
            
        elif args.command == 'reset':
            if not args.confirm:
                print("Warning: This will delete all database data!")
                confirm = input("Type 'yes' to confirm: ")
                if confirm.lower() != 'yes':
                    print("Reset cancelled")
                    return
            reset_database()
            
        elif args.command == 'status':
            create_tables()
            with Session(engine) as session:
                ingestion = SafeDataIngestion(session)
                existing_data, counts = ingestion.check_existing_data()
                
                print("Database Status:")
                print("="*30)
                for entity, count in counts.items():
                    print(f"{entity.capitalize()}: {count}")
                
                is_initialized = ingestion.is_database_initialized(counts)
                print(f"\nInitialized: {'Yes' if is_initialized else 'No'}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()