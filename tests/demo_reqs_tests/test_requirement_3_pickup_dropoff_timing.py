#!/usr/bin/env python3
"""
Test: Business Requirement 3 - Pickup/Dropoff Timing

Tests:
- Every pickup and dropoff takes 15 minutes
- Plus deviation from the route (up to 1km from any preexisting point)
- Time calculations including stops and deviations
"""

import pytest
import sys
import os
import random

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from order_processor import OrderProcessor, ValidationResult
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType
from app.database import engine, get_session, Route as DBRoute, Location as DBLocation, Truck as DBTruck
from sqlmodel import Session, select


class TestPickupDropoffTimingRequirement:
    """Test suite for pickup/dropoff timing requirement"""
    
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
    def db_data(self, db_session):
        """Fetch random data from database"""
        # Get random route
        routes = db_session.exec(select(DBRoute)).all()
        if not routes:
            pytest.skip("No routes in database")
        route_data = random.choice(routes)
        
        # Get route locations
        origin_location = db_session.get(DBLocation, route_data.location_origin_id)
        destiny_location = db_session.get(DBLocation, route_data.location_destiny_id)
        
        # Get random truck
        trucks = db_session.exec(select(DBTruck)).all()
        if not trucks:
            pytest.skip("No trucks in database")
        truck_data = random.choice(trucks)
        
        # Get additional random locations for testing
        all_locations = db_session.exec(select(DBLocation)).all()
        test_locations = random.sample(all_locations, min(4, len(all_locations)))
        
        return {
            'route_data': route_data,
            'origin_location': origin_location,
            'destiny_location': destiny_location,
            'truck_data': truck_data,
            'test_locations': test_locations
        }
    
    def create_schema_objects(self, db_data):
        """Convert DB objects to schema objects"""
        route = Route(
            id=db_data['route_data'].id,
            location_origin_id=db_data['route_data'].location_origin_id,
            location_destiny_id=db_data['route_data'].location_destiny_id,
            location_origin=Location(
                id=db_data['origin_location'].id,
                lat=db_data['origin_location'].lat,
                lng=db_data['origin_location'].lng
            ),
            location_destiny=Location(
                id=db_data['destiny_location'].id,
                lat=db_data['destiny_location'].lat,
                lng=db_data['destiny_location'].lng
            ),
            profitability=db_data['route_data'].profitability or -50.0,
            truck_id=db_data['route_data'].truck_id,
            orders=[]
        )
        
        truck = Truck(
            id=db_data['truck_data'].id,
            capacity=db_data['truck_data'].capacity,
            autonomy=db_data['truck_data'].autonomy,
            type=db_data['truck_data'].type,
            cargo_loads=[]
        )
        
        return route, truck
    
    def test_timing_calculations_with_db_data(self, processor, db_data):
        """Test timing calculations using real database data"""
        print(f"\n⏱️  TESTING REQUIREMENT 3: PICKUP/DROPOFF TIMING")
        print(f"=" * 70)
        
        route, truck = self.create_schema_objects(db_data)
        
        print(f"\nINPUT DATA FROM DATABASE:")
        print(f"  Route ID: {route.id}")
        print(f"  Route: ({route.location_origin.lat:.6f}, {route.location_origin.lng:.6f}) → ({route.location_destiny.lat:.6f}, {route.location_destiny.lng:.6f})")
        print(f"  Base Distance: {route.base_distance():.2f} km")
        print(f"  Base Driving Time: {route.base_distance() / 80.0:.2f} hours (at 80 km/h)")
        print(f"  Truck ID: {truck.id}")
        
        print(f"\nTIMING CONSTANTS:")
        print(f"  Stop time per pickup/dropoff: {processor.constants.STOP_TIME_MINUTES} minutes")
        print(f"  Maximum route deviation: {processor.constants.MAX_PROXIMITY_KM} km")
        print(f"  Maximum total route time: 10 hours")
        
        # Test different numbers of orders to see timing impact
        order_counts = [1, 3, 5, 8]
        
        for order_count in order_counts:
            print(f"\n  Testing with {order_count} order(s):")
            
            # Create test orders using random locations
            orders = []
            for i in range(order_count):
                test_location = random.choice(db_data['test_locations'])
                
                cargo = Cargo(id=i+1, order_id=i+1, packages=[
                    Package(id=i+1, volume=5.0, weight=100.0, type=CargoType.STANDARD, cargo_id=i+1)
                ])
                
                order = Order(
                    id=i+1,
                    location_origin_id=test_location.id,
                    location_destiny_id=route.location_destiny_id,
                    location_origin=Location(
                        id=test_location.id,
                        lat=test_location.lat,
                        lng=test_location.lng
                    ),
                    location_destiny=route.location_destiny,
                    cargo=[cargo]
                )
                orders.append(order)
            
            # Add orders to route for timing calculation
            route.orders = orders
            
            # Calculate timing components
            base_driving_time = route.base_distance() / 80.0  # hours
            stop_time = len(orders) * 2 * (processor.constants.STOP_TIME_MINUTES / 60.0)  # 2 stops per order
            return_time = route.base_distance() / 80.0  # return journey
            
            total_time = base_driving_time + stop_time + return_time
            
            print(f"    Orders: {len(orders)}")
            print(f"    Base driving (one-way): {base_driving_time:.2f}h")
            print(f"    Stop time: {stop_time:.2f}h ({len(orders)} orders × 2 stops × 15min)")
            print(f"    Return driving: {return_time:.2f}h")
            print(f"    Total time: {total_time:.2f}h")
            print(f"    Within 10h limit: {'✅ YES' if total_time <= 10.0 else '❌ NO'}")
            
            # Test individual order validation
            if orders:
                sample_order = orders[0]
                result = processor.validate_order_for_route(sample_order, route, truck)
                
                # Calculate deviation for this specific order
                pickup_deviation = processor._calculate_distance_to_route(
                    sample_order.location_origin, route
                )
                dropoff_deviation = processor._calculate_distance_to_route(
                    sample_order.location_destiny, route
                )
                
                print(f"    Sample order deviation:")
                print(f"      Pickup deviation: {pickup_deviation:.3f} km")
                print(f"      Dropoff deviation: {dropoff_deviation:.3f} km")
                print(f"      Validation: {'✅ PASS' if result.is_valid else '❌ FAIL'}")
                
                if not result.is_valid:
                    print(f"      Errors: {result.errors}")
        
        print(f"\n✅ TIMING CALCULATIONS TEST COMPLETED")
    
    def test_deviation_time_impact(self, processor, db_data):
        """Test how route deviations impact timing"""
        print(f"\n🛣️  TESTING DEVIATION TIME IMPACT")
        print(f"=" * 50)
        
        route, truck = self.create_schema_objects(db_data)
        
        # Create orders with different deviation distances
        deviation_tests = [
            ("On-route pickup", route.location_origin, 0.0),
            ("Small deviation", Location(
                id=901, 
                lat=route.location_origin.lat + 0.005,  # ~0.5km
                lng=route.location_origin.lng
            ), 0.5),
            ("Max deviation", Location(
                id=902, 
                lat=route.location_origin.lat + 0.009,  # ~1km
                lng=route.location_origin.lng
            ), 1.0),
        ]
        
        for test_name, pickup_location, expected_deviation in deviation_tests:
            print(f"\n  {test_name}:")
            
            cargo = Cargo(id=900, order_id=900, packages=[
                Package(id=900, volume=3.0, weight=50.0, type=CargoType.STANDARD, cargo_id=900)
            ])
            
            order = Order(
                id=900,
                location_origin_id=pickup_location.id,
                location_destiny_id=route.location_destiny_id,
                location_origin=pickup_location,
                location_destiny=route.location_destiny,
                cargo=[cargo]
            )
            
            # Calculate actual deviation
            actual_deviation = processor._calculate_distance_to_route(pickup_location, route)
            
            print(f"    Expected deviation: ~{expected_deviation:.1f} km")
            print(f"    Actual deviation: {actual_deviation:.3f} km")
            print(f"    Stop time: {processor.constants.STOP_TIME_MINUTES} min (pickup + dropoff)")
            
            # The deviation adds travel time (deviation distance / speed)
            deviation_time_hours = (actual_deviation / 80.0) * 2  # There and back
            print(f"    Deviation time: {deviation_time_hours * 60:.1f} minutes")
            
            result = processor.validate_order_for_route(order, route, truck)
            print(f"    Validation: {'✅ PASS' if result.is_valid else '❌ FAIL'}")
            
            if not result.is_valid:
                timing_error = any("time" in error.lower() or "hour" in error.lower() 
                               for error in result.errors)
                if timing_error:
                    print(f"    ⏰ Time constraint correctly enforced")
        
        print(f"\n✅ DEVIATION TIME IMPACT TEST COMPLETED")
    
    def test_ten_hour_limit_enforcement(self, processor, db_data):
        """Test the 10-hour daily limit enforcement"""
        print(f"\n🕙 TESTING 10-HOUR LIMIT ENFORCEMENT")
        print(f"=" * 50)
        
        route, truck = self.create_schema_objects(db_data)
        
        # Find a long route or create scenario that approaches 10 hours
        base_time = route.base_distance() / 80.0  # one-way driving time
        return_time = base_time  # return journey
        available_time_for_stops = 10.0 - (base_time + return_time)
        
        print(f"  Route timing analysis:")
        print(f"    Base driving time (one-way): {base_time:.2f}h")
        print(f"    Return driving time: {return_time:.2f}h")
        print(f"    Total driving time: {base_time + return_time:.2f}h")
        print(f"    Available time for stops: {available_time_for_stops:.2f}h")
        
        # Calculate max orders that fit in available time
        stop_time_per_order = 2 * (processor.constants.STOP_TIME_MINUTES / 60.0)  # 2 stops × 15min
        max_orders_by_time = int(available_time_for_stops / stop_time_per_order)
        
        print(f"    Time per order (2×15min stops): {stop_time_per_order:.2f}h")
        print(f"    Max orders by time limit: {max_orders_by_time}")
        
        # Test with orders at the limit and beyond
        test_order_counts = [
            max_orders_by_time,
            max_orders_by_time + 1,
            max_orders_by_time + 3
        ]
        
        for order_count in test_order_counts:
            if order_count < 0:
                continue
                
            print(f"\n  Testing {order_count} orders:")
            
            # Create orders
            orders = []
            for i in range(order_count):
                cargo = Cargo(id=i+800, order_id=i+800, packages=[
                    Package(id=i+800, volume=2.0, weight=30.0, type=CargoType.STANDARD, cargo_id=i+800)
                ])
                
                order = Order(
                    id=i+800,
                    location_origin_id=route.location_origin_id,
                    location_destiny_id=route.location_destiny_id,
                    location_origin=route.location_origin,
                    location_destiny=route.location_destiny,
                    cargo=[cargo]
                )
                orders.append(order)
            
            # Calculate total time with these orders
            stop_time = len(orders) * stop_time_per_order
            total_time = (base_time + return_time) + stop_time
            
            print(f"    Stop time: {stop_time:.2f}h")
            print(f"    Total time: {total_time:.2f}h")
            print(f"    Within 10h limit: {'✅ YES' if total_time <= 10.0 else '❌ NO'}")
            
            # Test validation (use first order as sample)
            if orders:
                route.orders = orders[:order_count-1] if order_count > 0 else []  # Existing orders
                sample_order = orders[-1] if orders else None  # New order to add
                
                if sample_order:
                    result = processor.validate_order_for_route(sample_order, route, truck)
                    print(f"    Adding order #{order_count}: {'✅ ACCEPTED' if result.is_valid else '❌ REJECTED'}")
                    
                    if not result.is_valid and total_time > 10.0:
                        print(f"    ⏰ 10-hour limit correctly enforced")
        
        print(f"\n✅ 10-HOUR LIMIT TEST COMPLETED")


if __name__ == "__main__":
    # Run the test directly for debugging
    test_instance = TestPickupDropoffTimingRequirement()
    
    # Create fixtures manually for direct run
    from app.database import get_session
    with get_session() as session:
        from sqlmodel import select
        routes = session.exec(select(DBRoute)).all()
        locations = session.exec(select(DBLocation)).all()
        trucks = session.exec(select(DBTruck)).all()
        
        if routes and locations and trucks:
            route_data = random.choice(routes)
            origin_location = session.get(DBLocation, route_data.location_origin_id)
            destiny_location = session.get(DBLocation, route_data.location_destiny_id)
            truck_data = random.choice(trucks)
            test_locations = random.sample(locations, min(4, len(locations)))
            
            db_data = {
                'route_data': route_data,
                'origin_location': origin_location,
                'destiny_location': destiny_location,
                'truck_data': truck_data,
                'test_locations': test_locations
            }
            
            processor = OrderProcessor()
            test_instance.test_timing_calculations_with_db_data(processor, db_data)
            test_instance.test_deviation_time_impact(processor, db_data)
            test_instance.test_ten_hour_limit_enforcement(processor, db_data)
        else:
            print("❌ No data available in database for testing")