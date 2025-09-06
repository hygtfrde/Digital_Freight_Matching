#!/usr/bin/env python3

"""
Debug script to isolate the batch processing issue
"""

import sys
import importlib

# Force reload modules
if 'order_processor' in sys.modules:
    importlib.reload(sys.modules['order_processor'])

from order_processor import OrderProcessor
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType

def create_simple_test_data():
    """Create simple test data"""

    # Atlanta and Savannah
    atlanta = Location(lat=33.7490, lng=-84.3880)
    savannah = Location(lat=32.0835, lng=-81.0998)

    # Nearby location (should be valid)
    atlanta_nearby = Location(lat=33.7500, lng=-84.3890)

    # Far location (should be invalid)
    miami = Location(lat=25.7617, lng=-80.1918)

    # Create truck
    truck = Truck(
        id=1,
        autonomy=800.0,
        capacity=48.0,
        type="standard",
        cargo_loads=[]
    )

    # Create route
    route = Route(
        id=1,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=atlanta,
        location_destiny=savannah,
        path=[atlanta, savannah],
        profitability=-50.0
    )

    # Create orders
    package1 = Package(volume=2.0, weight=50.0, type=CargoType.STANDARD)
    cargo1 = Cargo(order_id=1, packages=[package1])

    package2 = Package(volume=1.5, weight=40.0, type=CargoType.STANDARD)
    cargo2 = Cargo(order_id=2, packages=[package2])

    order1 = Order(  # Should be VALID
        id=1,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=atlanta_nearby,
        location_destiny=savannah,
        cargo=[cargo1]
    )

    order2 = Order(  # Should be INVALID (too far)
        id=2,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=miami,  # Too far
        location_destiny=savannah,
        cargo=[cargo2]
    )

    return [truck], [route], [order1, order2]

def main():
    print("=== BATCH PROCESSING DEBUG ===")

    processor = OrderProcessor()
    trucks, routes, orders = create_simple_test_data()

    print(f"Created {len(orders)} orders, {len(routes)} routes, {len(trucks)} trucks")

    # Test individual validation first
    print("\n--- Individual Validation ---")
    for i, order in enumerate(orders, 1):
        result = processor.validate_order_for_route(order, routes[0], trucks[0])
        print(f"Order {i}: {'VALID' if result.is_valid else 'INVALID'} ({len(result.errors)} errors)")
        if result.errors:
            print(f"  Error: {result.errors[0].message}")

    # Test batch processing
    print("\n--- Batch Processing ---")
    batch_results = processor.process_order_batch(orders, routes, trucks)

    print("Batch results:")
    for order_id, result in batch_results.items():
        print(f"Order {order_id}: {'VALID' if result.is_valid else 'INVALID'} ({len(result.errors)} errors)")
        if result.errors:
            print(f"  Error: {result.errors[0].message}")

    # Check if results match
    print("\n--- Comparison ---")
    individual_results = []
    for order in orders:
        result = processor.validate_order_for_route(order, routes[0], trucks[0])
        individual_results.append(result.is_valid)

    batch_valid = [batch_results[order.id].is_valid for order in orders]

    print(f"Individual: {individual_results}")
    print(f"Batch:      {batch_valid}")
    print(f"Match:      {individual_results == batch_valid}")

if __name__ == "__main__":
    main()
