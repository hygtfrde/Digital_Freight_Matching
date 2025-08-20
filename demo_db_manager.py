#!/usr/bin/env python3
"""
Demo script showing how to use the DatabaseManager
"""

import sys
import os
from sqlmodel import Session

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import engine
from db_manager import DatabaseManager

def demo_database_manager():
    """Demonstrate DatabaseManager functionality"""
    print("="*60)
    print("DATABASE MANAGER DEMONSTRATION")
    print("="*60)
    
    with Session(engine) as session:
        db_manager = DatabaseManager(session)
        
        print("\n1. Checking existing data...")
        existing_data, counts = db_manager.check_existing_data()
        print(f"Found: {counts}")
        
        print("\n2. Verifying database integrity...")
        integrity_counts = db_manager.verify_integrity()
        print(f"Integrity check completed. Counts: {integrity_counts}")
        
        print("\n3. Getting system status...")
        status = db_manager.get_system_status()
        print(f"System Status:")
        print(f"  - Total Routes: {status.total_routes}")
        print(f"  - Daily Profit/Loss: ${status.daily_profit_loss:.2f}")
        print(f"  - Pending Orders: {status.pending_orders}")
        print(f"  - Active Contracts: {status.active_contracts}")
        print(f"  - Truck Utilization: {status.truck_utilization:.1f}%")
        print(f"  - Clients: {status.clients}")
        print(f"  - Locations: {status.locations}")
        print(f"  - Trucks: {status.trucks}")
        print(f"  - Orders: {status.orders}")
        print(f"  - Cargo Loads: {status.cargo_loads}")
        print(f"  - Packages: {status.packages}")
        print(f"  - Last Updated: {status.last_updated}")
        
        print("\n4. Testing safe initialization...")
        success = db_manager.initialize_database()
        if success:
            print("Database was initialized successfully")
        else:
            print("Database initialization was skipped (data already exists)")
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED")
        print("="*60)
        print("\nThe DatabaseManager provides:")
        print("- Safe initialization that prevents duplicates")
        print("- Database integrity checking")
        print("- Comprehensive system status reporting")
        print("- Consolidated functionality from multiple scripts")
        print("- Proper error handling and logging")

if __name__ == "__main__":
    demo_database_manager()