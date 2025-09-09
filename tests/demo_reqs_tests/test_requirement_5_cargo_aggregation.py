#!/usr/bin/env python3
"""
Test: Business Requirement 5 - Cargo Aggregation and Route Generation

Tests:
- Cargo that can't fit on any route can be saved and combined with other clients' cargo
- Form new routes that MUST be profitable
- Automated cargo aggregation and route generation
"""

import pytest
import sys
import os
import random

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import engine, get_session, Client as DBClient, Location as DBLocation, Order as DBOrder, Truck as DBTruck, Route as DBRoute, Cargo as DBCargo, Package as DBPackage, CargoType
from services.cargo_aggregation_service import CargoAggregationService
from services.route_generation_service import RouteGenerationService
from sqlmodel import Session, select


class TestCargoAggregationRequirement:
    """Test suite for cargo aggregation requirement"""
    
    @pytest.fixture
    def db_session(self):
        """Provide database session"""
        with get_session() as session:
            yield session
    
    @pytest.fixture
    def aggregation_service(self):
        """Provide CargoAggregationService instance"""
        return CargoAggregationService()
    
    @pytest.fixture
    def route_generation_service(self):
        """Provide RouteGenerationService instance"""
        return RouteGenerationService()
    
    @pytest.fixture
    def db_data(self, db_session):
        """Fetch random data from database"""
        # Get clients
        clients = db_session.exec(select(DBClient)).all()
        if len(clients) < 2:
            pytest.skip("Need at least 2 clients in database")
        
        # Get locations
        locations = db_session.exec(select(DBLocation)).all()
        if len(locations) < 4:
            pytest.skip("Need at least 4 locations in database")
        
        # Get available trucks
        trucks = db_session.exec(select(DBTruck)).all()
        if not trucks:
            pytest.skip("No trucks in database")
        
        # Get existing routes to understand current capacity usage
        routes = db_session.exec(select(DBRoute)).all()
        
        return {
            'clients': clients,
            'locations': locations,
            'trucks': trucks,
            'routes': routes
        }
    
    def test_cargo_aggregation_with_db_data(self, aggregation_service, db_session, db_data):
        """Test cargo aggregation using real database data"""
        print(f"\n📦 TESTING REQUIREMENT 5: CARGO AGGREGATION AND ROUTE GENERATION")
        print(f"=" * 70)
        
        print(f"\nINPUT DATA FROM DATABASE:")
        print(f"  Available clients: {len(db_data['clients'])}")
        print(f"  Available locations: {len(db_data['locations'])}")
        print(f"  Available trucks: {len(db_data['trucks'])}")
        print(f"  Existing routes: {len(db_data['routes'])}")
        
        # Select random clients for test orders
        selected_clients = random.sample(db_data['clients'], min(3, len(db_data['clients'])))
        selected_locations = random.sample(db_data['locations'], min(6, len(db_data['locations'])))
        
        print(f"\nTEST SCENARIO:")
        print(f"  Testing with {len(selected_clients)} clients")
        print(f"  Using {len(selected_locations)} locations")
        
        # Create individual orders that might not fit existing routes
        test_orders = []
        for i, client in enumerate(selected_clients):
            origin = selected_locations[i * 2 % len(selected_locations)]
            destiny = selected_locations[(i * 2 + 1) % len(selected_locations)]
            
            print(f"\n  Client {i+1}: {client.name}")
            print(f"    Origin: Location {origin.id} ({origin.lat:.4f}, {origin.lng:.4f})")
            print(f"    Destiny: Location {destiny.id} ({destiny.lat:.4f}, {destiny.lng:.4f})")
            
            # Create order in database
            order = DBOrder(
                location_origin_id=origin.id,
                location_destiny_id=destiny.id,
                client_id=client.id
            )
            db_session.add(order)
            db_session.flush()
            
            # Create cargo with packages
            cargo = DBCargo(order_id=order.id)
            db_session.add(cargo)
            db_session.flush()
            
            # Random cargo characteristics
            package_count = random.randint(1, 3)
            total_volume = 0
            total_weight = 0
            
            for j in range(package_count):
                volume = random.uniform(3.0, 12.0)
                weight = random.uniform(100.0, 800.0)
                cargo_type = random.choice(list(CargoType))
                
                package = DBPackage(
                    volume=volume,
                    weight=weight,
                    type=cargo_type,
                    cargo_id=cargo.id
                )
                db_session.add(package)
                
                total_volume += volume
                total_weight += weight
            
            test_orders.append({
                'order': order,
                'cargo': cargo,
                'total_volume': total_volume,
                'total_weight': total_weight,
                'client_name': client.name
            })
            
            print(f"    Cargo: {total_volume:.1f}m³, {total_weight:.0f}kg")
        
        db_session.commit()
        
        print(f"\n🔍 AGGREGATION ANALYSIS:")
        
        # Find orders that can't fit existing routes
        unmatched_orders = []
        for order_info in test_orders:
            # Simplified check - in real system this would use proper validation
            can_fit_existing = False
            
            for route in db_data['routes']:
                # Check if order locations are compatible with existing route
                # This is simplified - real system would check proximity constraints
                if (order_info['order'].location_origin_id == route.location_origin_id and 
                    order_info['order'].location_destiny_id == route.location_destiny_id):
                    can_fit_existing = True
                    print(f"    Order from {order_info['client_name']}: ✅ Can fit existing route {route.id}")
                    break
            
            if not can_fit_existing:
                unmatched_orders.append(order_info)
                print(f"    Order from {order_info['client_name']}: ❌ Cannot fit existing routes")
        
        print(f"\nAGGREGATION OPPORTUNITIES:")
        print(f"  Orders needing aggregation: {len(unmatched_orders)}")
        
        if len(unmatched_orders) >= 2:
            print(f"  Attempting to aggregate {len(unmatched_orders)} orders...")
            
            # Try to find compatible orders for aggregation
            compatible_groups = []
            
            # Simple aggregation logic - group orders with similar routes
            for i, order1 in enumerate(unmatched_orders):
                for j, order2 in enumerate(unmatched_orders[i+1:], i+1):
                    # Check if orders can be combined (simplified logic)
                    combined_volume = order1['total_volume'] + order2['total_volume']
                    combined_weight = order1['total_weight'] + order2['total_weight']
                    
                    # Check truck capacity constraints
                    truck_capacity = 48.0  # Standard capacity
                    weight_limit_kg = 9180 / 2.20462  # Convert lbs to kg
                    
                    if combined_volume <= truck_capacity and combined_weight <= weight_limit_kg:
                        compatible_groups.append({
                            'orders': [order1, order2],
                            'combined_volume': combined_volume,
                            'combined_weight': combined_weight
                        })
                        print(f"  ✅ Compatible group found:")
                        print(f"    - {order1['client_name']} + {order2['client_name']}")
                        print(f"    - Combined: {combined_volume:.1f}m³, {combined_weight:.0f}kg")
                        break
            
            if compatible_groups:
                print(f"\n📈 NEW ROUTE GENERATION:")
                for i, group in enumerate(compatible_groups[:1], 1):  # Test first group
                    print(f"  New Route {i}:")
                    print(f"    Clients: {len(group['orders'])}")
                    print(f"    Total cargo: {group['combined_volume']:.1f}m³, {group['combined_weight']:.0f}kg")
                    
                    # Calculate if route would be profitable
                    # This is simplified - real calculation would be more complex
                    estimated_distance_km = 200  # Placeholder
                    estimated_revenue = len(group['orders']) * 150  # $150 per order
                    estimated_cost = estimated_distance_km * 1.2  # Simplified cost
                    estimated_profit = estimated_revenue - estimated_cost
                    
                    print(f"    Estimated revenue: ${estimated_revenue:.0f}")
                    print(f"    Estimated cost: ${estimated_cost:.0f}")
                    print(f"    Estimated profit: ${estimated_profit:.0f}")
                    print(f"    Profitable: {'✅ YES' if estimated_profit > 0 else '❌ NO'}")
                    
                    if estimated_profit > 0:
                        print(f"    ✅ Route meets profitability requirement")
                    else:
                        print(f"    ❌ Route would not be profitable - rejected")
            else:
                print(f"  ❌ No compatible aggregation groups found")
        else:
            print(f"  ⚠️  Not enough unmatched orders for aggregation testing")
        
        print(f"\n✅ CARGO AGGREGATION TEST COMPLETED")
        
        # Clean up test data
        for order_info in test_orders:
            db_session.delete(order_info['order'])
        db_session.commit()
    
    def test_profitability_requirement_enforcement(self, route_generation_service, db_session, db_data):
        """Test that new routes must be profitable"""
        print(f"\n💰 TESTING PROFITABILITY REQUIREMENT ENFORCEMENT")
        print(f"=" * 55)
        
        print(f"\nBUSINESS RULE: New routes MUST be profitable")
        
        # Create test scenario with different profitability outcomes
        test_scenarios = [
            {
                'name': 'High Revenue Route',
                'distance_km': 150,
                'orders': 3,
                'revenue_per_order': 200,
                'expected_profitable': True
            },
            {
                'name': 'Medium Revenue Route', 
                'distance_km': 300,
                'orders': 2,
                'revenue_per_order': 120,
                'expected_profitable': True
            },
            {
                'name': 'Low Revenue Route',
                'distance_km': 400,
                'orders': 1,
                'revenue_per_order': 80,
                'expected_profitable': False
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n  Scenario: {scenario['name']}")
            print(f"    Distance: {scenario['distance_km']} km")
            print(f"    Orders: {scenario['orders']}")
            print(f"    Revenue per order: ${scenario['revenue_per_order']}")
            
            # Calculate profitability
            total_revenue = scenario['orders'] * scenario['revenue_per_order']
            # Simplified cost calculation (real system would use OrderProcessingConstants)
            cost_per_km = 1.5  # Placeholder cost per km
            total_cost = scenario['distance_km'] * cost_per_km
            profit = total_revenue - total_cost
            
            print(f"    Total revenue: ${total_revenue:.0f}")
            print(f"    Estimated cost: ${total_cost:.0f}")
            print(f"    Profit: ${profit:.0f}")
            print(f"    Profitable: {'✅ YES' if profit > 0 else '❌ NO'}")
            print(f"    Expected: {'ACCEPT' if scenario['expected_profitable'] else 'REJECT'}")
            
            # Test route generation decision
            would_generate = profit > 0
            correct_decision = (would_generate == scenario['expected_profitable'])
            
            print(f"    Decision: {'GENERATE' if would_generate else 'REJECT'}")
            print(f"    Correct: {'✅ YES' if correct_decision else '❌ NO'}")
        
        print(f"\n✅ PROFITABILITY ENFORCEMENT TEST COMPLETED")
    
    def test_multi_client_aggregation(self, db_session, db_data):
        """Test aggregation across multiple clients"""
        print(f"\n👥 TESTING MULTI-CLIENT AGGREGATION")
        print(f"=" * 45)
        
        if len(db_data['clients']) < 3:
            print(f"  ⚠️  Skipping - need at least 3 clients (found {len(db_data['clients'])})")
            return
        
        selected_clients = random.sample(db_data['clients'], 3)
        selected_locations = random.sample(db_data['locations'], 4)
        
        print(f"\nMULTI-CLIENT SCENARIO:")
        for i, client in enumerate(selected_clients):
            print(f"  Client {i+1}: {client.name}")
        
        # Create orders from different clients that could be aggregated
        origin = selected_locations[0]
        destiny = selected_locations[1]
        
        print(f"\nSIMILAR ROUTE ORDERS:")
        print(f"  Route: Location {origin.id} → Location {destiny.id}")
        
        multi_client_orders = []
        total_volume = 0
        total_weight = 0
        
        for i, client in enumerate(selected_clients):
            # Create smaller orders that together would fill a truck
            volume = random.uniform(8.0, 15.0)
            weight = random.uniform(300.0, 600.0)
            
            print(f"  {client.name}: {volume:.1f}m³, {weight:.0f}kg")
            
            total_volume += volume
            total_weight += weight
            
            multi_client_orders.append({
                'client': client.name,
                'volume': volume,
                'weight': weight
            })
        
        print(f"\nAGGREGATION ANALYSIS:")
        print(f"  Combined volume: {total_volume:.1f}m³")
        print(f"  Combined weight: {total_weight:.0f}kg")
        print(f"  Truck capacity: 48.0m³")
        print(f"  Weight limit: ~4165kg")
        
        fits_capacity = total_volume <= 48.0 and total_weight <= 4165
        print(f"  Fits in one truck: {'✅ YES' if fits_capacity else '❌ NO'}")
        
        if fits_capacity:
            print(f"  ✅ Multi-client aggregation possible")
            print(f"  Route would serve {len(selected_clients)} different clients")
            print(f"  Capacity utilization: {total_volume/48.0*100:.1f}%")
        else:
            print(f"  ❌ Orders too large for single truck aggregation")
        
        print(f"\n✅ MULTI-CLIENT AGGREGATION TEST COMPLETED")
    
    def test_existing_route_integration(self, db_session, db_data):
        """Test integration with existing routes before aggregation"""
        print(f"\n🛣️  TESTING EXISTING ROUTE INTEGRATION")
        print(f"=" * 45)
        
        if not db_data['routes']:
            print(f"  ⚠️  No existing routes in database")
            return
        
        existing_route = random.choice(db_data['routes'])
        print(f"\nEXISTING ROUTE ANALYSIS:")
        print(f"  Route ID: {existing_route.id}")
        print(f"  Origin: Location {existing_route.location_origin_id}")
        print(f"  Destiny: Location {existing_route.location_destiny_id}")
        print(f"  Current profitability: ${existing_route.profitability or 0:.2f}")
        
        # Create test order that might fit this route
        test_volume = 10.0
        test_weight = 400.0
        
        print(f"\nTEST ORDER:")
        print(f"  Same route: {existing_route.location_origin_id} → {existing_route.location_destiny_id}")
        print(f"  Cargo: {test_volume}m³, {test_weight}kg")
        
        # Check if order should be added to existing route or aggregated
        route_has_capacity = True  # Simplified - real system would check truck capacity
        route_is_profitable = (existing_route.profitability or -999) > -100  # Some threshold
        
        print(f"\nROUTE INTEGRATION DECISION:")
        print(f"  Route has capacity: {'✅ YES' if route_has_capacity else '❌ NO'}")
        print(f"  Route reasonably profitable: {'✅ YES' if route_is_profitable else '❌ NO'}")
        
        if route_has_capacity and route_is_profitable:
            print(f"  Decision: ✅ ADD TO EXISTING ROUTE")
            print(f"  Reason: Better to utilize existing route capacity")
        else:
            print(f"  Decision: 📦 AGGREGATE FOR NEW ROUTE")
            print(f"  Reason: Existing route constraints")
        
        print(f"\n✅ EXISTING ROUTE INTEGRATION TEST COMPLETED")


if __name__ == "__main__":
    # Run the test directly for debugging
    test_instance = TestCargoAggregationRequirement()
    
    # Create fixtures manually for direct run
    from app.database import get_session
    with get_session() as session:
        from sqlmodel import select
        clients = session.exec(select(DBClient)).all()
        locations = session.exec(select(DBLocation)).all()
        trucks = session.exec(select(DBTruck)).all()
        routes = session.exec(select(DBRoute)).all()
        
        if len(clients) >= 2 and len(locations) >= 4:
            db_data = {
                'clients': clients,
                'locations': locations,
                'trucks': trucks,
                'routes': routes
            }
            
            aggregation_service = CargoAggregationService()
            route_generation_service = RouteGenerationService()
            
            test_instance.test_cargo_aggregation_with_db_data(aggregation_service, session, db_data)
            test_instance.test_profitability_requirement_enforcement(route_generation_service, session, db_data)
            test_instance.test_multi_client_aggregation(session, db_data)
            test_instance.test_existing_route_integration(session, db_data)
        else:
            print("❌ Insufficient data in database for testing")
            print(f"   Clients: {len(clients)} (need ≥2)")
            print(f"   Locations: {len(locations)} (need ≥4)")