"""
Comprehensive test suite for Cargo Aggregation and Route Generation Services

Tests the complete cargo aggregation and route generation workflow:
1. Finding unmatched orders
2. Creating compatible cargo combinations  
3. Generating profitable routes
4. Economic validation
"""

import pytest
import logging
from sqlmodel import Session, create_engine
from typing import List

# Import services and models
from app.database import (
    SQLModel, Client, Location, Order, Route, Truck, Cargo, Package, CargoType,
    create_location, create_order_from_dict
)
from services.cargo_aggregation_service import CargoAggregationService, CargoCombination
from services.route_generation_service import RouteGenerationService
from order_processor import OrderProcessor

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture 
def test_session(test_engine):
    """Create test session"""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def sample_data(test_session):
    """Create sample test data"""
    session = test_session
    
    # Create client
    client = Client(name="Test Logistics Co")
    session.add(client)
    session.flush()
    
    # Create locations (Georgia area)
    atlanta = create_location(session, 33.7490, -84.3880)  # Atlanta
    savannah = create_location(session, 32.0835, -81.0998)  # Savannah  
    augusta = create_location(session, 33.4735, -82.0105)   # Augusta
    macon = create_location(session, 32.8407, -83.6324)     # Macon
    columbus = create_location(session, 32.4609, -84.9877)  # Columbus
    
    # Create trucks
    truck1 = Truck(capacity=48.0, autonomy=800.0, type="standard")
    truck2 = Truck(capacity=48.0, autonomy=800.0, type="standard")
    session.add_all([truck1, truck2])
    session.flush()
    
    # Create existing route (Atlanta -> Savannah)
    route1 = Route(
        location_origin_id=atlanta.id,
        location_destiny_id=savannah.id,
        profitability=-100.0,  # Losing money
        truck_id=truck1.id
    )
    session.add(route1)
    session.flush()
    
    # Create unmatched orders (not assigned to any route)
    
    # Order 1: Atlanta area to Augusta area (compatible with route expansion)
    atlanta_nearby = create_location(session, 33.7500, -84.3890)  # 1km from Atlanta
    augusta_nearby = create_location(session, 33.4745, -82.0115)   # 1km from Augusta
    
    order1 = Order(
        location_origin_id=atlanta_nearby.id,
        location_destiny_id=augusta_nearby.id,
        client_id=client.id
    )
    session.add(order1)
    session.flush()
    
    # Add cargo to order1
    cargo1 = Cargo(order_id=order1.id)
    session.add(cargo1)
    session.flush()
    
    package1 = Package(volume=5.0, weight=100.0, type=CargoType.STANDARD, cargo_id=cargo1.id)
    session.add(package1)
    
    # Order 2: Macon to Columbus (new route potential)
    order2 = Order(
        location_origin_id=macon.id,
        location_destiny_id=columbus.id,
        client_id=client.id
    )
    session.add(order2)
    session.flush()
    
    cargo2 = Cargo(order_id=order2.id)
    session.add(cargo2)
    session.flush()
    
    package2 = Package(volume=8.0, weight=150.0, type=CargoType.STANDARD, cargo_id=cargo2.id)
    session.add(package2)
    
    # Order 3: Compatible with order2 (nearby locations)
    macon_nearby = create_location(session, 32.8417, -83.6334)    # Near Macon
    columbus_nearby = create_location(session, 32.4619, -84.9887) # Near Columbus
    
    order3 = Order(
        location_origin_id=macon_nearby.id,
        location_destiny_id=columbus_nearby.id,
        client_id=client.id
    )
    session.add(order3)
    session.flush()
    
    cargo3 = Cargo(order_id=order3.id)
    session.add(cargo3)
    session.flush()
    
    package3 = Package(volume=4.0, weight=80.0, type=CargoType.STANDARD, cargo_id=cargo3.id)
    session.add(package3)
    
    # Order 4: Incompatible cargo (hazmat + fragile)
    order4 = Order(
        location_origin_id=atlanta.id,
        location_destiny_id=augusta.id,
        client_id=client.id
    )
    session.add(order4)
    session.flush()
    
    cargo4a = Cargo(order_id=order4.id)
    cargo4b = Cargo(order_id=order4.id)
    session.add_all([cargo4a, cargo4b])
    session.flush()
    
    package4a = Package(volume=2.0, weight=50.0, type=CargoType.HAZMAT, cargo_id=cargo4a.id)
    package4b = Package(volume=3.0, weight=60.0, type=CargoType.FRAGILE, cargo_id=cargo4b.id)
    session.add_all([package4a, package4b])
    
    session.commit()
    
    return {
        'client': client,
        'locations': {
            'atlanta': atlanta,
            'savannah': savannah,
            'augusta': augusta,
            'macon': macon,
            'columbus': columbus
        },
        'trucks': [truck1, truck2],
        'routes': [route1],
        'orders': [order1, order2, order3, order4]
    }


def test_cargo_aggregation_service_initialization(test_session):
    """Test CargoAggregationService initialization"""
    service = CargoAggregationService(test_session)
    
    assert service.session == test_session
    assert service.order_processor is not None
    assert isinstance(service.order_processor, OrderProcessor)


def test_find_unmatched_orders(test_session, sample_data):
    """Test finding unmatched orders"""
    service = CargoAggregationService(test_session)
    
    routes = sample_data['routes']
    trucks = sample_data['trucks']
    
    unmatched_orders = service.find_unmatched_orders(routes, trucks)
    
    # Should find orders that don't fit existing Atlanta->Savannah route
    assert len(unmatched_orders) > 0
    logger.info(f"Found {len(unmatched_orders)} unmatched orders")
    
    # Verify these are actually unmatched by checking route_id is None
    for order in unmatched_orders:
        assert order.route_id is None


def test_find_compatible_combinations(test_session, sample_data):
    """Test finding compatible cargo combinations"""
    service = CargoAggregationService(test_session)
    
    routes = sample_data['routes']
    trucks = sample_data['trucks']
    
    # Get unmatched orders
    unmatched_orders = service.find_unmatched_orders(routes, trucks)
    
    if len(unmatched_orders) >= 2:
        combinations = service.find_compatible_combinations(unmatched_orders)
        
        logger.info(f"Found {len(combinations)} compatible combinations")
        
        # Verify combinations are valid
        for combo in combinations:
            assert isinstance(combo, CargoCombination)
            assert len(combo.orders) >= 2
            assert combo.total_volume_m3 <= 48.0  # Max truck capacity
            assert combo.total_weight_kg <= 9180.0 * 0.453592  # Max weight in kg
            assert combo.compatibility_score > 0
            
            logger.info(f"Combination: {len(combo.orders)} orders, "
                       f"{combo.total_volume_m3:.1f}m³, "
                       f"{combo.total_weight_kg:.1f}kg, "
                       f"score: {combo.compatibility_score:.1f}")


def test_cargo_type_compatibility(test_session, sample_data):
    """Test cargo type compatibility checking"""
    service = CargoAggregationService(test_session)
    
    # Test compatible types
    compatible_types = {CargoType.STANDARD, CargoType.REFRIGERATED}
    assert service._check_cargo_type_compatibility(compatible_types) == True
    
    # Test incompatible types (hazmat + fragile)
    incompatible_types = {CargoType.HAZMAT, CargoType.FRAGILE}
    assert service._check_cargo_type_compatibility(incompatible_types) == False
    
    # Test incompatible types (hazmat + refrigerated)
    incompatible_types2 = {CargoType.HAZMAT, CargoType.REFRIGERATED}
    assert service._check_cargo_type_compatibility(incompatible_types2) == False


def test_route_generation_service_initialization(test_session):
    """Test RouteGenerationService initialization"""
    service = RouteGenerationService(test_session)
    
    assert service.session == test_session
    assert service.constants is not None
    # route_service is None for demo purposes (OSMnx too slow)
    assert service.route_service is None


def test_economic_viability_validation(test_session, sample_data):
    """Test economic viability validation"""
    service = RouteGenerationService(test_session)
    aggregation_service = CargoAggregationService(test_session)
    
    routes = sample_data['routes']
    trucks = sample_data['trucks']
    
    unmatched_orders = aggregation_service.find_unmatched_orders(routes, trucks)
    
    if len(unmatched_orders) >= 2:
        combinations = aggregation_service.find_compatible_combinations(unmatched_orders)
        
        if combinations:
            combination = combinations[0]  # Test first combination
            
            is_viable, metrics = service.validate_economic_viability(combination)
            
            logger.info(f"Economic viability: {is_viable}")
            logger.info(f"Metrics: {metrics}")
            
            # Verify metrics structure
            expected_keys = ['estimated_distance_km', 'estimated_distance_miles', 
                           'estimated_cost_usd', 'estimated_revenue_usd', 
                           'estimated_profit_margin', 'min_profit_margin']
            
            for key in expected_keys:
                assert key in metrics
                assert isinstance(metrics[key], (int, float))


def test_route_generation_workflow(test_session, sample_data):
    """Test complete route generation workflow"""
    aggregation_service = CargoAggregationService(test_session)
    generation_service = RouteGenerationService(test_session)
    
    routes = sample_data['routes'] 
    trucks = sample_data['trucks']
    
    logger.info("=== CARGO AGGREGATION AND ROUTE GENERATION TEST ===")
    
    # Step 1: Find unmatched orders
    unmatched_orders = aggregation_service.find_unmatched_orders(routes, trucks)
    logger.info(f"Step 1: Found {len(unmatched_orders)} unmatched orders")
    
    if len(unmatched_orders) < 2:
        logger.warning("Not enough unmatched orders for combination testing")
        return
    
    # Step 2: Find compatible combinations
    combinations = aggregation_service.find_compatible_combinations(unmatched_orders)
    logger.info(f"Step 2: Found {len(combinations)} compatible combinations")
    
    if not combinations:
        logger.warning("No compatible combinations found")
        return
    
    # Step 3: Test route generation for best combination
    best_combination = combinations[0]
    logger.info(f"Step 3: Testing route generation for combination with {len(best_combination.orders)} orders")
    
    available_truck = trucks[1] if len(trucks) > 1 else trucks[0]  # Use second truck
    
    result = generation_service.generate_profitable_route(best_combination, available_truck)
    
    logger.info(f"Route generation result:")
    logger.info(f"  Success: {result.success}")
    logger.info(f"  Estimated profit: ${result.estimated_profit:.2f}")
    logger.info(f"  Estimated cost: ${result.estimated_cost:.2f}")
    logger.info(f"  Estimated revenue: ${result.estimated_revenue:.2f}")
    logger.info(f"  Distance: {result.total_distance_km:.1f} km")
    logger.info(f"  Time: {result.total_time_hours:.1f} hours")
    logger.info(f"  Orders included: {result.orders_included}")
    
    if not result.success:
        logger.info(f"  Error: {result.error_message}")
    
    # Verify result structure
    assert isinstance(result.success, bool)
    assert isinstance(result.estimated_profit, (int, float))
    assert isinstance(result.estimated_cost, (int, float))
    assert isinstance(result.estimated_revenue, (int, float))
    assert result.orders_included == len(best_combination.orders)


def test_analyze_aggregation_opportunities(test_session, sample_data):
    """Test comprehensive aggregation analysis"""
    service = CargoAggregationService(test_session)
    
    routes = sample_data['routes']
    trucks = sample_data['trucks']
    
    result = service.analyze_aggregation_opportunities(routes, trucks)
    
    logger.info(f"Aggregation opportunities analysis:")
    logger.info(f"  Unmatched orders: {len(result.unmatched_orders)}")
    logger.info(f"  Compatible combinations: {len(result.compatible_combinations)}")
    logger.info(f"  Total unmatched volume: {result.total_unmatched_volume:.1f} m³")
    logger.info(f"  Total unmatched weight: {result.total_unmatched_weight:.1f} kg")
    logger.info(f"  Aggregation opportunities: {result.aggregation_opportunities}")
    
    # Verify result structure
    assert isinstance(result.unmatched_orders, list)
    assert isinstance(result.compatible_combinations, list)
    assert isinstance(result.total_unmatched_volume, (int, float))
    assert isinstance(result.total_unmatched_weight, (int, float))
    assert isinstance(result.aggregation_opportunities, int)
    assert result.aggregation_opportunities == len(result.compatible_combinations)


if __name__ == "__main__":
    # Run tests manually for development
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Create test session and data
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Create sample data inline for manual testing
        client = Client(name="Test Logistics Co")
        session.add(client)
        session.flush()
        
        # Create locations
        atlanta = create_location(session, 33.7490, -84.3880)
        macon = create_location(session, 32.8407, -83.6324)
        columbus = create_location(session, 32.4609, -84.9877)
        
        # Create trucks
        truck1 = Truck(capacity=48.0, autonomy=800.0, type="standard")
        truck2 = Truck(capacity=48.0, autonomy=800.0, type="standard")
        session.add_all([truck1, truck2])
        session.flush()
        
        # Create route
        route1 = Route(
            location_origin_id=atlanta.id,
            location_destiny_id=macon.id,
            profitability=-50.0,
            truck_id=truck1.id
        )
        session.add(route1)
        session.flush()
        
        # Create unmatched orders
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
        session.commit()
        
        # Run manual test
        logger.info("=== MANUAL CARGO AGGREGATION TEST ===")
        
        aggregation_service = CargoAggregationService(session)
        generation_service = RouteGenerationService(session)
        
        result = aggregation_service.analyze_aggregation_opportunities([route1], [truck1, truck2])
        
        print(f"\nUnmatched orders: {len(result.unmatched_orders)}")
        print(f"Compatible combinations: {len(result.compatible_combinations)}")
        print(f"Aggregation opportunities: {result.aggregation_opportunities}")
        
        if result.compatible_combinations:
            combo = result.compatible_combinations[0]
            print(f"\nTesting route generation for combination with {len(combo.orders)} orders...")
            
            route_result = generation_service.generate_profitable_route(combo, truck2)
            print(f"Route generation success: {route_result.success}")
            if route_result.success:
                print(f"Estimated profit: ${route_result.estimated_profit:.2f}")
            else:
                print(f"Error: {route_result.error_message}")
        
        print("\n=== MANUAL TEST COMPLETE ===")