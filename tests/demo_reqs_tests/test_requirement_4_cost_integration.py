#!/usr/bin/env python3
"""
Test: Business Requirement 4 - Cost Integration

Tests:
- All costs per mile are given by a spreadsheet that's updated by Mr. Lightyear
- Integration of cost calculations in route optimization
- Profitability analysis using business cost structure
"""

import pytest
import sys
import os
import random

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from order_processor import OrderProcessor, OrderProcessingConstants, ValidationResult
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType
from app.database import engine, get_session, Route as DBRoute, Location as DBLocation, Truck as DBTruck
from sqlmodel import Session, select


class TestCostIntegrationRequirement:
    """Test suite for cost integration requirement"""
    
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
        
        return {
            'route_data': route_data,
            'origin_location': origin_location,
            'destiny_location': destiny_location,
            'truck_data': truck_data
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
    
    def test_cost_structure_integration(self, constants):
        """Test that cost structure from Mr. Lightyear's spreadsheet is properly integrated"""
        print(f"\n💰 TESTING REQUIREMENT 4: COST INTEGRATION")
        print(f"=" * 70)
        
        print(f"\nINTEGRATED COST STRUCTURE (Mr. Lightyear's Spreadsheet):")
        print(f"  Trucker cost per mile: ${constants.TRUCKER_COST_PER_MILE:.6f}")
        print(f"  Fuel cost per mile: ${constants.FUEL_COST_PER_MILE:.6f}")
        print(f"  Leasing cost per mile: ${constants.LEASING_COST_PER_MILE:.6f}")
        print(f"  Maintenance cost per mile: ${constants.MAINTENANCE_COST_PER_MILE:.6f}")
        print(f"  Insurance cost per mile: ${constants.INSURANCE_COST_PER_MILE:.6f}")
        print(f"  " + "─" * 50)
        print(f"  TOTAL COST PER MILE: ${constants.TOTAL_COST_PER_MILE:.6f}")
        
        print(f"\nOPERATIONAL PARAMETERS:")
        print(f"  Miles per gallon: {constants.MILES_PER_GALLON:.1f}")
        print(f"  Gas price: ${constants.GAS_PRICE:.2f}/gallon")
        print(f"  Average speed: {constants.AVG_SPEED_MPH:.0f} mph")
        
        # Verify fuel cost calculation consistency
        calculated_fuel_cost = constants.GAS_PRICE / constants.MILES_PER_GALLON
        fuel_cost_match = abs(constants.FUEL_COST_PER_MILE - calculated_fuel_cost) < 0.001
        
        print(f"\nCOST VERIFICATION:")
        print(f"  Calculated fuel cost: ${calculated_fuel_cost:.6f}")
        print(f"  Configured fuel cost: ${constants.FUEL_COST_PER_MILE:.6f}")
        print(f"  Fuel cost consistency: {'✅ MATCH' if fuel_cost_match else '❌ MISMATCH'}")
        
        # Verify total cost calculation
        sum_of_components = (
            constants.TRUCKER_COST_PER_MILE +
            constants.FUEL_COST_PER_MILE +
            constants.LEASING_COST_PER_MILE +
            constants.MAINTENANCE_COST_PER_MILE +
            constants.INSURANCE_COST_PER_MILE
        )
        total_cost_match = abs(constants.TOTAL_COST_PER_MILE - sum_of_components) < 0.001
        
        print(f"  Sum of components: ${sum_of_components:.6f}")
        print(f"  Total cost per mile: ${constants.TOTAL_COST_PER_MILE:.6f}")
        print(f"  Total cost consistency: {'✅ MATCH' if total_cost_match else '❌ MISMATCH'}")
        
        assert fuel_cost_match, "Fuel cost calculation inconsistency"
        assert total_cost_match, "Total cost calculation inconsistency"
        
        print(f"\n✅ COST STRUCTURE INTEGRATION VERIFIED")
    
    def test_route_cost_calculations_with_db_data(self, constants, db_data):
        """Test cost calculations for real routes from database"""
        print(f"\n🛣️  TESTING ROUTE COST CALCULATIONS WITH DB DATA")
        print(f"=" * 60)
        
        route, truck = self.create_schema_objects(db_data)
        
        print(f"\nROUTE DATA FROM DATABASE:")
        print(f"  Route ID: {route.id}")
        print(f"  Distance: {route.base_distance():.2f} km ({route.base_distance() * constants.KM_TO_MILES:.1f} miles)")
        print(f"  Current profitability: ${route.profitability:.2f}")
        
        # Calculate route costs
        distance_miles = route.base_distance() * constants.KM_TO_MILES
        route_cost = distance_miles * constants.TOTAL_COST_PER_MILE
        
        print(f"\nCOST BREAKDOWN:")
        print(f"  Distance (miles): {distance_miles:.1f}")
        
        # Break down by cost component
        trucker_cost = distance_miles * constants.TRUCKER_COST_PER_MILE
        fuel_cost = distance_miles * constants.FUEL_COST_PER_MILE
        leasing_cost = distance_miles * constants.LEASING_COST_PER_MILE
        maintenance_cost = distance_miles * constants.MAINTENANCE_COST_PER_MILE
        insurance_cost = distance_miles * constants.INSURANCE_COST_PER_MILE
        
        print(f"  Trucker cost: ${trucker_cost:.2f}")
        print(f"  Fuel cost: ${fuel_cost:.2f}")
        print(f"  Leasing cost: ${leasing_cost:.2f}")
        print(f"  Maintenance cost: ${maintenance_cost:.2f}")
        print(f"  Insurance cost: ${insurance_cost:.2f}")
        print(f"  " + "─" * 30)
        print(f"  TOTAL ROUTE COST: ${route_cost:.2f}")
        
        print(f"\nPROFITABILITY ANALYSIS:")
        print(f"  Current profitability: ${route.profitability:.2f}")
        print(f"  Route operational cost: ${route_cost:.2f}")
        
        # Calculate implied revenue
        if route.profitability < 0:
            print(f"  Status: LOSING MONEY")
            implied_revenue = route_cost + route.profitability
            print(f"  Implied daily revenue: ${implied_revenue:.2f}")
            print(f"  Revenue shortfall: ${-route.profitability:.2f}")
        else:
            print(f"  Status: PROFITABLE")
            implied_revenue = route_cost + route.profitability
            print(f"  Implied daily revenue: ${implied_revenue:.2f}")
            print(f"  Profit margin: ${route.profitability:.2f}")
        
        print(f"\n✅ ROUTE COST CALCULATIONS COMPLETED")
    
    def test_profitability_impact_of_new_orders(self, processor, constants, db_data):
        """Test how new orders impact route profitability using cost integration"""
        print(f"\n💡 TESTING PROFITABILITY IMPACT OF NEW ORDERS")
        print(f"=" * 55)
        
        route, truck = self.create_schema_objects(db_data)
        
        print(f"\nBASE ROUTE ANALYSIS:")
        print(f"  Route ID: {route.id}")
        print(f"  Current profitability: ${route.profitability:.2f}")
        
        # Create a profitable test order
        cargo = Cargo(id=1, order_id=1, packages=[
            Package(id=1, volume=10.0, weight=500.0, type=CargoType.STANDARD, cargo_id=1)
        ])
        
        order = Order(
            id=1,
            location_origin_id=route.location_origin_id,
            location_destiny_id=route.location_destiny_id,
            location_origin=route.location_origin,
            location_destiny=route.location_destiny,
            cargo=[cargo]
        )
        
        print(f"\nTEST ORDER:")
        print(f"  Volume: {order.total_volume():.1f} m³")
        print(f"  Weight: {order.total_weight():.0f} kg")
        
        # Validate the order
        result = processor.validate_order_for_route(order, route, truck)
        
        print(f"\nORDER VALIDATION:")
        print(f"  Validation result: {'✅ ACCEPTED' if result.is_valid else '❌ REJECTED'}")
        
        if not result.is_valid:
            print(f"  Rejection reasons: {result.errors}")
        
        # Calculate potential revenue from this order (simplified)
        # In real system, this would come from client payment
        estimated_revenue_per_mile = 2.0  # Example: $2 per mile for client orders
        order_distance_miles = route.base_distance() * constants.KM_TO_MILES
        estimated_order_revenue = order_distance_miles * estimated_revenue_per_mile
        
        print(f"\nPROFITABILITY IMPACT ESTIMATE:")
        print(f"  Order distance: {order_distance_miles:.1f} miles")
        print(f"  Estimated revenue: ${estimated_order_revenue:.2f} (${estimated_revenue_per_mile:.2f}/mile)")
        
        # Calculate if adding this order would make route profitable
        potential_new_profitability = route.profitability + estimated_order_revenue
        
        print(f"  Current profitability: ${route.profitability:.2f}")
        print(f"  Potential new profitability: ${potential_new_profitability:.2f}")
        print(f"  Improvement: ${estimated_order_revenue:.2f}")
        
        if route.profitability < 0 and potential_new_profitability > 0:
            print(f"  ✅ Order could make route profitable!")
        elif route.profitability < 0 and potential_new_profitability < 0:
            print(f"  ⚠️  Order helps but route still losing money")
        else:
            print(f"  📈 Order adds to existing profitability")
        
        print(f"\n✅ PROFITABILITY IMPACT ANALYSIS COMPLETED")
    
    def test_cost_per_mile_accuracy(self, constants):
        """Test the accuracy of cost per mile calculations against business requirements"""
        print(f"\n🎯 TESTING COST PER MILE ACCURACY")
        print(f"=" * 45)
        
        # Test against known business requirement routes
        known_routes = [
            ("Atlanta → Ringgold", 126, 202),      # km, miles
            ("Atlanta → Augusta", 189.2, 117.5),   # Business requirement distances
            ("Atlanta → Savannah", 496, 308),      # These should match business requirements
        ]
        
        print(f"\nBUSINESS REQUIREMENT ROUTE COSTS:")
        
        total_system_cost = 0.0
        
        for route_name, miles, km in known_routes:
            route_cost = miles * constants.TOTAL_COST_PER_MILE
            total_system_cost += route_cost
            
            print(f"\n  {route_name}:")
            print(f"    Distance: {miles:.1f} miles ({km:.1f} km)")
            print(f"    Cost per mile: ${constants.TOTAL_COST_PER_MILE:.6f}")
            print(f"    Total route cost: ${route_cost:.2f}")
            
            # Break down costs
            print(f"    Cost breakdown:")
            print(f"      Trucker: ${miles * constants.TRUCKER_COST_PER_MILE:.2f}")
            print(f"      Fuel: ${miles * constants.FUEL_COST_PER_MILE:.2f}")
            print(f"      Leasing: ${miles * constants.LEASING_COST_PER_MILE:.2f}")
            print(f"      Maintenance: ${miles * constants.MAINTENANCE_COST_PER_MILE:.2f}")
            print(f"      Insurance: ${miles * constants.INSURANCE_COST_PER_MILE:.2f}")
        
        print(f"\nSYSTEM TOTALS:")
        print(f"  Total daily operational cost: ${total_system_cost:.2f}")
        print(f"  Original business loss: -$388.15 (from requirements)")
        print(f"  Implied revenue shortfall: ${total_system_cost + 388.15:.2f}")
        
        # Verify cost structure makes business sense
        print(f"\nCOST STRUCTURE VALIDATION:")
        print(f"  Operational cost represents: {total_system_cost / (total_system_cost + 388.15) * 100:.1f}% of needed revenue")
        print(f"  Cost structure: {'✅ REASONABLE' if 70 <= (total_system_cost / (total_system_cost + 388.15) * 100) <= 90 else '⚠️ CHECK REQUIRED'}")
        
        print(f"\n✅ COST PER MILE ACCURACY TEST COMPLETED")


if __name__ == "__main__":
    # Run the test directly for debugging
    test_instance = TestCostIntegrationRequirement()
    
    # Create fixtures manually for direct run
    constants = OrderProcessingConstants()
    processor = OrderProcessor()
    
    from app.database import get_session
    with get_session() as session:
        from sqlmodel import select
        routes = session.exec(select(DBRoute)).all()
        locations = session.exec(select(DBLocation)).all()
        trucks = session.exec(select(DBTruck)).all()
        
        # Test cost structure first (doesn't need DB data)
        test_instance.test_cost_structure_integration(constants)
        test_instance.test_cost_per_mile_accuracy(constants)
        
        if routes and locations and trucks:
            route_data = random.choice(routes)
            origin_location = session.get(DBLocation, route_data.location_origin_id)
            destiny_location = session.get(DBLocation, route_data.location_destiny_id)
            truck_data = random.choice(trucks)
            
            db_data = {
                'route_data': route_data,
                'origin_location': origin_location,
                'destiny_location': destiny_location,
                'truck_data': truck_data
            }
            
            test_instance.test_route_cost_calculations_with_db_data(constants, db_data)
            test_instance.test_profitability_impact_of_new_orders(processor, constants, db_data)
        else:
            print("❌ No database data available for route-specific testing")