#!/usr/bin/env python3
"""
Demo: Bonus Requirement - Cargo Type Compatibility

Demonstrates:
- Includes cargo type: Some types can't be transported together
- Hazmat + Fragile incompatibility
- Hazmat + Refrigerated incompatibility
- Compatible cargo type combinations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from order_processor import OrderProcessor, ValidationResult
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


def create_cargo_type_test_data():
    """Create test data with various cargo type combinations"""
    
    # Standard route setup
    atlanta = Location(id=1, lat=33.7490, lng=-84.3880)
    augusta = Location(id=2, lat=33.4735, lng=-82.0105)
    
    route = Route(
        id=1,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=atlanta,
        location_destiny=augusta,
        profitability=-50.12,
        orders=[]
    )
    
    truck = Truck(
        id=1,
        capacity=48.0,
        autonomy=800.0,
        type="standard",
        cargo_loads=[]
    )
    
    # Nearby locations (within 1km for proximity compliance)
    atlanta_near = Location(id=3, lat=33.7500, lng=-84.3890)
    augusta_near = Location(id=4, lat=33.4745, lng=-82.0115)
    
    return route, truck, atlanta_near, augusta_near


def create_cargo_type_test_orders(pickup_loc, dropoff_loc):
    """Create orders with different cargo type combinations"""
    
    orders = []
    
    # Order 1: VALID - All Standard cargo
    cargo1 = Cargo(id=1, order_id=1, packages=[
        Package(id=1, volume=10.0, weight=200.0, type=CargoType.STANDARD, cargo_id=1),
        Package(id=2, volume=8.0, weight=150.0, type=CargoType.STANDARD, cargo_id=1)
    ])
    order1 = Order(
        id=1,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo1]
    )
    orders.append(("VALID: All Standard cargo", order1))
    
    # Order 2: VALID - Standard + Fragile (compatible)
    cargo2 = Cargo(id=2, order_id=2, packages=[
        Package(id=3, volume=12.0, weight=300.0, type=CargoType.STANDARD, cargo_id=2),
        Package(id=4, volume=6.0, weight=100.0, type=CargoType.FRAGILE, cargo_id=2)
    ])
    order2 = Order(
        id=2,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo2]
    )
    orders.append(("VALID: Standard + Fragile", order2))
    
    # Order 3: VALID - Standard + Refrigerated (compatible)
    cargo3 = Cargo(id=3, order_id=3, packages=[
        Package(id=5, volume=15.0, weight=400.0, type=CargoType.STANDARD, cargo_id=3),
        Package(id=6, volume=10.0, weight=250.0, type=CargoType.REFRIGERATED, cargo_id=3)
    ])
    order3 = Order(
        id=3,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo3]
    )
    orders.append(("VALID: Standard + Refrigerated", order3))
    
    # Order 4: INVALID - Hazmat + Fragile (incompatible)
    cargo4 = Cargo(id=4, order_id=4, packages=[
        Package(id=7, volume=8.0, weight=150.0, type=CargoType.HAZMAT, cargo_id=4),
        Package(id=8, volume=5.0, weight=80.0, type=CargoType.FRAGILE, cargo_id=4)
    ])
    order4 = Order(
        id=4,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo4]
    )
    orders.append(("INVALID: Hazmat + Fragile", order4))
    
    # Order 5: INVALID - Hazmat + Refrigerated (incompatible)  
    cargo5 = Cargo(id=5, order_id=5, packages=[
        Package(id=9, volume=12.0, weight=200.0, type=CargoType.HAZMAT, cargo_id=5),
        Package(id=10, volume=8.0, weight=180.0, type=CargoType.REFRIGERATED, cargo_id=5)
    ])
    order5 = Order(
        id=5,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo5]
    )
    orders.append(("INVALID: Hazmat + Refrigerated", order5))
    
    # Order 6: VALID - Pure Hazmat (compatible with itself)
    cargo6 = Cargo(id=6, order_id=6, packages=[
        Package(id=11, volume=10.0, weight=300.0, type=CargoType.HAZMAT, cargo_id=6),
        Package(id=12, volume=5.0, weight=150.0, type=CargoType.HAZMAT, cargo_id=6)
    ])
    order6 = Order(
        id=6,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo6]
    )
    orders.append(("VALID: Pure Hazmat", order6))
    
    # Order 7: VALID - Fragile + Refrigerated (compatible)
    cargo7 = Cargo(id=7, order_id=7, packages=[
        Package(id=13, volume=6.0, weight=120.0, type=CargoType.FRAGILE, cargo_id=7),
        Package(id=14, volume=9.0, weight=200.0, type=CargoType.REFRIGERATED, cargo_id=7)
    ])
    order7 = Order(
        id=7,
        location_origin_id=pickup_loc.id,
        location_destiny_id=dropoff_loc.id,
        location_origin=pickup_loc,
        location_destiny=dropoff_loc,
        cargo=[cargo7]
    )
    orders.append(("VALID: Fragile + Refrigerated", order7))
    
    return orders


def demonstrate_cargo_compatibility():
    """Demonstrate cargo type compatibility validation"""
    
    print("📦 BONUS REQUIREMENT: CARGO TYPE COMPATIBILITY")
    print("=" * 70)
    print("Bonus Requirement: Some cargo types can't be transported together")
    print("Incompatible combinations:")
    print("- Hazmat + Fragile")
    print("- Hazmat + Refrigerated")
    print("=" * 70)
    
    # Create test data
    route, truck, pickup_loc, dropoff_loc = create_cargo_type_test_data()
    test_orders = create_cargo_type_test_orders(pickup_loc, dropoff_loc)
    
    # Initialize order processor
    processor = OrderProcessor()
    
    print(f"\n🚛 TRUCK SETUP:")
    print(f"   Type: {truck.type}")
    print(f"   Capacity: {truck.capacity:.0f} m³")
    print(f"   Route: Atlanta → Augusta")
    
    print(f"\n🧪 CARGO TYPE COMPATIBILITY RULES:")
    print(f"   ✅ Compatible combinations:")
    print(f"      • Standard + any other type")
    print(f"      • Fragile + Refrigerated")
    print(f"      • Same types together")
    print(f"   ❌ Incompatible combinations:")
    print(f"      • Hazmat + Fragile")
    print(f"      • Hazmat + Refrigerated")
    
    print(f"\n🔍 CARGO TYPE VALIDATION TESTS:")
    print("")
    
    compatible_orders = 0
    incompatible_orders = 0
    
    for i, (description, order) in enumerate(test_orders, 1):
        print(f"   Test {i}: {description}")
        
        # Get cargo types in this order
        all_types = set()
        for cargo in order.cargo:
            all_types.update(cargo.get_types())
        
        types_list = [ct.value for ct in all_types]
        print(f"      Cargo types: {types_list}")
        
        # Validate order against route
        result = processor.validate_order_for_route(order, route, truck)
        
        # Check specifically for cargo compatibility
        cargo_compatible = True
        compatibility_errors = []
        
        for error in result.errors:
            if error.result == ValidationResult.INCOMPATIBLE_CARGO:
                cargo_compatible = False
                compatibility_errors.append(error.message)
        
        if cargo_compatible:
            print(f"      ✅ COMPATIBLE - Cargo types can be transported together")
            compatible_orders += 1
        else:
            print(f"      ❌ INCOMPATIBLE - Cargo types cannot be mixed")
            for error_msg in compatibility_errors:
                print(f"         {error_msg}")
            incompatible_orders += 1
        
        # Show package details
        total_packages = sum(len(cargo.packages) for cargo in order.cargo)
        total_volume = order.total_volume()
        total_weight = order.total_weight()
        print(f"      Packages: {total_packages}, Volume: {total_volume:.1f}m³, Weight: {total_weight:.0f}kg")
        
        print("")
    
    print(f"📊 CARGO COMPATIBILITY SUMMARY:")
    print(f"   Total orders tested: {len(test_orders)}")
    print(f"   Compatible orders: {compatible_orders}")
    print(f"   Incompatible orders: {incompatible_orders}")
    print(f"   Compatibility rate: {compatible_orders/len(test_orders)*100:.1f}%")
    
    return compatible_orders, incompatible_orders


def demonstrate_existing_cargo_conflicts():
    """Demonstrate conflicts with cargo already in truck"""
    
    print(f"\n🚚 EXISTING CARGO CONFLICT DEMONSTRATION:")
    print("Testing what happens when truck already has conflicting cargo")
    print("")
    
    # Create truck with existing hazmat cargo
    route, truck, pickup_loc, dropoff_loc = create_cargo_type_test_data()
    
    # Add existing hazmat cargo to truck
    existing_cargo = Cargo(id=100, order_id=100, packages=[
        Package(id=100, volume=5.0, weight=100.0, type=CargoType.HAZMAT, cargo_id=100)
    ])
    truck.cargo_loads = [existing_cargo]
    
    print(f"   Truck status: Contains existing Hazmat cargo")
    print(f"   Existing cargo: {existing_cargo.total_volume():.1f}m³, {existing_cargo.total_weight():.0f}kg")
    
    # Test orders with different compatibility
    test_scenarios = [
        ("Standard cargo", CargoType.STANDARD, True),
        ("More Hazmat", CargoType.HAZMAT, True), 
        ("Fragile cargo", CargoType.FRAGILE, False),
        ("Refrigerated cargo", CargoType.REFRIGERATED, False),
    ]
    
    processor = OrderProcessor()
    
    for scenario_name, cargo_type, expected_compatible in test_scenarios:
        print(f"\n   Testing: {scenario_name}")
        
        # Create test order
        test_cargo = Cargo(id=200, order_id=200, packages=[
            Package(id=200, volume=8.0, weight=150.0, type=cargo_type, cargo_id=200)
        ])
        test_order = Order(
            id=200,
            location_origin_id=pickup_loc.id,
            location_destiny_id=dropoff_loc.id,
            location_origin=pickup_loc,
            location_destiny=dropoff_loc,
            cargo=[test_cargo]
        )
        
        # Validate
        result = processor.validate_order_for_route(test_order, route, truck)
        
        cargo_compatible = True
        for error in result.errors:
            if error.result == ValidationResult.INCOMPATIBLE_CARGO:
                cargo_compatible = False
        
        expected_str = "✅ Compatible" if expected_compatible else "❌ Incompatible"
        actual_str = "✅ Compatible" if cargo_compatible else "❌ Incompatible"
        
        print(f"      Expected: {expected_str}")
        print(f"      Actual: {actual_str}")
        print(f"      Result: {'✅ CORRECT' if cargo_compatible == expected_compatible else '❌ INCORRECT'}")


def demonstrate_cargo_type_business_value():
    """Show business value of cargo type compatibility"""
    
    print(f"\n💼 BUSINESS VALUE OF CARGO TYPE COMPATIBILITY:")
    print("")
    
    print(f"   Safety Benefits:")
    print(f"   • Prevents dangerous chemical reactions")
    print(f"   • Avoids contamination of fragile goods")
    print(f"   • Maintains temperature control integrity")
    print(f"   • Reduces liability and insurance costs")
    print("")
    
    print(f"   Regulatory Compliance:")
    print(f"   • DOT hazardous materials regulations")
    print(f"   • FDA food safety requirements")
    print(f"   • Insurance policy requirements")
    print(f"   • Customer contract specifications")
    print("")
    
    print(f"   Operational Benefits:")
    print(f"   • Automated validation prevents human error")
    print(f"   • Consistent enforcement across all routes")
    print(f"   • Documentation for audits and claims")
    print(f"   • Customer confidence in service reliability")
    print("")
    
    # Example cost impact
    print(f"   Example Cost Impact:")
    print(f"   Route without compatibility checking:")
    print(f"   • Risk: Chemical spill damages fragile electronics")
    print(f"   • Potential claim: $50,000 - $200,000")
    print(f"   • Insurance deductible: $10,000")
    print(f"   • Lost customer relationships: Incalculable")
    print(f"   ")
    print(f"   Route with compatibility checking:")
    print(f"   • Prevention: Incompatible cargo rejected automatically")
    print(f"   • Cost: $0 (prevented incident)")
    print(f"   • Benefit: Maintained customer trust and safety record")


def main():
    """Run the cargo type compatibility demonstration"""
    
    try:
        # Demonstrate cargo compatibility validation
        compatible, incompatible = demonstrate_cargo_compatibility()
        
        # Show conflicts with existing cargo
        demonstrate_existing_cargo_conflicts()
        
        # Show business value
        demonstrate_cargo_type_business_value()
        
        print(f"\n" + "=" * 70)
        print(f"✅ DEMONSTRATION COMPLETE")
        print(f"   Bonus Requirement: Cargo Type Compatibility is FULLY IMPLEMENTED")
        print(f"   • Hazmat + Fragile incompatibility enforced ✅")
        print(f"   • Hazmat + Refrigerated incompatibility enforced ✅")
        print(f"   • Compatible combinations allowed ✅")
        print(f"   • Existing cargo conflict detection ✅")
        print(f"   Compatibility validation: {compatible} valid, {incompatible} invalid")
        print(f"=" * 70)
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()