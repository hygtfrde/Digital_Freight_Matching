#!/usr/bin/env python3
"""
Test script to demonstrate safe database initialization
Shows how the system prevents duplicate data seeding
"""

import os
import sys
from sqlmodel import Session, select

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import Client, Location, Truck, Route, Order, engine, create_tables
from safe_db_init import SafeDataIngestion

def print_database_counts(session: Session, label: str):
    """Print current database entity counts"""
    clients = len(session.exec(select(Client)).all())
    locations = len(session.exec(select(Location)).all())
    trucks = len(session.exec(select(Truck)).all())
    routes = len(session.exec(select(Route)).all())
    orders = len(session.exec(select(Order)).all())
    
    print(f"\n{label}:")
    print(f"  Clients: {clients}")
    print(f"  Locations: {locations}")
    print(f"  Trucks: {trucks}")
    print(f"  Routes: {routes}")
    print(f"  Orders: {orders}")

def test_safe_initialization():
    """Test the safe initialization process"""
    print("Testing Safe Database Initialization")
    print("="*50)
    
    # Ensure tables exist
    create_tables()
    
    with Session(engine) as session:
        # Show initial state
        print_database_counts(session, "Initial Database State")
        
        # First initialization
        print("\n1. Running first initialization...")
        ingestion = SafeDataIngestion(session)
        ingestion.initialize_safely()
        
        print_database_counts(session, "After First Initialization")
        
        # Second initialization (should skip due to existing data)
        print("\n2. Running second initialization (should skip)...")
        ingestion2 = SafeDataIngestion(session)
        ingestion2.initialize_safely()
        
        print_database_counts(session, "After Second Initialization (Should be Same)")
        
        # Force initialization (will create duplicates)
        print("\n3. Running forced initialization (will create duplicates)...")
        ingestion3 = SafeDataIngestion(session)
        ingestion3.initialize_safely(force_reinit=True)
        
        print_database_counts(session, "After Forced Initialization (May Have Duplicates)")

if __name__ == "__main__":
    test_safe_initialization()