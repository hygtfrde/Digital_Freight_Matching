"""
Demo script for Cargo Aggregation and Route Generation Services

Demonstrates the complete workflow:
1. Finding unmatched orders
2. Creating compatible cargo combinations  
3. Generating profitable routes
4. Integration with existing system
"""

import sys
import os
import logging
from sqlmodel import Session

# Add project paths
sys.path.insert(0, os.path.abspath('.'))

from app.database import engine, Client, Location, Order, Truck, Route, Cargo, Package, CargoType
from services.cargo_aggregation_service import CargoAggregationService
from services.route_generation_service import RouteGenerationService
from services.integrated_matching_service import IntegratedMatchingService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_demo_data(session: Session):
    """Create demo data for testing"""
    logger.info("Creating demo data...")
    
    # Create client
    client = Client(name="Demo Logistics Inc")
    session.add(client)
    session.flush()
    
    # Create locations (Georgia area)
    atlanta = Location(lat=33.7490, lng=-84.3880, marked=False)
    savannah = Location(lat=32.0835, lng=-81.0998, marked=False)
    augusta = Location(lat=33.4735, lng=-82.0105, marked=False)
    macon = Location(lat=32.8407, lng=-83.6324, marked=False)
    columbus = Location(lat=32.4609, lng=-84.9877, marked=False)
    
    locations = [atlanta, savannah, augusta, macon, columbus]
    session.add_all(locations)
    session.flush()
    
    # Create trucks
    truck1 = Truck(capacity=48.0, autonomy=800.0, type="standard", cargo_loads=[])
    truck2 = Truck(capacity=48.0, autonomy=800.0, type="standard", cargo_loads=[])
    truck3 = Truck(capacity=48.0, autonomy=800.0, type="refrigerated", cargo_loads=[])
    
    trucks = [truck1, truck2, truck3]
    session.add_all(trucks)
    session.flush()
    
    # Create existing route (losing money)
    existing_route = Route(
        location_origin_id=atlanta.id,
        location_destiny_id=savannah.id,
        profitability=-100.0,
        truck_id=truck1.id
    )
    session.add(existing_route)
    session.flush()
    
    # Create unmatched orders
    orders = []
    
    # Order 1: Macon to Columbus
    order1 = Order(
        location_origin_id=macon.id,
        location_destiny_id=columbus.id,
        client_id=client.id
    )
    session.add(order1)
    session.flush()
    
    cargo1 = Cargo(order_id=order1.id)
    session.add(cargo1)
    session.flush()
    
    package1 = Package(volume=10.0, weight=200.0, type=CargoType.STANDARD, cargo_id=cargo1.id)
    session.add(package1)
    orders.append(order1)
    
    # Order 2: Augusta to Macon (compatible for combination)
    order2 = Order(
        location_origin_id=augusta.id,
        location_destiny_id=macon.id,
        client_id=client.id
    )
    session.add(order2)
    session.flush()
    
    cargo2 = Cargo(order_id=order2.id)
    session.add(cargo2)
    session.flush()
    
    package2 = Package(volume=8.0, weight=150.0, type=CargoType.STANDARD, cargo_id=cargo2.id)
    session.add(package2)
    orders.append(order2)
    
    # Order 3: Columbus to Atlanta
    order3 = Order(
        location_origin_id=columbus.id,
        location_destiny_id=atlanta.id,
        client_id=client.id
    )
    session.add(order3)
    session.flush()
    
    cargo3 = Cargo(order_id=order3.id)
    session.add(cargo3)
    session.flush()
    
    package3 = Package(volume=6.0, weight=120.0, type=CargoType.REFRIGERATED, cargo_id=cargo3.id)
    session.add(package3)
    orders.append(order3)
    
    session.commit()
    
    logger.info(f"Created demo data: {len(locations)} locations, {len(trucks)} trucks, "
               f"1 existing route, {len(orders)} unmatched orders")
    
    return {
        'client': client,
        'locations': locations,
        'trucks': trucks,
        'existing_routes': [existing_route],
        'orders': orders
    }


def demo_cargo_aggregation():
    """Demonstrate cargo aggregation service"""
    logger.info("=== CARGO AGGREGATION SERVICE DEMO ===")
    
    with Session(engine) as session:
        # Create demo data
        data = create_demo_data(session)
        
        # Initialize services
        aggregation_service = CargoAggregationService(session)
        
        # Analyze aggregation opportunities
        result = aggregation_service.analyze_aggregation_opportunities(
            data['existing_routes'], 
            data['trucks']
        )
        
        print(f"\n📊 AGGREGATION ANALYSIS RESULTS:")
        print(f"   Unmatched orders: {len(result.unmatched_orders)}")
        print(f"   Compatible combinations: {len(result.compatible_combinations)}")
        print(f"   Total unmatched volume: {result.total_unmatched_volume:.1f} m³")
        print(f"   Total unmatched weight: {result.total_unmatched_weight:.1f} kg")
        print(f"   Aggregation opportunities: {result.aggregation_opportunities}")
        
        # Show details of combinations
        if result.compatible_combinations:
            print(f"\n🔗 COMPATIBLE COMBINATIONS:")
            for i, combo in enumerate(result.compatible_combinations[:3]):  # Show top 3
                print(f"   Combination {i+1}:")
                print(f"     Orders: {len(combo.orders)}")
                print(f"     Volume: {combo.total_volume_m3:.1f} m³")
                print(f"     Weight: {combo.total_weight_kg:.1f} kg")
                print(f"     Score: {combo.compatibility_score:.1f}")
                print(f"     Cargo types: {[ct.value for ct in combo.cargo_types]}")
        
        return result


def demo_route_generation():
    """Demonstrate route generation service"""
    logger.info("=== ROUTE GENERATION SERVICE DEMO ===")
    
    with Session(engine) as session:
        # Create demo data
        data = create_demo_data(session)
        
        # Initialize services
        aggregation_service = CargoAggregationService(session)
        generation_service = RouteGenerationService(session)
        
        # Get aggregation opportunities
        aggregation_result = aggregation_service.analyze_aggregation_opportunities(
            data['existing_routes'], 
            data['trucks']
        )
        
        if not aggregation_result.compatible_combinations:
            print("❌ No compatible combinations found for route generation")
            return None
        
        # Test route generation for best combination
        best_combination = aggregation_result.compatible_combinations[0]
        available_truck = data['trucks'][1]  # Use second truck
        
        print(f"\n🚛 TESTING ROUTE GENERATION:")
        print(f"   Combination: {len(best_combination.orders)} orders")
        print(f"   Available truck: {available_truck.type} (capacity: {available_truck.capacity}m³)")
        
        # Generate route
        route_result = generation_service.generate_profitable_route(best_combination, available_truck)
        
        print(f"\n📈 ROUTE GENERATION RESULTS:")
        print(f"   Success: {'✅ YES' if route_result.success else '❌ NO'}")
        print(f"   Estimated profit: ${route_result.estimated_profit:.2f}")
        print(f"   Estimated cost: ${route_result.estimated_cost:.2f}")
        print(f"   Estimated revenue: ${route_result.estimated_revenue:.2f}")
        print(f"   Distance: {route_result.total_distance_km:.1f} km")
        print(f"   Time: {route_result.total_time_hours:.1f} hours")
        print(f"   Orders included: {route_result.orders_included}")
        
        if not route_result.success:
            print(f"   Error: {route_result.error_message}")
        
        return route_result


def demo_integrated_matching():
    """Demonstrate integrated matching service"""
    logger.info("=== INTEGRATED MATCHING SERVICE DEMO ===")
    
    with Session(engine) as session:
        # Create demo data
        data = create_demo_data(session)
        
        # Initialize integrated service
        integrated_service = IntegratedMatchingService(session)
        
        print(f"\n🔄 STARTING INTEGRATED MATCHING:")
        print(f"   Orders to process: {len(data['orders'])}")
        print(f"   Existing routes: {len(data['existing_routes'])}")
        print(f"   Available trucks: {len(data['trucks'])}")
        
        # Run integrated matching
        result = integrated_service.process_orders_with_aggregation(
            data['orders'],
            data['existing_routes'],
            data['trucks']
        )
        
        print(f"\n🎯 INTEGRATED MATCHING RESULTS:")
        print(f"   Total orders processed: {result.total_orders_processed}")
        print(f"   Matched to existing routes: {result.matched_to_existing_routes}")
        print(f"   Orders still unmatched: {result.unmatched_orders}")
        print(f"   New routes generated: {result.new_routes_generated}")
        print(f"   Total orders assigned: {result.total_orders_assigned}")
        print(f"   Additional profit estimate: ${result.estimated_additional_profit:.2f}")
        
        if result.successful_combinations:
            print(f"\n✅ SUCCESSFUL COMBINATIONS:")
            for i, combo in enumerate(result.successful_combinations):
                print(f"     Route {i+1}: {combo['orders_count']} orders, "
                      f"${combo['estimated_profit']:.2f} profit")
        
        if result.failed_combinations:
            print(f"\n❌ FAILED COMBINATIONS:")
            for i, combo in enumerate(result.failed_combinations):
                error = combo.get('error', 'Unknown error')
                print(f"     Combination {i+1}: {combo['orders_count']} orders - {error}")
        
        if result.processing_errors:
            print(f"\n⚠️  PROCESSING ERRORS:")
            for error in result.processing_errors:
                print(f"     {error}")
        
        # Generate performance report
        report = integrated_service.generate_performance_report(result)
        
        print(f"\n📊 PERFORMANCE REPORT:")
        print(f"   Assignment rate: {report['processing_summary']['assignment_rate_percent']}%")
        print(f"   Integration successful: {report['success_metrics']['integration_successful']}")
        print(f"   Routes generated: {report['success_metrics']['some_routes_generated']}")
        print(f"   Profit improvement: {report['success_metrics']['profit_improvement']}")
        
        return result


def main():
    """Run all demos"""
    print("🚛 DIGITAL FREIGHT MATCHING - CARGO AGGREGATION & ROUTE GENERATION DEMO")
    print("=" * 80)
    
    try:
        # Demo 1: Cargo Aggregation
        aggregation_result = demo_cargo_aggregation()
        
        print("\n" + "=" * 80)
        
        # Demo 2: Route Generation  
        route_result = demo_route_generation()
        
        print("\n" + "=" * 80)
        
        # Demo 3: Integrated Matching
        integrated_result = demo_integrated_matching()
        
        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        
        # Summary
        print(f"\n🎯 SUMMARY:")
        if aggregation_result:
            print(f"   Found {aggregation_result.aggregation_opportunities} aggregation opportunities")
        if route_result and route_result.success:
            print(f"   Generated route with ${route_result.estimated_profit:.2f} profit potential")
        if integrated_result:
            print(f"   Integrated matching: {integrated_result.total_orders_assigned}/{integrated_result.total_orders_processed} orders assigned")
            print(f"   Estimated additional profit: ${integrated_result.estimated_additional_profit:.2f}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ DEMO FAILED: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())