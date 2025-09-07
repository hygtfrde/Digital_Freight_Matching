#!/usr/bin/env python3
"""
Demo: Business Requirement 4 - Cost Integration

Demonstrates:
- All costs per mile are given by a spreadsheet that's updated by Mr. Lightyear
- Integration of cost calculations in route optimization
- Profitability analysis using business cost structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from order_processor import OrderProcessor, OrderProcessingConstants
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


def demonstrate_cost_structure():
    """Demonstrate the integrated cost structure from business requirements"""
    
    print("💰 BUSINESS REQUIREMENT 4: COST INTEGRATION")
    print("=" * 70)
    print("Requirement: All costs per mile are given by a spreadsheet")
    print("that's updated by Mr. Lightyear")
    print("=" * 70)
    
    # Initialize constants
    constants = OrderProcessingConstants()
    
    print(f"\n📊 INTEGRATED COST STRUCTURE (per mile):")
    print(f"   Trucker cost: ${constants.TRUCKER_COST_PER_MILE:.3f}")
    print(f"   Fuel cost: ${constants.FUEL_COST_PER_MILE:.3f}")
    print(f"   Leasing cost: ${constants.LEASING_COST_PER_MILE:.3f}")
    print(f"   Maintenance cost: ${constants.MAINTENANCE_COST_PER_MILE:.3f}")
    print(f"   Insurance cost: ${constants.INSURANCE_COST_PER_MILE:.3f}")
    print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   TOTAL COST: ${constants.TOTAL_COST_PER_MILE:.6f} per mile")
    
    print(f"\n⚙️  OPERATIONAL PARAMETERS:")
    print(f"   Fuel efficiency: {constants.MILES_PER_GALLON:.1f} miles per gallon")
    print(f"   Gas price: ${constants.GAS_PRICE:.2f} per gallon")
    print(f"   Average speed: {constants.AVG_SPEED_MPH:.0f} mph")
    print(f"   Calculated fuel cost: ${constants.GAS_PRICE / constants.MILES_PER_GALLON:.3f} per mile")
    print(f"   (Matches fuel cost: {abs(constants.FUEL_COST_PER_MILE - constants.GAS_PRICE / constants.MILES_PER_GALLON) < 0.01})")
    
    return constants


def demonstrate_cost_calculations():
    """Demonstrate cost calculations for different route scenarios"""
    
    print(f"\n🛣️  ROUTE COST CALCULATIONS:")
    print("")
    
    constants = OrderProcessingConstants()
    
    # Business requirement routes with actual distances
    routes = [
        ("Atlanta → Ringgold", 202),     # Business requirement
        ("Atlanta → Augusta", 189.2),    # Business requirement  
        ("Atlanta → Savannah", 496),     # Business requirement
        ("Atlanta → Albany", 364),       # Business requirement
        ("Atlanta → Columbus", 214),     # Business requirement
    ]
    
    total_daily_cost = 0.0
    
    for route_name, distance_miles in routes:
        route_cost = distance_miles * constants.TOTAL_COST_PER_MILE
        total_daily_cost += route_cost
        
        print(f"   {route_name}:")
        print(f"     Distance: {distance_miles:.1f} miles ({distance_miles * constants.MILES_TO_KM:.1f} km)")
        print(f"     Total cost: ${route_cost:.2f}")
        
        # Breakdown by cost component
        trucker_cost = distance_miles * constants.TRUCKER_COST_PER_MILE
        fuel_cost = distance_miles * constants.FUEL_COST_PER_MILE
        leasing_cost = distance_miles * constants.LEASING_COST_PER_MILE
        maintenance_cost = distance_miles * constants.MAINTENANCE_COST_PER_MILE
        insurance_cost = distance_miles * constants.INSURANCE_COST_PER_MILE
        
        print(f"       Trucker: ${trucker_cost:.2f}, Fuel: ${fuel_cost:.2f}")
        print(f"       Leasing: ${leasing_cost:.2f}, Maint: ${maintenance_cost:.2f}, Insurance: ${insurance_cost:.2f}")
        print("")
    
    print(f"📈 TOTAL SYSTEM COST ANALYSIS:")
    print(f"   Total daily operational cost: ${total_daily_cost:.2f}")
    print(f"   Original daily loss (business req): -$388.15")
    print(f"   Implied revenue shortfall: ${total_daily_cost + 388.15:.2f}")
    print(f"   Cost represents: {total_daily_cost / (total_daily_cost + 388.15) * 100:.1f}% of needed revenue")


def demonstrate_profitability_integration():
    """Demonstrate how costs integrate with profitability calculations"""
    
    print(f"\n💡 PROFITABILITY INTEGRATION DEMONSTRATION:")
    print("")
    
    constants = OrderProcessingConstants()
    processor = OrderProcessor()
    
    # Create sample route and order for cost analysis
    atlanta = Location(id=1, lat=33.7490, lng=-84.3880)
    augusta = Location(id=2, lat=33.4735, lng=-82.0105)
    
    route = Route(
        id=1,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=atlanta,
        location_destiny=augusta,
        profitability=-50.12,  # Business requirement: original loss
        orders=[]
    )
    
    truck = Truck(
        id=1,
        capacity=48.0,
        autonomy=800.0,
        type="standard",
        cargo_loads=[]
    )
    
    # Create profitable additional order
    atlanta_near = Location(id=3, lat=33.7500, lng=-84.3890)
    augusta_near = Location(id=4, lat=33.4745, lng=-82.0115)
    
    cargo = Cargo(id=1, order_id=1, packages=[
        Package(id=1, volume=20.0, weight=1000.0, type=CargoType.STANDARD, cargo_id=1)
    ])
    
    order = Order(
        id=1,
        location_origin_id=3,
        location_destiny_id=4,
        location_origin=atlanta_near,
        location_destiny=augusta_near,
        cargo=[cargo]
    )
    
    print(f"   Route Analysis: Atlanta → Augusta")
    print(f"   Base distance: {route.base_distance():.1f} km ({route.base_distance() * constants.KM_TO_MILES:.1f} miles)")
    print(f"   Current profitability: ${route.profitability:.2f}")
    
    # Validate order and get metrics
    result = processor.validate_order_for_route(order, route, truck)
    
    print(f"\n   Adding Third-Party Order:")
    print(f"   Order volume: {order.total_volume():.1f} m³")
    print(f"   Order weight: {order.total_weight():.1f} kg")
    print(f"   Validation result: {'✅ Valid' if result.is_valid else '❌ Invalid'}")
    
    if result.is_valid:
        metrics = result.metrics
        
        additional_cost = metrics.get('additional_cost_usd', 0.0)
        deviation_miles = metrics.get('deviation_distance_miles', 0.0)
        
        print(f"   Additional cost: ${additional_cost:.2f}")
        print(f"   Deviation distance: {deviation_miles:.1f} miles")
        
        # Estimate revenue for this order
        base_rate = 200.0  # Example rate
        distance_rate = order.total_distance() * constants.KM_TO_MILES * 2.0  # $2 per mile
        volume_rate = order.total_volume() * 25.0  # $25 per m³
        weight_rate = order.total_weight() * 0.10   # $0.10 per kg
        
        estimated_revenue = base_rate + distance_rate + volume_rate + weight_rate
        net_profit = estimated_revenue - additional_cost
        
        print(f"\n   Revenue Estimation:")
        print(f"     Base rate: ${base_rate:.2f}")
        print(f"     Distance rate: ${distance_rate:.2f}")
        print(f"     Volume rate: ${volume_rate:.2f}")
        print(f"     Weight rate: ${weight_rate:.2f}")
        print(f"     Total revenue: ${estimated_revenue:.2f}")
        print(f"     Net profit: ${net_profit:.2f}")
        
        # Route improvement calculation
        improved_profitability = route.profitability + net_profit
        
        print(f"\n   Route Improvement:")
        print(f"     Original loss: ${route.profitability:.2f}")
        print(f"     Additional profit: ${net_profit:.2f}")
        print(f"     Improved profitability: ${improved_profitability:.2f}")
        
        if improved_profitability > 0:
            print(f"     ✅ Route becomes PROFITABLE!")
        elif improved_profitability > route.profitability:
            print(f"     📈 Route loss REDUCED by ${net_profit:.2f}")
        else:
            print(f"     📉 Order not economically viable")


def demonstrate_cost_sensitivity():
    """Demonstrate cost sensitivity to parameter changes"""
    
    print(f"\n📊 COST SENSITIVITY ANALYSIS:")
    print(f"   How cost changes affect profitability calculations")
    print("")
    
    constants = OrderProcessingConstants()
    base_distance = 200.0  # miles
    base_cost = base_distance * constants.TOTAL_COST_PER_MILE
    
    print(f"   Base scenario: 200-mile route")
    print(f"   Base cost: ${base_cost:.2f}")
    print("")
    
    # Fuel price sensitivity
    fuel_scenarios = [
        ("Current", constants.GAS_PRICE),
        ("10% increase", constants.GAS_PRICE * 1.1),
        ("20% increase", constants.GAS_PRICE * 1.2),
        ("30% increase", constants.GAS_PRICE * 1.3),
    ]
    
    print(f"   Fuel Price Sensitivity:")
    for scenario_name, gas_price in fuel_scenarios:
        fuel_cost_per_mile = gas_price / constants.MILES_PER_GALLON
        total_cost_per_mile = (constants.TOTAL_COST_PER_MILE - constants.FUEL_COST_PER_MILE + fuel_cost_per_mile)
        scenario_cost = base_distance * total_cost_per_mile
        cost_increase = scenario_cost - base_cost
        
        print(f"     {scenario_name}: ${gas_price:.2f}/gal → ${scenario_cost:.2f} total (+${cost_increase:.2f})")
    
    print("")
    
    # Distance sensitivity  
    print(f"   Distance Sensitivity:")
    distances = [100, 150, 200, 300, 500]
    
    for distance in distances:
        route_cost = distance * constants.TOTAL_COST_PER_MILE
        cost_per_km = route_cost / (distance * constants.MILES_TO_KM)
        
        print(f"     {distance} miles: ${route_cost:.2f} (${cost_per_km:.2f}/km)")


def main():
    """Run the cost integration demonstration"""
    
    try:
        # Show integrated cost structure
        constants = demonstrate_cost_structure()
        
        # Demonstrate route cost calculations
        demonstrate_cost_calculations()
        
        # Show profitability integration
        demonstrate_profitability_integration()
        
        # Show cost sensitivity
        demonstrate_cost_sensitivity()
        
        print(f"\n" + "=" * 70)
        print(f"✅ DEMONSTRATION COMPLETE")
        print(f"   Business Requirement 4 is FULLY IMPLEMENTED")
        print(f"   • Cost structure integrated from business spreadsheet")
        print(f"   • All cost components tracked per mile")
        print(f"   • Profitability calculations use accurate costs")
        print(f"   • System ready for cost updates from Mr. Lightyear")
        print(f"=" * 70)
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()