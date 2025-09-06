"""
Demo script showing Order Processing Engine in action

Demonstrates:
- Order validation against routes and trucks
- Proximity, capacity, time, and cargo compatibility checking
- Batch processing of multiple orders
- Integration with existing DFM system
"""

from order_processor import OrderProcessor, OrderProcessingConstants
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


def create_demo_data():
    """Create demo data for testing"""
    
    # Atlanta area locations
    atlanta = Location(lat=33.7490, lng=-84.3880)
    savannah = Location(lat=32.0835, lng=-81.0998)
    augusta = Location(lat=33.4735, lng=-82.0105)
    
    # Nearby locations (within 1km)
    atlanta_nearby = Location(lat=33.7500, lng=-84.3890)
    savannah_nearby = Location(lat=32.0845, lng=-81.1008)
    
    # Far locations (outside 1km)
    miami = Location(lat=25.7617, lng=-80.1918)
    
    # Create trucks with different capacities
    trucks = [
        Truck(
            id=1,
            autonomy=800.0,
            capacity=48.0,  # 48 cubic meters
            type="standard",
            cargo_loads=[]
        ),
        Truck(
            id=2,
            autonomy=600.0,
            capacity=36.0,  # 36 cubic meters
            type="refrigerated",
            cargo_loads=[]
        )
    ]
    
    # Create routes
    routes = [
        Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=atlanta,
            location_destiny=savannah,
            path=[atlanta, savannah],
            profitability=-50.0
        ),
        Route(
            id=2,
            location_origin_id=1,
            location_destiny_id=3,
            location_origin=atlanta,
            location_destiny=augusta,
            path=[atlanta, augusta],
            profitability=-30.0
        )
    ]
    
    # Create test orders
    orders = []
    
    # Order 1: Valid order (nearby locations, reasonable cargo)
    package1 = Package(volume=2.0, weight=50.0, type=CargoType.STANDARD)
    cargo1 = Cargo(order_id=1, packages=[package1])
    order1 = Order(
        id=1,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=atlanta_nearby,
        location_destiny=savannah_nearby,
        cargo=[cargo1]
    )
    orders.append(order1)
    
    # Order 2: Invalid proximity (too far from route)
    package2 = Package(volume=1.5, weight=40.0, type=CargoType.STANDARD)
    cargo2 = Cargo(order_id=2, packages=[package2])
    order2 = Order(
        id=2,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=miami,  # Too far from Atlanta-Savannah route
        location_destiny=savannah_nearby,
        cargo=[cargo2]
    )
    orders.append(order2)
    
    # Order 3: Invalid capacity (too large)
    large_package = Package(volume=50.0, weight=2000.0, type=CargoType.STANDARD)
    large_cargo = Cargo(order_id=3, packages=[large_package])
    order3 = Order(
        id=3,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=atlanta_nearby,
        location_destiny=savannah_nearby,
        cargo=[large_cargo]
    )
    orders.append(order3)
    
    # Order 4: Refrigerated cargo (needs special truck)
    cold_package = Package(volume=3.0, weight=75.0, type=CargoType.REFRIGERATED)
    cold_cargo = Cargo(order_id=4, packages=[cold_package])
    order4 = Order(
        id=4,
        location_origin_id=1,
        location_destiny_id=3,
        location_origin=atlanta_nearby,
        location_destiny=Location(lat=33.4745, lng=-82.0115),  # Near Augusta
        cargo=[cold_cargo]
    )
    orders.append(order4)
    
    return trucks, routes, orders


def demo_individual_validation():
    """Demonstrate individual order validation"""
    print("=" * 60)
    print("INDIVIDUAL ORDER VALIDATION DEMO")
    print("=" * 60)
    
    processor = OrderProcessor()
    trucks, routes, orders = create_demo_data()
    
    for i, order in enumerate(orders, 1):
        print(f"\n--- Order {i} Validation ---")
        print(f"Pickup: ({order.location_origin.lat:.4f}, {order.location_origin.lng:.4f})")
        print(f"Dropoff: ({order.location_destiny.lat:.4f}, {order.location_destiny.lng:.4f})")
        print(f"Cargo: {len(order.cargo)} items, {order.total_volume():.1f}m³, {order.total_weight():.1f}kg")
        
        # Test against first route and truck
        result = processor.validate_order_for_route(order, routes[0], trucks[0])
        
        if result.is_valid:
            print("✅ VALID - Order can be processed")
        else:
            print("❌ INVALID - Validation errors:")
            for error in result.errors:
                print(f"   • {error.message}")
        
        # Show key metrics
        if result.metrics:
            print("📊 Metrics:")
            print(f"   • Volume utilization: {result.metrics.get('volume_utilization_percent', 0):.1f}%")
            print(f"   • Weight utilization: {result.metrics.get('weight_utilization_percent', 0):.1f}%")
            print(f"   • Additional cost: ${result.metrics.get('additional_cost_usd', 0):.2f}")


def demo_batch_processing():
    """Demonstrate batch processing of orders"""
    print("\n" + "=" * 60)
    print("BATCH PROCESSING DEMO")
    print("=" * 60)
    
    processor = OrderProcessor()
    trucks, routes, orders = create_demo_data()
    
    # Test each order against each route individually
    print("\n_Testing each order against available routes:")
    
    valid_count = 0
    for i, order in enumerate(orders, 1):
        print(f"\n--- Order {i} ---")
        print(f"Pickup: ({order.location_origin.lat:.4f}, {order.location_origin.lng:.4f})")
        print(f"Dropoff: ({order.location_destiny.lat:.4f}, {order.location_destiny.lng:.4f})")
        
        best_result = None
        best_route = None
        best_truck = None
        
        # Try each route-truck combination
        for j, route in enumerate(routes):
            truck = trucks[j] if j < len(trucks) else trucks[0]
            result = processor.validate_order_for_route(order, route, truck)
            
            print(f"  Route {j+1} + Truck {truck.id}: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
            if not result.is_valid and len(result.errors) > 0:
                print(f"    Error: {result.errors[0].message}")
            
            # Keep track of the best (first valid) result
            if result.is_valid and best_result is None:
                best_result = result
                best_route = j + 1
                best_truck = truck.id
        
        # Show final result for this order
        if best_result:
            print(f"  ✅ MATCHED to Route {best_route} + Truck {best_truck}")
            valid_count += 1
        else:
            print(f"  ❌ NO MATCH FOUND")
    
    print(f"\n" + "=" * 40)
    print(f"SUMMARY: {valid_count}/{len(orders)} orders successfully matched ({valid_count/len(orders)*100:.1f}%)")
    
    if valid_count == len(orders):
        print("🎉 All orders can be processed!")
    elif valid_count > 0:
        print("⚠️  Some orders need alternative solutions")
    else:
        print("❌ No orders can be processed with current routes")


def demo_constants_usage():
    """Demonstrate usage of business constants"""
    print("\n" + "=" * 60)
    print("BUSINESS CONSTANTS DEMO")
    print("=" * 60)
    
    constants = OrderProcessingConstants()
    
    print("📋 Truck Specifications (from documentation):")
    print(f"   • Total cost per mile: ${constants.TOTAL_COST_PER_MILE:.6f}")
    print(f"   • Max weight: {constants.MAX_WEIGHT_LBS:,} lbs")
    print(f"   • Total volume: {constants.TOTAL_VOLUME_CUBIC_FEET:,} cubic feet")
    print(f"   • Average speed: {constants.AVG_SPEED_MPH} mph")
    print(f"   • Miles per gallon: {constants.MILES_PER_GALLON}")
    
    print("\n🚛 Pallet Information:")
    print(f"   • Pallets per truck: {constants.PALLETS_PER_TRUCK}")
    print(f"   • Pallet weight: {constants.PALLET_WEIGHT_LBS} lbs")
    print(f"   • Pallet volume: {constants.PALLET_VOLUME_CUBIC_FEET} cubic feet")
    print(f"   • Pallet cost per mile: ${constants.PALLET_COST_PER_MILE:.8f}")
    
    print("\n📏 Business Rules:")
    print(f"   • Max proximity: {constants.MAX_PROXIMITY_KM} km")
    print(f"   • Stop time: {constants.STOP_TIME_MINUTES} minutes")
    print(f"   • Max route time: {constants.MAX_ROUTE_HOURS} hours")
    
    # Calculate example costs
    print("\n💰 Example Cost Calculation (100 mile route):")
    distance_miles = 100
    total_cost = distance_miles * constants.TOTAL_COST_PER_MILE
    fuel_cost = distance_miles * constants.FUEL_COST_PER_MILE
    trucker_cost = distance_miles * constants.TRUCKER_COST_PER_MILE
    
    print(f"   • Total cost: ${total_cost:.2f}")
    print(f"   • Fuel cost: ${fuel_cost:.2f}")
    print(f"   • Trucker cost: ${trucker_cost:.2f}")


def demo_capacity_calculations():
    """Demonstrate capacity calculations with real units"""
    print("\n" + "=" * 60)
    print("CAPACITY CALCULATIONS DEMO")
    print("=" * 60)
    
    constants = OrderProcessingConstants()
    
    # Standard truck capacity
    truck_capacity_m3 = 48.0  # Standard truck capacity in cubic meters
    truck_capacity_cf = truck_capacity_m3 / constants.CUBIC_FEET_TO_CUBIC_METERS
    
    print(f"🚛 Standard Truck Capacity:")
    print(f"   • {truck_capacity_m3:.1f} cubic meters")
    print(f"   • {truck_capacity_cf:.1f} cubic feet")
    print(f"   • Max weight: {constants.MAX_WEIGHT_LBS:,} lbs ({constants.MAX_WEIGHT_LBS * constants.LBS_TO_KG:.0f} kg)")
    
    # Example order
    order_volume_m3 = 5.0
    order_weight_kg = 200.0
    order_volume_cf = order_volume_m3 / constants.CUBIC_FEET_TO_CUBIC_METERS
    order_weight_lbs = order_weight_kg / constants.LBS_TO_KG
    
    print(f"\n📦 Example Order:")
    print(f"   • Volume: {order_volume_m3:.1f} m³ ({order_volume_cf:.1f} cf)")
    print(f"   • Weight: {order_weight_kg:.1f} kg ({order_weight_lbs:.1f} lbs)")
    
    # Utilization calculations
    volume_util = (order_volume_cf / truck_capacity_cf) * 100
    weight_util = (order_weight_lbs / constants.MAX_WEIGHT_LBS) * 100
    
    print(f"\n📊 Utilization:")
    print(f"   • Volume utilization: {volume_util:.1f}%")
    print(f"   • Weight utilization: {weight_util:.1f}%")
    
    # Remaining capacity
    remaining_volume_cf = truck_capacity_cf - order_volume_cf
    remaining_weight_lbs = constants.MAX_WEIGHT_LBS - order_weight_lbs
    
    print(f"\n🔄 Remaining Capacity:")
    print(f"   • Volume: {remaining_volume_cf:.1f} cf ({remaining_volume_cf * constants.CUBIC_FEET_TO_CUBIC_METERS:.1f} m³)")
    print(f"   • Weight: {remaining_weight_lbs:.1f} lbs ({remaining_weight_lbs * constants.LBS_TO_KG:.1f} kg)")


if __name__ == "__main__":
    print("🚛 ORDER PROCESSING ENGINE DEMO")
    print("Using exact constants from documentation")
    
    demo_constants_usage()
    demo_capacity_calculations()
    demo_individual_validation()
    demo_batch_processing()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("Order Processing Engine ready for integration!")
    print("=" * 60)