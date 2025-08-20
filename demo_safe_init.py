#!/usr/bin/env python3
"""
Demonstration of Safe Database Initialization
Shows the difference between old (unsafe) and new (safe) initialization
"""

import os
import sys
from sqlmodel import Session, select

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import Client, Location, Truck, Route, Order, engine, create_tables
from safe_db_init import SafeDataIngestion

def count_entities(session: Session) -> dict:
    """Count all database entities"""
    return {
        'clients': len(session.exec(select(Client)).all()),
        'locations': len(session.exec(select(Location)).all()),
        'trucks': len(session.exec(select(Truck)).all()),
        'routes': len(session.exec(select(Route)).all()),
        'orders': len(session.exec(select(Order)).all())
    }

def print_counts(counts: dict, label: str):
    """Print entity counts with a label"""
    print(f"\n{label}:")
    for entity, count in counts.items():
        print(f"  {entity.capitalize()}: {count}")

def demonstrate_safe_initialization():
    """Demonstrate the safe initialization behavior"""
    print("Digital Freight Matcher - Safe Initialization Demo")
    print("="*60)
    
    create_tables()
    
    with Session(engine) as session:
        # Show current state
        initial_counts = count_entities(session)
        print_counts(initial_counts, "Current Database State")
        
        print(f"\n{'='*60}")
        print("DEMONSTRATION: Safe vs Unsafe Initialization")
        print("="*60)
        
        # Safe initialization (first time)
        print("\n1. Running SAFE initialization...")
        ingestion = SafeDataIngestion(session)
        ingestion.initialize_safely()
        
        after_safe_counts = count_entities(session)
        print_counts(after_safe_counts, "After Safe Initialization")
        
        # Safe initialization (second time - should skip)
        print("\n2. Running SAFE initialization again (should skip)...")
        ingestion2 = SafeDataIngestion(session)
        ingestion2.initialize_safely()
        
        after_safe_again_counts = count_entities(session)
        print_counts(after_safe_again_counts, "After Second Safe Initialization")
        
        # Check if counts are the same
        if after_safe_counts == after_safe_again_counts:
            print("\n✅ SUCCESS: Safe initialization prevented duplicates!")
        else:
            print("\n❌ ERROR: Duplicates were created!")
        
        print(f"\n{'='*60}")
        print("COMPARISON: What would happen with unsafe initialization")
        print("="*60)
        
        print("\n3. Simulating UNSAFE initialization (force mode)...")
        print("   This demonstrates what the old scripts would do...")
        
        ingestion3 = SafeDataIngestion(session)
        ingestion3.initialize_safely(force_reinit=True)
        
        after_unsafe_counts = count_entities(session)
        print_counts(after_unsafe_counts, "After Forced (Unsafe) Initialization")
        
        # Show the difference
        print(f"\n{'='*60}")
        print("RESULTS COMPARISON")
        print("="*60)
        
        print("\nEntity count changes:")
        for entity in initial_counts.keys():
            initial = initial_counts[entity]
            safe = after_safe_again_counts[entity]
            unsafe = after_unsafe_counts[entity]
            
            print(f"  {entity.capitalize()}:")
            print(f"    Initial: {initial}")
            print(f"    After safe init: {safe} (+{safe - initial})")
            print(f"    After unsafe init: {unsafe} (+{unsafe - initial})")
            
            if unsafe > safe:
                print(f"    ⚠️  Unsafe created {unsafe - safe} duplicates!")
        
        print(f"\n{'='*60}")
        print("KEY BENEFITS OF SAFE INITIALIZATION")
        print("="*60)
        print("✅ Prevents duplicate data")
        print("✅ Idempotent - can run multiple times safely")
        print("✅ Detects existing data intelligently")
        print("✅ Provides clear logging")
        print("✅ Maintains data integrity")
        print("✅ Backward compatible with existing databases")
        
        print(f"\n{'='*60}")
        print("USAGE RECOMMENDATIONS")
        print("="*60)
        print("🔧 Use 'python manage_db.py init' for safe initialization")
        print("🔧 Use 'python manage_db.py status' to check database state")
        print("🔧 Use 'python manage_db.py verify' to validate data")
        print("🔧 Only use --force flag for development/testing")

if __name__ == "__main__":
    demonstrate_safe_initialization()