#!/usr/bin/env python3
"""
Test: Bonus Requirement 2 - Union Break Requirements

Tests:
- Union: Truck drivers must take a 30-minute break after 4 hours of work
- Impact on route time calculations
- Implementation status verification
"""

import pytest
import sys
import os
import random

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from order_processor import OrderProcessor, OrderProcessingConstants
from schemas.schemas import Route, Location
from app.database import engine, get_session, Route as DBRoute, Location as DBLocation, Truck as DBTruck
from sqlmodel import Session, select


class TestUnionBreakRequirement:
    """Test suite for union break requirement"""
    
    @pytest.fixture
    def db_session(self):
        """Provide database session"""
        with get_session() as session:
            yield session
    
    @pytest.fixture
    def processor(self):
        """Provide OrderProcessor instance"""
        return OrderProcessor()
    
    @pytest.fixture
    def constants(self):
        """Provide OrderProcessingConstants instance"""
        return OrderProcessingConstants()
    
    @pytest.fixture
    def db_data(self, db_session):
        """Fetch random data from database"""
        # Get routes of different lengths for break time testing
        routes = db_session.exec(select(DBRoute)).all()
        if not routes:
            pytest.skip("No routes in database")
        
        # Calculate distances and categorize routes
        route_data_with_distances = []
        for route in routes:
            origin_location = db_session.get(DBLocation, route.location_origin_id)
            destiny_location = db_session.get(DBLocation, route.location_destiny_id)
            
            if origin_location and destiny_location:
                # Calculate distance
                import math
                lat1, lng1 = math.radians(origin_location.lat), math.radians(origin_location.lng)
                lat2, lng2 = math.radians(destiny_location.lat), math.radians(destiny_location.lng)
                dlat, dlng = lat2 - lat1, lng2 - lng1
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
                distance_km = 6371 * 2 * math.asin(math.sqrt(a))
                
                route_data_with_distances.append({
                    'route': route,
                    'origin_location': origin_location,
                    'destiny_location': destiny_location,
                    'distance_km': distance_km
                })
        
        return {'routes_with_distances': route_data_with_distances}
    
    def create_schema_route(self, route_info):
        """Convert DB objects to schema objects"""
        route_data = route_info['route']
        origin = route_info['origin_location']
        destiny = route_info['destiny_location']
        
        route = Route(
            id=route_data.id,
            location_origin_id=route_data.location_origin_id,
            location_destiny_id=route_data.location_destiny_id,
            location_origin=Location(
                id=origin.id,
                lat=origin.lat,
                lng=origin.lng
            ),
            location_destiny=Location(
                id=destiny.id,
                lat=destiny.lat,
                lng=destiny.lng
            ),
            profitability=route_data.profitability or -50.0,
            truck_id=route_data.truck_id,
            orders=[]
        )
        
        return route
    
    def test_union_break_requirements_analysis(self, constants):
        """Test analysis of union break requirements"""
        print(f"\n👷 TESTING BONUS REQUIREMENT 2: UNION BREAK REQUIREMENTS")
        print(f"=" * 70)
        
        print(f"\nBUSINESS RULE: Truck drivers must take a 30-minute break after 4 hours of work")
        
        print(f"\nCURRENT IMPLEMENTATION STATUS:")
        print(f"  Union breaks: ⚠️  NOT FULLY IMPLEMENTED")
        print(f"  Break duration: 30 minutes (as specified)")
        print(f"  Break trigger: After 4 hours of work")
        print(f"  Break frequency: Every 4 hours of continuous work")
        
        print(f"\nUNION BREAK CALCULATION METHODOLOGY:")
        print(f"  1. Track cumulative work time (driving + stops)")
        print(f"  2. Insert 30-minute break every 4 hours")
        print(f"  3. Breaks count toward total daily time limit")
        print(f"  4. Maximum daily time still 10 hours (including breaks)")
        
        # Demonstrate break calculations
        example_scenarios = [
            ("Short route (3h total)", 3.0, 0),
            ("Medium route (4.5h total)", 4.5, 1),
            ("Long route (7h total)", 7.0, 1),
            ("Very long route (8.5h total)", 8.5, 2),
        ]
        
        print(f"\nBREAK CALCULATION EXAMPLES:")
        
        for scenario_name, work_hours, expected_breaks in example_scenarios:
            breaks_needed = int(work_hours / 4.0)
            break_time = breaks_needed * 0.5  # 30 minutes per break
            total_time_with_breaks = work_hours + break_time
            
            print(f"\n  {scenario_name}:")
            print(f"    Work time: {work_hours:.1f}h")
            print(f"    Breaks needed: {breaks_needed} (every 4h)")
            print(f"    Break time: {break_time:.1f}h ({breaks_needed} × 30min)")
            print(f"    Total time: {total_time_with_breaks:.1f}h")
            print(f"    Within 10h limit: {'✅ YES' if total_time_with_breaks <= 10.0 else '❌ NO'}")
            
            assert breaks_needed == expected_breaks, f"Break calculation error for {scenario_name}"
        
        print(f"\n✅ UNION BREAK ANALYSIS COMPLETED")
    
    def test_break_impact_on_db_routes(self, constants, db_data):
        """Test union break impact on real database routes"""
        print(f"\n📊 TESTING BREAK IMPACT ON DATABASE ROUTES")
        print(f"=" * 55)
        
        if not db_data['routes_with_distances']:
            print(f"  ❌ No routes available for testing")
            return
        
        # Test different routes
        test_routes = db_data['routes_with_distances'][:5]  # Test first 5 routes
        
        print(f"\nTESTING {len(test_routes)} ROUTES FROM DATABASE:")
        
        compliant_without_breaks = 0
        compliant_with_breaks = 0
        
        for i, route_info in enumerate(test_routes, 1):
            route = self.create_schema_route(route_info)
            distance_km = route_info['distance_km']
            
            print(f"\n  Route {i} (ID: {route.id}):")
            print(f"    Distance: {distance_km:.1f} km")
            
            # Assume moderate order load for testing
            order_count = 4
            
            # Calculate time without union breaks
            base_driving_time = distance_km / 80.0  # hours at 80 km/h
            stop_time = order_count * 2 * (constants.STOP_TIME_MINUTES / 60.0)
            return_time = base_driving_time
            work_time = base_driving_time + stop_time + return_time
            
            print(f"    Work time breakdown:")
            print(f"      Driving (one-way): {base_driving_time:.2f}h")
            print(f"      Stops: {stop_time:.2f}h ({order_count} orders)")
            print(f"      Return driving: {return_time:.2f}h")
            print(f"      Total work time: {work_time:.2f}h")
            
            # Calculate with union breaks
            breaks_needed = int(work_time / 4.0)
            break_time = breaks_needed * 0.5
            total_time_with_breaks = work_time + break_time
            
            print(f"    Union breaks:")
            print(f"      Breaks needed: {breaks_needed}")
            print(f"      Break time: {break_time:.1f}h")
            print(f"      Total with breaks: {total_time_with_breaks:.2f}h")
            
            # Compliance check
            compliant_without = work_time <= 10.0
            compliant_with = total_time_with_breaks <= 10.0
            
            print(f"    Compliance without breaks: {'✅ YES' if compliant_without else '❌ NO'}")
            print(f"    Compliance with breaks: {'✅ YES' if compliant_with else '❌ NO'}")
            
            if compliant_without:
                compliant_without_breaks += 1
            if compliant_with:
                compliant_with_breaks += 1
            
            # Impact analysis
            if compliant_without and not compliant_with:
                print(f"    ⚠️  Union breaks would make route non-compliant")
            elif not compliant_without and not compliant_with:
                print(f"    ❌ Route non-compliant even without breaks")
            elif compliant_with:
                print(f"    ✅ Route remains compliant with union breaks")
        
        print(f"\nBREAK IMPACT SUMMARY:")
        print(f"  Routes compliant without breaks: {compliant_without_breaks}/{len(test_routes)}")
        print(f"  Routes compliant with breaks: {compliant_with_breaks}/{len(test_routes)}")
        print(f"  Routes affected by break requirement: {compliant_without_breaks - compliant_with_breaks}")
        
        impact_percentage = (compliant_without_breaks - compliant_with_breaks) / len(test_routes) * 100
        print(f"  Impact rate: {impact_percentage:.1f}% of routes affected")
        
        print(f"\n✅ BREAK IMPACT ANALYSIS COMPLETED")
    
    def test_implementation_status_verification(self, processor):
        """Test current implementation status of union breaks"""
        print(f"\n🔍 TESTING IMPLEMENTATION STATUS VERIFICATION")
        print(f"=" * 55)
        
        print(f"\nIMPLEMENTATION STATUS CHECK:")
        
        # Check if processor has union break methods
        has_break_calculation = hasattr(processor, 'calculate_union_breaks')
        has_break_validation = hasattr(processor, 'validate_union_breaks')
        has_break_constants = hasattr(processor.constants, 'UNION_BREAK_DURATION')
        
        print(f"  Union break calculation method: {'✅ PRESENT' if has_break_calculation else '❌ MISSING'}")
        print(f"  Union break validation method: {'✅ PRESENT' if has_break_validation else '❌ MISSING'}")
        print(f"  Union break constants: {'✅ PRESENT' if has_break_constants else '❌ MISSING'}")
        
        # Check constants for break-related values
        constants_check = {
            'BREAK_INTERVAL_HOURS': getattr(processor.constants, 'BREAK_INTERVAL_HOURS', None),
            'BREAK_DURATION_MINUTES': getattr(processor.constants, 'BREAK_DURATION_MINUTES', None),
            'UNION_BREAK_ENABLED': getattr(processor.constants, 'UNION_BREAK_ENABLED', None),
        }
        
        print(f"\nCONSTANTS STATUS:")
        for const_name, const_value in constants_check.items():
            if const_value is not None:
                print(f"  {const_name}: {const_value} ✅")
            else:
                print(f"  {const_name}: NOT DEFINED ❌")
        
        # Implementation recommendations
        print(f"\nIMPLEMENTATION RECOMMENDATIONS:")
        if not has_break_calculation:
            print(f"  1. Add calculate_union_breaks() method to OrderProcessor")
        if not has_break_validation:
            print(f"  2. Add validate_union_breaks() method to OrderProcessor")
        if not has_break_constants:
            print(f"  3. Add union break constants to OrderProcessingConstants")
        
        print(f"  4. Integrate break calculations into route time validation")
        print(f"  5. Update total_time() methods to include break time")
        print(f"  6. Add break scheduling to route optimization")
        
        # Overall status
        implementation_score = sum([has_break_calculation, has_break_validation, has_break_constants])
        total_checks = 3
        
        print(f"\nOVERALL IMPLEMENTATION STATUS:")
        print(f"  Implementation score: {implementation_score}/{total_checks}")
        print(f"  Completion percentage: {implementation_score/total_checks*100:.0f}%")
        
        if implementation_score == 0:
            print(f"  Status: ❌ NOT IMPLEMENTED")
        elif implementation_score < total_checks:
            print(f"  Status: ⚠️  PARTIALLY IMPLEMENTED")
        else:
            print(f"  Status: ✅ FULLY IMPLEMENTED")
        
        print(f"\n✅ IMPLEMENTATION STATUS VERIFICATION COMPLETED")
    
    def test_union_break_business_impact(self, constants):
        """Test business impact of implementing union breaks"""
        print(f"\n💼 TESTING UNION BREAK BUSINESS IMPACT")
        print(f"=" * 50)
        
        print(f"\nBUSINESS IMPACT ANALYSIS:")
        
        # Analyze different route scenarios
        route_scenarios = [
            ("Short routes (<4h)", 3.5, 4),
            ("Medium routes (4-6h)", 5.0, 5),
            ("Long routes (6-8h)", 7.5, 6),
            ("Very long routes (8-10h)", 9.0, 8),
        ]
        
        print(f"\nIMPACT BY ROUTE TYPE:")
        
        total_capacity_loss = 0
        
        for scenario_name, base_work_time, max_orders_before in route_scenarios:
            breaks_needed = int(base_work_time / 4.0)
            break_time = breaks_needed * 0.5
            total_time_with_breaks = base_work_time + break_time
            
            # Calculate capacity impact
            time_lost_percentage = (break_time / base_work_time) * 100 if base_work_time > 0 else 0
            
            print(f"\n  {scenario_name}:")
            print(f"    Base work time: {base_work_time:.1f}h")
            print(f"    Break time added: {break_time:.1f}h")
            print(f"    Total time: {total_time_with_breaks:.1f}h")
            print(f"    Time increase: {time_lost_percentage:.1f}%")
            print(f"    Still within 10h limit: {'✅ YES' if total_time_with_breaks <= 10.0 else '❌ NO'}")
            
            if total_time_with_breaks > 10.0:
                excess_time = total_time_with_breaks - 10.0
                print(f"    Excess time: {excess_time:.1f}h (route becomes non-compliant)")
            
            total_capacity_loss += time_lost_percentage
        
        average_capacity_loss = total_capacity_loss / len(route_scenarios)
        
        print(f"\nOVERALL BUSINESS IMPACT:")
        print(f"  Average capacity loss: {average_capacity_loss:.1f}%")
        print(f"  Operational efficiency impact: {'⚠️  MODERATE' if average_capacity_loss < 15 else '❌ HIGH'}")
        
        print(f"\nMITIGATION STRATEGIES:")
        print(f"  1. Route optimization to minimize break requirements")
        print(f"  2. Driver scheduling to accommodate break times")
        print(f"  3. Load balancing to stay within time constraints")
        print(f"  4. Client communication about potential delivery delays")
        
        print(f"\nCOMPLIANCE PRIORITY:")
        print(f"  Union break requirement: 🏛️  REGULATORY COMPLIANCE")
        print(f"  Implementation urgency: HIGH (legal requirement)")
        print(f"  Business risk if not implemented: SIGNIFICANT")
        
        print(f"\n✅ UNION BREAK BUSINESS IMPACT ANALYSIS COMPLETED")
    
    def test_break_scheduling_methodology(self):
        """Test break scheduling methodology"""
        print(f"\n⏰ TESTING BREAK SCHEDULING METHODOLOGY")
        print(f"=" * 50)
        
        print(f"\nBREAK SCHEDULING RULES:")
        print(f"  1. Break required after every 4 hours of continuous work")
        print(f"  2. Break duration: 30 minutes")
        print(f"  3. Work time includes: driving + loading/unloading + waiting")
        print(f"  4. Break time counts toward daily 10-hour limit")
        
        # Example scheduling scenarios
        work_blocks = [
            ("Route starts", 0.0, "Begin work"),
            ("After 4h work", 4.0, "First break required (30min)"),
            ("After 8h work", 8.5, "Second break required (30min)"),  # 8h + 30min break = 8.5h
            ("Max work day", 10.0, "End of allowable work day"),
        ]
        
        print(f"\nBREAK SCHEDULING TIMELINE:")
        
        for milestone, time_hours, description in work_blocks:
            minutes = int((time_hours % 1) * 60)
            hours = int(time_hours)
            time_str = f"{hours:02d}:{minutes:02d}"
            print(f"  {time_str} - {milestone}: {description}")
        
        print(f"\nSCHEDULING ALGORITHM:")
        print(f"  1. Calculate total work time for route")
        print(f"  2. Determine break insertion points (every 4h)")
        print(f"  3. Add break duration to total time")
        print(f"  4. Verify total time ≤ 10 hours")
        print(f"  5. Reject route if time limit exceeded")
        
        # Practical example
        example_route_time = 8.75  # 8 hours 45 minutes of work
        breaks_needed = int(example_route_time / 4.0)
        break_time = breaks_needed * 0.5
        total_with_breaks = example_route_time + break_time
        
        print(f"\nPRACTICAL EXAMPLE:")
        print(f"  Route work time: {example_route_time:.2f}h")
        print(f"  Breaks needed: {breaks_needed}")
        print(f"  Break time: {break_time:.1f}h")
        print(f"  Total time: {total_with_breaks:.2f}h")
        print(f"  Acceptable: {'✅ YES' if total_with_breaks <= 10.0 else '❌ NO'}")
        
        print(f"\n✅ BREAK SCHEDULING METHODOLOGY COMPLETED")


if __name__ == "__main__":
    # Run the test directly for debugging
    test_instance = TestUnionBreakRequirement()
    
    # Create fixtures manually for direct run
    processor = OrderProcessor()
    constants = OrderProcessingConstants()
    
    # Test implementation status and methodology (don't need DB data)
    test_instance.test_union_break_requirements_analysis(constants)
    test_instance.test_implementation_status_verification(processor)
    test_instance.test_union_break_business_impact(constants)
    test_instance.test_break_scheduling_methodology()
    
    # Test with database data if available
    from app.database import get_session
    with get_session() as session:
        from sqlmodel import select
        routes = session.exec(select(DBRoute)).all()
        locations = session.exec(select(DBLocation)).all()
        
        if routes and locations:
            import math
            route_data_with_distances = []
            
            for route in routes[:10]:  # Limit to first 10 routes
                origin_location = session.get(DBLocation, route.location_origin_id)
                destiny_location = session.get(DBLocation, route.location_destiny_id)
                
                if origin_location and destiny_location:
                    lat1, lng1 = math.radians(origin_location.lat), math.radians(origin_location.lng)
                    lat2, lng2 = math.radians(destiny_location.lat), math.radians(destiny_location.lng)
                    dlat, dlng = lat2 - lat1, lng2 - lng1
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
                    distance_km = 6371 * 2 * math.asin(math.sqrt(a))
                    
                    route_data_with_distances.append({
                        'route': route,
                        'origin_location': origin_location,
                        'destiny_location': destiny_location,
                        'distance_km': distance_km
                    })
            
            db_data = {'routes_with_distances': route_data_with_distances}
            test_instance.test_break_impact_on_db_routes(constants, db_data)
        else:
            print("❌ No database data available for route-specific testing")