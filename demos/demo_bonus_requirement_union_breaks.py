#!/usr/bin/env python3
"""
Demo: Bonus Requirement - Union Break Requirements

Demonstrates:
- Union: Truck drivers must take a 30-minute break after 4 hours of work
- Impact on route time calculations
- Implementation status (currently NOT IMPLEMENTED)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from order_processor import OrderProcessingConstants
from schemas.schemas import Route, Location


def create_union_break_test_data():
    """Create test data to demonstrate union break requirements"""
    
    # Business requirement locations with known distances
    atlanta = Location(id=1, lat=33.7490, lng=-84.3880)
    savannah = Location(id=2, lat=32.0835, lng=-81.0998)  # 496 miles from Atlanta
    albany = Location(id=3, lat=31.5804, lng=-84.1557)    # 364 miles from Atlanta
    columbus = Location(id=4, lat=32.4609, lng=-84.9877)  # 214 miles from Atlanta
    
    # Create routes with different time characteristics
    routes = [
        # Short route (under 4 hours) - no break needed
        Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=4,
            location_origin=atlanta,
            location_destiny=columbus,
            profitability=-56.69,
            orders=[]
        ),
        
        # Medium route (around 4-5 hours) - one break needed  
        Route(
            id=2,
            location_origin_id=1,
            location_destiny_id=3,
            location_origin=atlanta,
            location_destiny=albany,
            profitability=-96.43,
            orders=[]
        ),
        
        # Long route (over 8 hours) - multiple breaks needed
        Route(
            id=3,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=atlanta,
            location_destiny=savannah,
            profitability=-131.40,
            orders=[]
        )
    ]
    
    return routes


def calculate_current_time_without_breaks(route):
    """Calculate current route time without union breaks"""
    
    constants = OrderProcessingConstants()
    
    # Base distance (one-way)
    distance_km = route.base_distance()
    distance_miles = distance_km * constants.KM_TO_MILES
    
    # Driving time (round trip)
    driving_time_hours = (distance_km * 2) / constants.AVG_SPEED_MPH / constants.MILES_TO_KM
    
    # Stop time (assuming 3 orders per route for demonstration)
    orders_count = 3
    stop_time_hours = orders_count * 2 * (constants.STOP_TIME_MINUTES / 60.0)
    
    total_time = driving_time_hours + stop_time_hours
    
    return {
        'distance_km': distance_km,
        'distance_miles': distance_miles,
        'driving_time': driving_time_hours,
        'stop_time': stop_time_hours,
        'total_time': total_time
    }


def calculate_time_with_union_breaks(route_time_data):
    """Calculate route time including mandatory union breaks"""
    
    driving_time = route_time_data['driving_time']
    stop_time = route_time_data['stop_time']
    base_total = route_time_data['total_time']
    
    # Union rule: 30-minute break after every 4 hours of work
    work_hours = driving_time + stop_time
    break_count = int(work_hours / 4.0)  # Number of 4-hour periods
    
    # Each break is 30 minutes (0.5 hours)
    break_time_hours = break_count * 0.5
    
    # Total time with breaks
    total_with_breaks = base_total + break_time_hours
    
    return {
        'work_hours': work_hours,
        'break_count': break_count,
        'break_time_hours': break_time_hours,
        'total_with_breaks': total_with_breaks,
        'time_increase': break_time_hours
    }


def demonstrate_union_break_impact():
    """Demonstrate impact of union break requirements"""
    
    print("⏰ BONUS REQUIREMENT: UNION BREAK REQUIREMENTS")
    print("=" * 70)
    print("Bonus Requirement: Truck drivers must take a 30-minute break")
    print("after 4 hours of work")
    print("Current Status: NOT IMPLEMENTED")
    print("=" * 70)
    
    # Create test routes
    routes = create_union_break_test_data()
    
    route_names = [
        "Short Route: Atlanta → Columbus (214 miles)",
        "Medium Route: Atlanta → Albany (364 miles)", 
        "Long Route: Atlanta → Savannah (496 miles)"
    ]
    
    print(f"\n📊 UNION BREAK IMPACT ANALYSIS:")
    print(f"   Union Rule: 30-minute break required after every 4 hours of work")
    print(f"   Work includes: driving time + loading/unloading time")
    print("")
    
    total_without_breaks = 0
    total_with_breaks = 0
    
    for i, (route_name, route) in enumerate(zip(route_names, routes)):
        print(f"   {route_name}")
        
        # Calculate current time (without breaks)
        current_time = calculate_current_time_without_breaks(route)
        
        # Calculate time with union breaks
        break_analysis = calculate_time_with_union_breaks(current_time)
        
        print(f"     Current Implementation:")
        print(f"       Round-trip distance: {current_time['distance_km']*2:.0f} km ({current_time['distance_miles']*2:.0f} miles)")
        print(f"       Driving time: {current_time['driving_time']:.1f}h")
        print(f"       Stop time: {current_time['stop_time']:.1f}h (3 orders)")
        print(f"       Total time: {current_time['total_time']:.1f}h")
        
        print(f"     With Union Breaks:")
        print(f"       Work hours: {break_analysis['work_hours']:.1f}h")
        print(f"       Required breaks: {break_analysis['break_count']} × 30min = {break_analysis['break_time_hours']:.1f}h")
        print(f"       Total time: {break_analysis['total_with_breaks']:.1f}h")
        print(f"       Time increase: +{break_analysis['time_increase']:.1f}h ({break_analysis['time_increase']/current_time['total_time']*100:.1f}%)")
        
        # Check 10-hour limit compliance
        within_limit_current = current_time['total_time'] <= 10.0
        within_limit_breaks = break_analysis['total_with_breaks'] <= 10.0
        
        print(f"     10-Hour Limit Compliance:")
        print(f"       Current: {'✅ Compliant' if within_limit_current else '❌ Violation'} ({current_time['total_time']:.1f}h)")
        print(f"       With breaks: {'✅ Compliant' if within_limit_breaks else '❌ Violation'} ({break_analysis['total_with_breaks']:.1f}h)")
        
        total_without_breaks += current_time['total_time']
        total_with_breaks += break_analysis['total_with_breaks']
        
        print("")
    
    print(f"📈 SYSTEM-WIDE IMPACT:")
    print(f"   Total route time without breaks: {total_without_breaks:.1f}h")
    print(f"   Total route time with breaks: {total_with_breaks:.1f}h")
    print(f"   System-wide time increase: +{total_with_breaks - total_without_breaks:.1f}h ({(total_with_breaks - total_without_breaks)/total_without_breaks*100:.1f}%)")


def demonstrate_implementation_requirements():
    """Show what would be needed to implement union breaks"""
    
    print(f"\n🔧 IMPLEMENTATION REQUIREMENTS:")
    print("")
    
    print(f"   Code Changes Needed:")
    print(f"   1. Route time calculation modification:")
    print(f"      • Add break calculation logic")
    print(f"      • Insert breaks every 4 hours of work")
    print(f"      • Account for 30-minute break duration")
    print("")
    
    print(f"   2. OrderProcessor enhancement:")
    print(f"      • Update _validate_time_constraint() method")
    print(f"      • Include break time in route feasibility")
    print(f"      • Adjust 10-hour limit validation")
    print("")
    
    print(f"   3. RouteGenerationService update:")
    print(f"      • Modify _analyze_route_economics() method")
    print(f"      • Include break time in profitability calculations")
    print(f"      • Update cost analysis for longer routes")
    print("")
    
    print(f"   4. Business validation update:")
    print(f"      • Update BusinessValidator time constraints")
    print(f"      • Add union compliance validation")
    print(f"      • Include break requirements in reporting")


def demonstrate_business_impact():
    """Show business impact of implementing union breaks"""
    
    print(f"\n💼 BUSINESS IMPACT ANALYSIS:")
    print("")
    
    print(f"   Compliance Benefits:")
    print(f"   • Legal compliance with union agreements")
    print(f"   • Improved driver satisfaction and retention")
    print(f"   • Reduced fatigue-related safety incidents")
    print(f"   • Better insurance rates due to safety record")
    print("")
    
    print(f"   Operational Challenges:")
    print(f"   • Longer route times reduce daily capacity")
    print(f"   • Some routes may exceed 10-hour limit")
    print(f"   • Higher labor costs per route")
    print(f"   • Need for driver rest facilities")
    print("")
    
    print(f"   Financial Impact (Estimated):")
    routes = create_union_break_test_data()
    
    # Calculate average time increase
    total_increase = 0
    for route in routes:
        current_time = calculate_current_time_without_breaks(route)
        break_analysis = calculate_time_with_union_breaks(current_time)
        total_increase += break_analysis['time_increase']
    
    avg_increase = total_increase / len(routes)
    
    print(f"   • Average time increase per route: {avg_increase:.1f} hours")
    print(f"   • Additional labor cost per route: ${avg_increase * 25:.2f} (at $25/hour)")
    print(f"   • Daily system cost increase: ${avg_increase * 25 * 5:.2f} (5 routes)")
    print(f"   • Annual cost increase: ${avg_increase * 25 * 5 * 365:.2f}")


def demonstrate_current_vs_compliant():
    """Compare current system with union-compliant version"""
    
    print(f"\n⚖️  CURRENT vs UNION-COMPLIANT COMPARISON:")
    print("")
    
    routes = create_union_break_test_data()
    route_names = ["Columbus Route", "Albany Route", "Savannah Route"]
    
    print(f"   {'Route':<15} {'Current':<12} {'Compliant':<12} {'Impact':<15} {'10h Limit'}")
    print(f"   {'-'*15} {'-'*12} {'-'*12} {'-'*15} {'-'*10}")
    
    routes_affected = 0
    routes_over_limit = 0
    
    for route_name, route in zip(route_names, routes):
        current_time = calculate_current_time_without_breaks(route)
        break_analysis = calculate_time_with_union_breaks(current_time)
        
        current_str = f"{current_time['total_time']:.1f}h"
        compliant_str = f"{break_analysis['total_with_breaks']:.1f}h"
        impact_str = f"+{break_analysis['time_increase']:.1f}h"
        
        if break_analysis['total_with_breaks'] > 10.0:
            limit_str = "❌ Over"
            routes_over_limit += 1
        else:
            limit_str = "✅ OK"
        
        if break_analysis['break_count'] > 0:
            routes_affected += 1
            
        print(f"   {route_name:<15} {current_str:<12} {compliant_str:<12} {impact_str:<15} {limit_str}")
    
    print(f"\n   Summary:")
    print(f"   • Routes affected by union breaks: {routes_affected}/{len(routes)}")
    print(f"   • Routes exceeding 10h limit: {routes_over_limit}/{len(routes)}")
    print(f"   • Implementation priority: {'🔴 HIGH' if routes_over_limit > 0 else '🟡 MEDIUM'}")


def main():
    """Run the union break requirements demonstration"""
    
    try:
        # Show impact of union break requirements
        demonstrate_union_break_impact()
        
        # Show implementation requirements
        demonstrate_implementation_requirements()
        
        # Show business impact
        demonstrate_business_impact()
        
        # Compare current vs compliant
        demonstrate_current_vs_compliant()
        
        print(f"\n" + "=" * 70)
        print(f"⚠️  DEMONSTRATION COMPLETE")
        print(f"   Bonus Requirement: Union Break Requirements is NOT IMPLEMENTED")
        print(f"   • Current system does not account for mandatory breaks ❌")
        print(f"   • Route time calculations underestimate actual time ❌")
        print(f"   • Some routes may violate union agreements ❌")
        print(f"   • Implementation would require significant updates ⚠️")
        print(f"   Recommendation: Implement union compliance for legal/safety reasons")
        print(f"=" * 70)
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()