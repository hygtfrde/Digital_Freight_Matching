#!/usr/bin/env python3
"""Quick test to debug route generation error"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from sqlmodel import Session
from app.database import engine, Route, Location

# Test the Route path functionality directly
with Session(engine) as session:
    # Create test locations
    loc1 = Location(lat=33.7490, lng=-84.3880, marked=False)
    loc2 = Location(lat=32.0835, lng=-81.0998, marked=False)
    
    session.add_all([loc1, loc2])
    session.flush()
    
    # Create test route
    route = Route(
        location_origin_id=loc1.id,
        location_destiny_id=loc2.id,
        profitability=100.0
    )
    
    print("Route created successfully")
    
    # Test set_path
    try:
        route.set_path([loc1, loc2])
        print("set_path worked!")
        print(f"Route has path: {hasattr(route, 'path')}")
        if hasattr(route, 'path'):
            print(f"Path length: {len(route.path)}")
    except Exception as e:
        print(f"set_path failed: {e}")
        import traceback
        traceback.print_exc()

print("Test complete")