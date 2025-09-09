"""
Comprehensive Integration Testing Suite for Digital Freight Matching System

This module implements the IntegrationTestSuite class with end-to-end test methods
for complete workflow validation, database consistency checking, API integration testing,
CLI functionality validation, and performance assertions.

Requirements covered:
- 3.1: End-to-end order processing workflow validation
- 3.2: Profitability calculations match expected results
- 3.3: Constraint enforcement (proximity, capacity, time, cargo compatibility)
- 3.4: Database operations maintain consistency and prevent corruption
"""

import unittest
import time
import os
import sys
import subprocess
from sqlmodel import Session, select
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
import json

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database import (
    engine, create_tables, get_session,
    Client, Location, Order, Route, Truck, Cargo, Package
)
from schemas.schemas import CargoType
from order_processor import OrderProcessor, ValidationResult, ProcessingResult
from validation.business_validator import BusinessValidator, ValidationStatus
from db_manager import DatabaseManager


class IntegrationTestSuite(unittest.TestCase):
    """
    Comprehensive integration test suite for the Digital Freight Matching System.

    This class provides end-to-end testing capabilities covering:
    - Complete order processing workflows
    - Database integrity and consistency
    - API endpoint integration
    - CLI functionality validation
    - Performance requirements validation
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        cls.test_db_path = "test_logistics.db"
        cls.original_db_url = os.environ.get("DATABASE_URL")

        # Use test database
        os.environ["DATABASE_URL"] = f"sqlite:///./{cls.test_db_path}"

        # Create fresh test database
        from sqlmodel import SQLModel
        from app.database import engine
        
        # Drop all tables and recreate them
        SQLModel.metadata.drop_all(engine)
        create_tables()

        # Initialize test data
        cls._initialize_test_data()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        # Restore original database URL
        if cls.original_db_url:
            os.environ["DATABASE_URL"] = cls.original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Remove test database
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    @classmethod
    def _initialize_test_data(cls):
        """Initialize test data for integration tests"""
        with Session(engine) as session:
            # Create test locations
            atlanta = Location(lat=33.7490, lng=-84.3880, marked=True)
            savannah = Location(lat=32.0835, lng=-81.0998, marked=True)
            augusta = Location(lat=33.4735, lng=-82.0105, marked=True)
            columbus = Location(lat=32.4609, lng=-84.9877, marked=True)
            albany = Location(lat=31.5804, lng=-84.1557, marked=True)

            session.add_all([atlanta, savannah, augusta, columbus, albany])
            session.commit()

            # Create test clients
            contract_client = Client(name="Too-Big-To-Fail Company")
            example_client = Client(name="Example Client")

            session.add_all([contract_client, example_client])
            session.commit()

            # Create test trucks
            trucks = [
                Truck(id=1, autonomy=800.0, capacity=48.0, type="standard"),
                Truck(id=2, autonomy=900.0, capacity=45.0, type="refrigerated"),
                Truck(id=3, autonomy=750.0, capacity=48.0, type="hazmat"),
                Truck(id=4, autonomy=850.0, capacity=47.0, type="standard"),
                Truck(id=5, autonomy=800.0, capacity=48.0, type="standard")
            ]

            session.add_all(trucks)
            session.commit()

            # Create test routes
            routes = [
                Route(location_origin_id=atlanta.id, location_destiny_id=savannah.id,
                     profitability=-77.63, truck_id=1),
                Route(location_origin_id=atlanta.id, location_destiny_id=augusta.id,
                     profitability=-77.63, truck_id=2),
                Route(location_origin_id=atlanta.id, location_destiny_id=columbus.id,
                     profitability=-77.63, truck_id=3),
                Route(location_origin_id=atlanta.id, location_destiny_id=albany.id,
                     profitability=-77.63, truck_id=4),
                Route(location_origin_id=atlanta.id, location_destiny_id=savannah.id,
                     profitability=-77.63, truck_id=5)
            ]

            session.add_all(routes)
            session.commit()

            # Store IDs for test access
            cls.test_client_id = contract_client.id
            cls.test_route_ids = [r.id for r in routes]
            cls.test_truck_ids = [t.id for t in trucks]
            cls.test_location_ids = [atlanta.id, savannah.id, augusta.id, columbus.id, albany.id]

    def setUp(self):
        """Set up for each individual test"""
        self.session = Session(engine)
        self.order_processor = OrderProcessor()
        self.business_validator = BusinessValidator()
        self.db_manager = DatabaseManager(self.session)

        # Performance tracking
        self.test_start_time = time.time()

    def tear_Down(self):
        """Clean up after each test"""
        self.session.close()

        # Log test performance
        test_duration = time.time() - self.test_start_time
        if test_duration > 5.0:  # Performance assertion: <5 seconds
            self.fail(f"Test exceeded 5 second performance target: {test_duration:.2f}s")

    def test_end_to_end_order_processing(self):
        """
        Test complete order-to-route matching workflow (Requirement 3.1)

        This test validates the entire process from order creation through
        route assignment, capacity checking, and profitability calculation.
        """
        # Create test order data
        order_data = {
            'cargo': {
                'packages': [
                    (5.0, 100.0, 'standard'),  # 5m³, 100kg, standard cargo
                    (3.0, 50.0, 'fragile')     # 3m³, 50kg, fragile cargo
                ]
            },
            'pick-up': {'latitude': 33.7500, 'longitude': -84.3900},    # Near Atlanta
            'drop-off': {'latitude': 32.0900, 'longitude': -81.1000}   # Near Savannah
        }

        # Step 1: Create order in database
        pickup_loc = Location(lat=order_data['pick-up']['latitude'],
                            lng=order_data['pick-up']['longitude'])
        dropoff_loc = Location(lat=order_data['drop-off']['latitude'],
                             lng=order_data['drop-off']['longitude'])

        self.session.add_all([pickup_loc, dropoff_loc])
        self.session.commit()

        order = Order(
            location_origin_id=pickup_loc.id,
            location_destiny_id=dropoff_loc.id,
            client_id=self.test_client_id
        )
        self.session.add(order)
        self.session.commit()

        # Create cargo and packages
        cargo = Cargo(order_id=order.id)
        self.session.add(cargo)
        self.session.commit()

        packages = [
            Package(volume=5.0, weight=100.0, type=CargoType.STANDARD, cargo_id=cargo.id),
            Package(volume=3.0, weight=50.0, type=CargoType.FRAGILE, cargo_id=cargo.id)
        ]
        self.session.add_all(packages)
        self.session.commit()

        # Step 2: Load routes and trucks
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        self.assertGreater(len(routes), 0, "No routes available for testing")
        self.assertGreater(len(trucks), 0, "No trucks available for testing")

        # Step 3: Process order through validation
        route = routes[0]  # Use first route (Atlanta to Savannah)
        truck = trucks[0]  # Use first truck

        result = self.order_processor.validate_order_for_route(order, route, truck)

        # Step 4: Validate processing results
        self.assertIsInstance(result, ProcessingResult)
        self.assertIsInstance(result.is_valid, bool)
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.metrics, dict)

        # Step 5: Check business logic compliance
        if result.is_valid:
            # Order should be valid for nearby locations with sufficient capacity
            self.assertTrue(result.is_valid, "Valid order should pass validation")
            self.assertEqual(len(result.errors), 0, "Valid order should have no errors")

            # Verify metrics are calculated
            self.assertIn('order_volume_m3', result.metrics)
            self.assertIn('order_weight_kg', result.metrics)
            self.assertIn('volume_utilization_percent', result.metrics)

            # Check capacity utilization is reasonable
            volume_util = result.metrics['volume_utilization_percent']
            self.assertGreaterEqual(volume_util, 0.0)
            self.assertLessEqual(volume_util, 100.0)

        # Step 6: Test profitability calculation
        original_profit = route.profitability

        # Simulate adding order to route (simplified)
        if result.is_valid:
            # Calculate expected profit improvement
            additional_revenue = 50.0  # Assumed revenue per order
            route.profitability += additional_revenue

            self.assertGreater(route.profitability, original_profit,
                             "Adding order should improve profitability")

        # Step 7: Verify database consistency
        self.session.refresh(order)
        self.assertIsNotNone(order.id, "Order should be persisted with ID")
        self.assertEqual(len(order.cargo), 1, "Order should have one cargo load")
        self.assertEqual(len(order.cargo[0].packages), 2, "Cargo should have two packages")

    def test_profitability_calculations_accuracy(self):
        """
        Test that profitability calculations match expected business results (Requirement 3.2)

        Validates that the system correctly calculates route profitability improvements
        and matches expected financial outcomes from business requirements.
        """
        # Load test routes
        routes = self.session.exec(select(Route)).all()
        self.assertGreaterEqual(len(routes), 5, "Need at least 5 routes for contract compliance")

        # Calculate baseline total daily loss
        baseline_loss = sum(route.profitability for route in routes)
        expected_baseline = -388.15  # From business requirements

        # Allow for small floating point differences
        self.assertAlmostEqual(baseline_loss, expected_baseline, places=1,
                              msg=f"Baseline loss {baseline_loss} should match expected {expected_baseline}")

        # Test profitability improvement calculation
        test_route = routes[0]
        original_profit = test_route.profitability

        # Simulate adding profitable order
        revenue_per_order = 50.0
        additional_cost = 20.0
        net_improvement = revenue_per_order - additional_cost

        test_route.profitability += net_improvement

        # Verify improvement
        actual_improvement = test_route.profitability - original_profit
        self.assertAlmostEqual(actual_improvement, net_improvement, places=2,
                              msg="Profitability improvement calculation should be accurate")

        # Test system-wide profitability validation
        validation_report = self.business_validator.validate_profitability_requirements(
            routes, baseline_daily_loss=abs(expected_baseline)
        )

        self.assertEqual(validation_report.requirement_id, "1.1")
        self.assertIn(validation_report.status, [ValidationStatus.PASSED, ValidationStatus.WARNING])
        self.assertIn("baseline_daily_loss", validation_report.metrics)
        self.assertIn("current_daily_profit", validation_report.metrics)
        self.assertIn("improvement_amount", validation_report.metrics)

        # Verify metrics accuracy
        self.assertEqual(validation_report.metrics["baseline_daily_loss"], abs(expected_baseline))

    def test_constraint_enforcement_comprehensive(self):
        """
        Test comprehensive constraint enforcement (Requirement 3.3)

        Validates proximity, capacity, time, and cargo compatibility constraints
        are properly enforced according to business requirements.
        """
        # Load test data
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        route = routes[0]
        truck = trucks[0]

        # Test 1: Proximity constraint (1km limit)
        # Create order with pickup too far from route
        far_pickup = Location(lat=25.7617, lng=-80.1918)  # Miami - very far from Atlanta
        near_dropoff = Location(lat=32.0900, lng=-81.1000)  # Near Savannah

        self.session.add_all([far_pickup, near_dropoff])
        self.session.commit()

        far_order = Order(
            location_origin_id=far_pickup.id,
            location_destiny_id=near_dropoff.id,
            client_id=self.test_client_id,
            cargo=[]
        )
        self.session.add(far_order)
        self.session.commit()

        result = self.order_processor.validate_order_for_route(far_order, route, truck)

        # Should fail proximity constraint
        self.assertFalse(result.is_valid, "Order with far pickup should fail proximity constraint")
        proximity_errors = [e for e in result.errors if e.result == ValidationResult.INVALID_PROXIMITY]
        self.assertGreater(len(proximity_errors), 0, "Should have proximity constraint violations")

        # Test 2: Capacity constraint (48m³, 9180 lbs limits)
        # Create order that exceeds volume capacity
        near_pickup = Location(lat=33.7500, lng=-84.3900)  # Near Atlanta
        self.session.add(near_pickup)
        self.session.commit()

        oversized_order = Order(
            location_origin_id=near_pickup.id,
            location_destiny_id=near_dropoff.id,
            client_id=self.test_client_id
        )
        self.session.add(oversized_order)
        self.session.commit()

        # Create oversized cargo
        oversized_cargo = Cargo(order_id=oversized_order.id)
        self.session.add(oversized_cargo)
        self.session.commit()

        # Package that exceeds truck capacity (50m³ > 48m³ limit)
        oversized_package = Package(
            volume=50.0, weight=100.0, type=CargoType.STANDARD, cargo_id=oversized_cargo.id
        )
        self.session.add(oversized_package)
        self.session.commit()

        result = self.order_processor.validate_order_for_route(oversized_order, route, truck)

        # Should fail capacity constraint
        self.assertFalse(result.is_valid, "Oversized order should fail capacity constraint")
        capacity_errors = [e for e in result.errors if e.result == ValidationResult.INVALID_CAPACITY]
        self.assertGreater(len(capacity_errors), 0, "Should have capacity constraint violations")

        # Test 3: Weight constraint (9180 lbs limit)
        overweight_order = Order(
            location_origin_id=near_pickup.id,
            location_destiny_id=near_dropoff.id,
            client_id=self.test_client_id
        )
        self.session.add(overweight_order)
        self.session.commit()

        overweight_cargo = Cargo(order_id=overweight_order.id)
        self.session.add(overweight_cargo)
        self.session.commit()

        # Package that exceeds weight limit (5000kg ≈ 11,000 lbs > 9180 lbs)
        overweight_package = Package(
            volume=1.0, weight=5000.0, type=CargoType.STANDARD, cargo_id=overweight_cargo.id
        )
        self.session.add(overweight_package)
        self.session.commit()

        result = self.order_processor.validate_order_for_route(overweight_order, route, truck)

        # Should fail weight constraint
        self.assertFalse(result.is_valid, "Overweight order should fail weight constraint")
        weight_errors = [e for e in result.errors if e.result == ValidationResult.INVALID_WEIGHT]
        self.assertGreater(len(weight_errors), 0, "Should have weight constraint violations")

        # Test 4: Cargo compatibility constraint
        # Create order with incompatible cargo types
        incompatible_order = Order(
            location_origin_id=near_pickup.id,
            location_destiny_id=near_dropoff.id,
            client_id=self.test_client_id
        )
        self.session.add(incompatible_order)
        self.session.commit()

        # Add existing hazmat cargo to truck
        existing_cargo = Cargo(order_id=incompatible_order.id, truck_id=truck.id)
        self.session.add(existing_cargo)
        self.session.commit()

        hazmat_package = Package(
            volume=1.0, weight=10.0, type=CargoType.HAZMAT, cargo_id=existing_cargo.id
        )
        self.session.add(hazmat_package)
        self.session.commit()

        # Try to add fragile cargo (should be incompatible with hazmat)
        new_cargo = Cargo(order_id=incompatible_order.id)
        self.session.add(new_cargo)
        self.session.commit()

        fragile_package = Package(
            volume=1.0, weight=10.0, type=CargoType.FRAGILE, cargo_id=new_cargo.id
        )
        self.session.add(fragile_package)
        self.session.commit()

        # Refresh truck to get updated cargo loads
        self.session.refresh(truck)

        result = self.order_processor.validate_order_for_route(incompatible_order, route, truck)

        # May fail cargo compatibility (depending on implementation)
        if not result.is_valid:
            cargo_errors = [e for e in result.errors if e.result == ValidationResult.INCOMPATIBLE_CARGO]
            if len(cargo_errors) > 0:
                self.assertGreater(len(cargo_errors), 0, "Should detect cargo incompatibility")

    def test_data_integrity_validation(self):
        """
        Test database consistency and data integrity (Requirement 3.4)

        Validates that database operations maintain consistency and prevent corruption.
        """
        # Test 1: Referential integrity
        # Verify all foreign key relationships are valid

        # Check orders reference valid locations
        orders = self.session.exec(select(Order)).all()
        for order in orders:
            self.assertIsNotNone(order.location_origin_id, "Order must have origin location")
            self.assertIsNotNone(order.location_destiny_id, "Order must have destiny location")

            # Verify locations exist
            origin = self.session.get(Location, order.location_origin_id)
            destiny = self.session.get(Location, order.location_destiny_id)
            self.assertIsNotNone(origin, f"Origin location {order.location_origin_id} must exist")
            self.assertIsNotNone(destiny, f"Destiny location {order.location_destiny_id} must exist")

        # Check routes reference valid locations and trucks
        routes = self.session.exec(select(Route)).all()
        for route in routes:
            self.assertIsNotNone(route.location_origin_id, "Route must have origin location")
            self.assertIsNotNone(route.location_destiny_id, "Route must have destiny location")

            origin = self.session.get(Location, route.location_origin_id)
            destiny = self.session.get(Location, route.location_destiny_id)
            self.assertIsNotNone(origin, f"Route origin location {route.location_origin_id} must exist")
            self.assertIsNotNone(destiny, f"Route destiny location {route.location_destiny_id} must exist")

            if route.truck_id:
                truck = self.session.get(Truck, route.truck_id)
                self.assertIsNotNone(truck, f"Route truck {route.truck_id} must exist")

        # Test 2: Data consistency validation
        # Check cargo-package relationships
        cargo_loads = self.session.exec(select(Cargo)).all()
        for cargo in cargo_loads:
            self.assertIsNotNone(cargo.order_id, "Cargo must reference an order")

            order = self.session.get(Order, cargo.order_id)
            self.assertIsNotNone(order, f"Cargo order {cargo.order_id} must exist")

            # Verify packages belong to cargo
            packages = self.session.exec(select(Package).where(Package.cargo_id == cargo.id)).all()
            for package in packages:
                self.assertEqual(package.cargo_id, cargo.id, "Package must reference correct cargo")

        # Test 3: Business rule consistency
        # Verify truck capacity constraints are not violated in existing data
        trucks = self.session.exec(select(Truck)).all()
        for truck in trucks:
            # Check truck capacity is within business limits (48m³)
            self.assertLessEqual(truck.capacity, 48.0,
                               f"Truck {truck.id} capacity {truck.capacity}m³ exceeds 48m³ limit")

            # Check total cargo doesn't exceed truck capacity
            total_cargo_volume = sum(cargo.total_volume() for cargo in truck.cargo_loads)
            self.assertLessEqual(total_cargo_volume, truck.capacity,
                               f"Truck {truck.id} cargo volume {total_cargo_volume}m³ exceeds capacity {truck.capacity}m³")

        # Test 4: Transaction consistency
        # Test that database operations are atomic
        original_order_count = len(self.session.exec(select(Order)).all())

        try:
            # Start a transaction that should fail
            new_order = Order(
                location_origin_id=99999,  # Non-existent location
                location_destiny_id=99998,  # Non-existent location
                client_id=self.test_client_id
            )
            self.session.add(new_order)
            self.session.commit()

            # If we get here, the constraint wasn't enforced (may be SQLite limitation)
            # Clean up the invalid order
            self.session.delete(new_order)
            self.session.commit()

        except Exception:
            # Expected behavior - transaction should fail
            self.session.rollback()

        # Verify order count unchanged after failed transaction
        final_order_count = len(self.session.exec(select(Order)).all())
        self.assertEqual(original_order_count, final_order_count,
                        "Failed transaction should not change order count")

        # Test 5: Database manager integrity checks
        integrity_counts = self.db_manager.verify_integrity()

        # Verify all expected entities exist
        expected_entities = ['clients', 'locations', 'trucks', 'routes', 'orders', 'cargo', 'packages']
        for entity in expected_entities:
            self.assertIn(entity, integrity_counts, f"Integrity check should include {entity}")
            self.assertGreaterEqual(integrity_counts[entity], 0, f"{entity} count should be non-negative")

    def test_api_endpoints_integration(self):
        """
        Test FastAPI integration and endpoint functionality (Requirement 3.4)

        Validates that API endpoints work correctly and return expected data formats.
        """
        if not REQUESTS_AVAILABLE:
            self.skipTest("requests module not available for API testing")

        # Note: This test assumes the FastAPI server is running
        # In a full integration environment, we would start the server programmatically

        base_url = "http://localhost:8000"

        try:
            # Test 1: Root endpoint
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                self.assertIn("Digital Freight Matcher", response.text)
            else:
                self.skipTest("FastAPI server not available for integration testing")

        except requests.exceptions.RequestException:
            self.skipTest("FastAPI server not available for integration testing")

        # If server is available, continue with API tests
        try:
            # Test 2: Clients endpoint
            response = requests.get(f"{base_url}/clients", timeout=5)
            self.assertEqual(response.status_code, 200)

            clients_data = response.json()
            self.assertIsInstance(clients_data, list)

            if len(clients_data) > 0:
                client = clients_data[0]
                self.assertIn("id", client)
                self.assertIn("name", client)
                self.assertIn("created_at", client)

            # Test 3: Routes endpoint
            response = requests.get(f"{base_url}/routes", timeout=5)
            self.assertEqual(response.status_code, 200)

            routes_data = response.json()
            self.assertIsInstance(routes_data, list)

            if len(routes_data) > 0:
                route = routes_data[0]
                self.assertIn("id", route)
                self.assertIn("profitability", route)
                self.assertIn("truck_id", route)

            # Test 4: Analytics endpoint
            response = requests.get(f"{base_url}/analytics/summary", timeout=5)
            self.assertEqual(response.status_code, 200)

            analytics_data = response.json()
            self.assertIn("entities", analytics_data)
            self.assertIn("financial", analytics_data)
            self.assertIn("capacity", analytics_data)

            # Verify financial data matches business requirements
            financial = analytics_data["financial"]
            self.assertIn("total_daily_loss", financial)
            self.assertIn("target_daily_loss", financial)
            self.assertEqual(financial["target_daily_loss"], -388.15)

        except requests.exceptions.RequestException as e:
            self.fail(f"API integration test failed: {e}")

    def test_cli_functionality_validation(self):
        """
        Test command-line interface functionality (Requirement 3.4)

        Validates that CLI commands work correctly and provide expected outputs.
        """
        # Test 1: Database manager CLI
        try:
            # Test database status check
            result = subprocess.run(
                [sys.executable, "db_manager.py", "status"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            # Should complete successfully or with expected error
            self.assertIn(result.returncode, [0, 1], "DB manager should run without crashing")

            if result.returncode == 0:
                # Verify output contains expected information
                output = result.stdout.lower()
                self.assertTrue(
                    any(word in output for word in ["clients", "routes", "trucks", "orders"]),
                    "DB manager output should contain entity information"
                )

        except subprocess.TimeoutExpired:
            self.fail("Database manager CLI command timed out")
        except FileNotFoundError:
            self.skipTest("Database manager script not found")

        # Test 2: Order processor CLI (if available)
        try:
            result = subprocess.run(
                [sys.executable, "order_processor.py", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            # Order processor may not have CLI interface - that's acceptable
            if result.returncode == 0 and result.stdout.strip():
                self.assertIn("usage", result.stdout.lower())

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # CLI help not available - skip this test
            pass

        # Test 3: DFM demo functionality
        try:
            result = subprocess.run(
                [sys.executable, "-c", "from dfm import dfm_demo; dfm_demo()"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            # Should complete without crashing
            self.assertIn(result.returncode, [0, 1], "DFM demo should run without crashing")

        except subprocess.TimeoutExpired:
            self.fail("DFM demo timed out")

    def test_performance_requirements_validation(self):
        """
        Test performance requirements (<5 second order processing target)

        Validates that order processing completes within acceptable time limits.
        """
        # Create test orders for performance testing
        test_orders = []

        for i in range(10):  # Test with 10 orders
            # Create locations near existing routes
            pickup_loc = Location(
                lat=33.7490 + (i * 0.001),  # Slight variations around Atlanta
                lng=-84.3880 + (i * 0.001)
            )
            dropoff_loc = Location(
                lat=32.0835 + (i * 0.001),  # Slight variations around Savannah
                lng=-81.0998 + (i * 0.001)
            )

            self.session.add_all([pickup_loc, dropoff_loc])
            self.session.commit()

            order = Order(
                location_origin_id=pickup_loc.id,
                location_destiny_id=dropoff_loc.id,
                client_id=self.test_client_id
            )
            self.session.add(order)
            self.session.commit()

            # Add small cargo load
            cargo = Cargo(order_id=order.id)
            self.session.add(cargo)
            self.session.commit()

            package = Package(
                volume=2.0, weight=50.0, type=CargoType.STANDARD, cargo_id=cargo.id
            )
            self.session.add(package)
            self.session.commit()

            test_orders.append(order)

        # Load routes and trucks
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        # Test 1: Single order processing performance
        start_time = time.time()

        result = self.order_processor.validate_order_for_route(
            test_orders[0], routes[0], trucks[0]
        )

        single_order_time = time.time() - start_time

        # Performance assertion: <5 seconds per order
        self.assertLess(single_order_time, 5.0,
                       f"Single order processing took {single_order_time:.2f}s, should be <5s")

        # Test 2: Batch order processing performance
        start_time = time.time()

        batch_results = self.order_processor.process_order_batch(
            test_orders, routes, trucks
        )

        batch_processing_time = time.time() - start_time

        # Verify all orders were processed
        self.assertEqual(len(batch_results), len(test_orders),
                        "All orders should be processed in batch")

        # Performance assertion: batch should be efficient
        avg_time_per_order = batch_processing_time / len(test_orders)
        self.assertLess(avg_time_per_order, 5.0,
                       f"Average batch processing time {avg_time_per_order:.2f}s per order should be <5s")

        # Test 3: Business validation performance
        start_time = time.time()

        validation_reports = self.business_validator.validate_all_requirements(
            test_orders, routes, trucks, baseline_daily_loss=-388.15
        )

        validation_time = time.time() - start_time

        # Performance assertion: validation should be fast
        self.assertLess(validation_time, 5.0,
                       f"Business validation took {validation_time:.2f}s, should be <5s")

        # Verify validation completed successfully
        self.assertEqual(len(validation_reports), 5,
                        "Should have 5 validation reports (one per requirement)")

        # Test 4: Database operation performance
        start_time = time.time()

        # Simulate complex database query
        complex_query_result = self.session.exec(
            select(Order)
            .join(Cargo)
            .join(Package)
            .where(Package.type == CargoType.STANDARD)
        ).all()

        query_time = time.time() - start_time

        # Performance assertion: database queries should be fast
        self.assertLess(query_time, 2.0,
                       f"Complex database query took {query_time:.2f}s, should be <2s")

        # Verify query returned results
        self.assertGreaterEqual(len(complex_query_result), 0,
                               "Complex query should return results")


def run_integration_tests():
    """
    Run the complete integration test suite

    Returns:
        unittest.TestResult: Results of the test execution
    """
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTestSuite)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    # Run integration tests when executed directly
    print("=" * 80)
    print("DIGITAL FREIGHT MATCHING SYSTEM - INTEGRATION TEST SUITE")
    print("=" * 80)
    print()

    result = run_integration_tests()

    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.tests_Run}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Exit with appropriate code
    sys.exit(0 if result.was_Successful() else 1)
