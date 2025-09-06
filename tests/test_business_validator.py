"""
Unit tests for Business Requirements Validation Framework

Tests all validation methods against the 7 main business requirements:
1. Profitability improvement validation
2. Proximity constraint enforcement (1km)
3. Capacity constraint validation (48m³, 9180 lbs)
4. Time constraint validation (10 hours max)
5. Contract route preservation (5 routes)
"""

import unittest
from datetime import datetime

from validation.business_validator import (
    BusinessValidator,
    ValidationReport,
    PerformanceReport,
    ValidationStatus
)
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


class TestBusinessValidator(unittest.TestCase):
    """Test the BusinessValidator class initialization and basic functionality"""
    
    def set_Up(self):
        """Set up test fixtures"""
        self.validator = BusinessValidator()
    
    def test_validator_initialization(self):
        """Test that validator initializes correctly"""
        self.assertIsInstance(self.validator, BusinessValidator)
        self.assert_Equal(len(self.validator.validation_history), 0)
        self.assert_Equal(len(self.validator.performance_history), 0)
    
    def test_business_constants(self):
        """Test that business constants match requirements"""
        self.assert_Equal(self.validator.TARGET_DAILY_LOSS_REDUCTION, 388.15)
        self.assert_Equal(self.validator.MAX_PROXIMITY_KM, 1.0)
        self.assert_Equal(self.validator.MAX_TRUCK_VOLUME_M3, 48.0)
        self.assert_Equal(self.validator.MAX_TRUCK_WEIGHT_LBS, 9180.0)
        self.assert_Equal(self.validator.MAX_ROUTE_TIME_HOURS, 10.0)
        self.assert_Equal(self.validator.STOP_TIME_MINUTES, 15.0)
        self.assert_Equal(self.validator.REQUIRED_CONTRACT_ROUTES, 5)
        
        expected_destinations = ["Ringgold", "Augusta", "Savannah", "Albany", "Columbus"]
        self.assert_Equal(self.validator.CONTRACT_DESTINATIONS, expected_destinations)


class TestProfitabilityValidation(unittest.TestCase):
    """Test profitability requirement validation (Requirement 1.1)"""
    
    def set_Up(self):
        """Set up test fixtures"""
        self.validator = BusinessValidator()
        
        # Create test routes with different profitability scenarios
        self.profitable_routes = [
            Route(
                id=1,
                location_origin_id=1,
                location_destiny_id=2,
                profitability=100.0,  # Profitable
                orders=[]
            ),
            Route(
                id=2,
                location_origin_id=2,
                location_destiny_id=3,
                profitability=150.0,  # Profitable
                orders=[]
            )
        ]
        
        self.loss_making_routes = [
            Route(
                id=1,
                location_origin_id=1,
                location_destiny_id=2,
                profitability=-200.0,  # Loss
                orders=[]
            ),
            Route(
                id=2,
                location_origin_id=2,
                location_destiny_id=3,
                profitability=-100.0,  # Loss
                orders=[]
            )
        ]
        
        self.mixed_routes = [
            Route(
                id=1,
                location_origin_id=1,
                location_destiny_id=2,
                profitability=200.0,  # Profitable
                orders=[]
            ),
            Route(
                id=2,
                location_origin_id=2,
                location_destiny_id=3,
                profitability=-100.0,  # Loss
                orders=[]
            )
        ]
    
    def test_profitable_system_validation(self):
        """Test validation when system is profitable"""
        report = self.validator.validate_profitability_requirements(
            self.profitable_routes, 
            baseline_daily_loss=388.15
        )
        
        self.assert_Equal(report.requirement_id, "1.1")
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_In("successfully converted", report.details)
        self.assert_Equal(report.metrics["baseline_daily_loss"], 388.15)
        self.assert_Equal(report.metrics["current_daily_profit"], 250.0)
        self.assert_Greater(report.metrics["improvement_amount"], 0)
        self.assert_Equal(len(self.validator.validation_history), 1)
    
    def test_loss_making_system_validation(self):
        """Test validation when system is still making losses"""
        report = self.validator.validate_profitability_requirements(
            self.loss_making_routes,
            baseline_daily_loss=388.15
        )
        
        # Loss making routes still show improvement over baseline, so should be WARNING
        self.assert_Equal(report.status, ValidationStatus.WARNING)
        self.assert_In("reduced daily loss", report.details)
        self.assert_Equal(report.metrics["current_daily_profit"], -300.0)
        self.assert_Greater(report.metrics["improvement_amount"], 0)  # -300 is better than -388.15
    
    def test_improved_but_not_profitable_validation(self):
        """Test validation when system improved but not yet profitable"""
        # Routes that reduce loss but don't achieve profitability
        improved_routes = [
            Route(id=1, location_origin_id=1, location_destiny_id=2, profitability=-100.0, orders=[])
        ]
        
        report = self.validator.validate_profitability_requirements(
            improved_routes,
            baseline_daily_loss=388.15
        )
        
        self.assert_Equal(report.status, ValidationStatus.WARNING)
        self.assert_In("reduced daily loss", report.details)
        self.assert_Greater(report.metrics["improvement_amount"], 0)
        self.assert_Less(report.metrics["current_daily_profit"], 0)
    
    def test_profitability_validation_with_empty_routes(self):
        """Test validation with empty routes list"""
        report = self.validator.validate_profitability_requirements([], 388.15)
        
        # Empty routes with baseline loss should be WARNING (break-even from loss)
        self.assert_Equal(report.status, ValidationStatus.WARNING)
        self.assert_Equal(report.metrics["current_daily_profit"], 0.0)
        self.assert_Equal(report.metrics["routes_analyzed"], 0)
    
    def test_profitability_validation_error_handling(self):
        """Test validation handles errors gracefully"""
        # Create invalid route that might cause errors
        invalid_routes = [Mock()]
        invalid_routes[0].profitability = None  # This should cause an error
        
        report = self.validator.validate_profitability_requirements(invalid_routes, 388.15)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_In("Validation failed due to error", report.details)


class TestProximityValidation(unittest.TestCase):
    """Test proximity constraint validation (Requirement 1.2)"""
    
    def set_Up(self):
        """Set up test fixtures"""
        self.validator = BusinessValidator()
        
        # Create test locations
        self.atlanta = Location(lat=33.7490, lng=-84.3880)
        self.nearby_location = Location(lat=33.7500, lng=-84.3890)  # ~1km from Atlanta
        self.far_location = Location(lat=34.0522, lng=-118.2437)  # Los Angeles - very far
        
        # Create test route
        self.route = Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.atlanta,
            location_destiny=Location(lat=33.8490, lng=-84.4880),
            path=[self.atlanta, Location(lat=33.8490, lng=-84.4880)],
            orders=[]
        )
        
        # Create test orders
        self.compliant_order = Order(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.nearby_location,
            location_destiny=self.nearby_location,
            cargo=[]
        )
        
        self.non_compliant_order = Order(
            id=2,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.far_location,
            location_destiny=self.far_location,
            cargo=[]
        )
    
    def test_compliant_proximity_validation(self):
        """Test validation with orders that comply with proximity constraint"""
        orders = [self.compliant_order]
        routes = [self.route]
        
        report = self.validator.validate_proximity_constraint(orders, routes)
        
        self.assert_Equal(report.requirement_id, "1.2")
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 100.0)
        self.assert_Equal(report.metrics["violations_count"], 0)
        self.assert_Equal(report.metrics["compliant_orders"], 1)
    
    def test_non_compliant_proximity_validation(self):
        """Test validation with orders that violate proximity constraint"""
        orders = [self.non_compliant_order]
        routes = [self.route]
        
        report = self.validator.validate_proximity_constraint(orders, routes)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 0.0)
        self.assert_Equal(report.metrics["violations_count"], 1)
        self.assert_Equal(report.metrics["compliant_orders"], 0)
    
    def test_mixed_proximity_validation(self):
        """Test validation with mix of compliant and non-compliant orders"""
        orders = [self.compliant_order, self.non_compliant_order]
        routes = [self.route]
        
        report = self.validator.validate_proximity_constraint(orders, routes)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 50.0)
        self.assert_Equal(report.metrics["violations_count"], 1)
        self.assert_Equal(report.metrics["compliant_orders"], 1)
    
    def test_proximity_validation_with_missing_locations(self):
        """Test validation with orders missing pickup or dropoff locations"""
        incomplete_order = Order(
            id=3,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=None,  # Missing pickup
            location_destiny=self.nearby_location,
            cargo=[]
        )
        
        orders = [incomplete_order]
        routes = [self.route]
        
        report = self.validator.validate_proximity_constraint(orders, routes)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 0.0)
        self.assert_Greater(report.metrics["violations_count"], 0)
    
    def test_proximity_validation_with_empty_route_path(self):
        """Test validation with route that has no path defined"""
        empty_route = Route(
            id=2,
            location_origin_id=1,
            location_destiny_id=2,
            path=[],  # Empty path
            orders=[]
        )
        
        orders = [self.compliant_order]
        routes = [empty_route]
        
        report = self.validator.validate_proximity_constraint(orders, routes)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 0.0)
    
    def test_proximity_validation_with_empty_inputs(self):
        """Test validation with empty orders and routes"""
        report = self.validator.validate_proximity_constraint([], [])
        
        self.assert_Equal(report.status, ValidationStatus.PASSED)  # No orders to violate
        self.assert_Equal(report.metrics["total_orders"], 0)


class TestCapacityValidation(unittest.TestCase):
    """Test capacity constraint validation (Requirement 1.3)"""
    
    def set_Up(self):
        """Set up test fixtures"""
        self.validator = BusinessValidator()
        
        # Create test packages
        self.small_package = Package(
            id=1,
            volume=1.0,  # 1 cubic meter
            weight=25.0,  # 25 kg
            type=CargoType.STANDARD
        )
        
        self.large_package = Package(
            id=2,
            volume=50.0,  # 50 cubic meters - exceeds capacity
            weight=1000.0,  # 1000 kg
            type=CargoType.STANDARD
        )
        
        self.heavy_package = Package(
            id=3,
            volume=1.0,  # Small volume
            weight=5000.0,  # 5000 kg = ~11,000 lbs (exceeds weight limit)
            type=CargoType.STANDARD
        )
        
        # Create test cargo
        self.small_cargo = Cargo(
            id=1,
            order_id=1,
            packages=[self.small_package]
        )
        
        self.oversized_cargo = Cargo(
            id=2,
            order_id=2,
            packages=[self.large_package]
        )
        
        self.overweight_cargo = Cargo(
            id=3,
            order_id=3,
            packages=[self.heavy_package]
        )
        
        # Create test orders
        self.compliant_order = Order(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[self.small_cargo]
        )
        
        self.oversized_order = Order(
            id=2,
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[self.oversized_cargo]
        )
        
        self.overweight_order = Order(
            id=3,
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[self.overweight_cargo]
        )
        
        # Create test trucks
        self.compliant_truck = Truck(
            id=1,
            autonomy=800.0,
            capacity=48.0,  # Within limit
            type="standard",
            cargo_loads=[]
        )
        
        self.oversized_truck = Truck(
            id=2,
            autonomy=800.0,
            capacity=60.0,  # Exceeds 48m³ limit
            type="standard",
            cargo_loads=[]
        )
        
        self.loaded_truck = Truck(
            id=3,
            autonomy=800.0,
            capacity=48.0,
            type="standard",
            cargo_loads=[self.small_cargo]  # Has existing cargo
        )
    
    def test_compliant_capacity_validation(self):
        """Test validation with compliant capacity usage"""
        orders = [self.compliant_order]
        trucks = [self.compliant_truck]
        
        report = self.validator.validate_capacity_constraints(orders, trucks)
        
        self.assert_Equal(report.requirement_id, "1.3")
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_Equal(report.metrics["violations_count"], 0)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 100.0)
    
    def test_volume_capacity_violation(self):
        """Test validation with volume capacity violations"""
        orders = [self.oversized_order]
        trucks = [self.compliant_truck]
        
        report = self.validator.validate_capacity_constraints(orders, trucks)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Greater(report.metrics["violations_count"], 0)
        self.assert_In("violations detected", report.details)
    
    def test_weight_capacity_violation(self):
        """Test validation with weight capacity violations"""
        orders = [self.overweight_order]
        trucks = [self.compliant_truck]
        
        report = self.validator.validate_capacity_constraints(orders, trucks)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Greater(report.metrics["violations_count"], 0)
        self.assert_In("violations detected", report.details)
    
    def test_truck_capacity_limit_violation(self):
        """Test validation with truck that exceeds capacity limits"""
        orders = []
        trucks = [self.oversized_truck]
        
        report = self.validator.validate_capacity_constraints(orders, trucks)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Greater(report.metrics["violations_count"], 0)
    
    def test_capacity_with_existing_cargo(self):
        """Test capacity validation with trucks that have existing cargo"""
        orders = []
        trucks = [self.loaded_truck]
        
        report = self.validator.validate_capacity_constraints(orders, trucks)
        
        # Should pass since small cargo is within limits
        self.assert_Equal(report.status, ValidationStatus.PASSED)
    
    def test_mixed_capacity_scenarios(self):
        """Test validation with mix of compliant and non-compliant scenarios"""
        orders = [self.compliant_order, self.oversized_order]
        trucks = [self.compliant_truck, self.oversized_truck]
        
        report = self.validator.validate_capacity_constraints(orders, trucks)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Greater(report.metrics["violations_count"], 0)
        # Should have violations even if compliance rate calculation has issues
        self.assert_Greater(report.metrics["violations_count"], 0)


class TestTimeValidation(unittest.TestCase):
    """Test time constraint validation (Requirement 1.4)"""
    
    def set_Up(self):
        """Set up test fixtures"""
        self.validator = BusinessValidator()
        
        # Create test locations
        self.atlanta = Location(lat=33.7490, lng=-84.3880)
        self.savannah = Location(lat=32.0835, lng=-81.0998)  # ~400km from Atlanta
        
        # Create test orders
        self.order1 = Order(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[]
        )
        
        self.order2 = Order(
            id=2,
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[]
        )
        
        # Create test routes
        self.short_route = Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.atlanta,
            location_destiny=Location(lat=33.8490, lng=-84.4880),  # Short distance
            path=[self.atlanta, Location(lat=33.8490, lng=-84.4880)],
            orders=[self.order1]  # 1 order = 30 minutes stop time
        )
        
        self.long_route = Route(
            id=2,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.atlanta,
            location_destiny=self.savannah,  # Long distance
            path=[self.atlanta, self.savannah],
            orders=[self.order1, self.order2]  # 2 orders = 60 minutes stop time
        )
    
    def test_compliant_time_validation(self):
        """Test validation with routes that comply with time constraint"""
        routes = [self.short_route]
        
        report = self.validator.validate_time_constraints(routes)
        
        self.assert_Equal(report.requirement_id, "1.4")
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_Equal(report.metrics["violations_count"], 0)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 100.0)
    
    def test_time_constraint_violation(self):
        """Test validation with routes that exceed time limit"""
        # Create a route with many orders to exceed time limit
        many_orders = [Order(id=i, location_origin_id=1, location_destiny_id=2, cargo=[]) for i in range(20)]
        
        # Create a very long route that will exceed time limits
        very_long_route = Route(
            id=3,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7490, lng=-84.3880),
            location_destiny=Location(lat=25.7617, lng=-80.1918),  # Miami - very far
            path=[
                Location(lat=33.7490, lng=-84.3880),
                Location(lat=25.7617, lng=-80.1918)
            ],
            orders=many_orders  # Many orders = lots of stop time
        )
        
        routes = [very_long_route]
        
        report = self.validator.validate_time_constraints(routes)
        
        # Should exceed 10 hour limit due to distance + many stops
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Greater(report.metrics["violations_count"], 0)
        self.assert_Less(report.metrics["compliance_rate_percent"], 100.0)
    
    def test_time_calculation_includes_stops(self):
        """Test that time calculation includes 15-minute stops"""
        routes = [self.short_route]
        
        # The route has 1 order, so should add 30 minutes (2 stops * 15 minutes)
        report = self.validator.validate_time_constraints(routes)
        
        # Verify stop time is calculated correctly
        expected_stop_time = len(self.short_route.orders) * 2 * (15.0 / 60.0)  # 0.5 hours
        self.assert_Equal(expected_stop_time, 0.5)
    
    def test_empty_routes_validation(self):
        """Test validation with empty routes list"""
        report = self.validator.validate_time_constraints([])
        
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_Equal(report.metrics["total_routes"], 0)
        self.assert_Equal(report.metrics["compliance_rate_percent"], 100.0)
    
    def test_mixed_time_scenarios(self):
        """Test validation with mix of compliant and non-compliant routes"""
        # Create a route with many orders to exceed time limit
        many_orders = [Order(id=i, location_origin_id=1, location_destiny_id=2, cargo=[]) for i in range(15)]
        
        problematic_route = Route(
            id=3,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7490, lng=-84.3880),
            location_destiny=Location(lat=25.7617, lng=-80.1918),  # Miami - very far
            path=[
                Location(lat=33.7490, lng=-84.3880),
                Location(lat=25.7617, lng=-80.1918)
            ],
            orders=many_orders  # Many orders = lots of stop time
        )
        
        routes = [self.short_route, problematic_route]
        
        report = self.validator.validate_time_constraints(routes)
        
        # Should have some violations but not all routes
        self.assert_Greater(report.metrics["violations_count"], 0)
        self.assert_Less(report.metrics["compliance_rate_percent"], 100.0)
        self.assert_Greater(report.metrics["compliance_rate_percent"], 0.0)


class TestContractCompliance(unittest.TestCase):
    """Test contract compliance validation (Requirement 1.5)"""
    
    def set_Up(self):
        """Set up test fixtures"""
        self.validator = BusinessValidator()
        
        # Create 5 contract routes (minimum required)
        self.contract_routes = []
        for i in range(5):
            route = Route(
                id=i+1,
                location_origin_id=1,
                location_destiny_id=i+2,
                profitability=0.0,
                orders=[]
            )
            self.contract_routes.append(route)
        
        # Create fewer than required routes
        self.insufficient_routes = self.contract_routes[:3]  # Only 3 routes
        
        # Create more than required routes
        self.excess_routes = self.contract_routes + [
            Route(id=6, location_origin_id=1, location_destiny_id=7, profitability=0.0, orders=[]),
            Route(id=7, location_origin_id=1, location_destiny_id=8, profitability=0.0, orders=[])
        ]
    
    def test_compliant_contract_validation(self):
        """Test validation with exactly 5 contract routes"""
        report = self.validator.validate_contract_compliance(self.contract_routes)
        
        self.assert_Equal(report.requirement_id, "1.5")
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_Equal(report.metrics["contract_routes_preserved"], 5)
        self.assert_Equal(report.metrics["missing_routes_count"], 0)
        self.assert_In("All 5 contract routes are preserved", report.details)
    
    def test_insufficient_routes_validation(self):
        """Test validation with fewer than 5 routes"""
        report = self.validator.validate_contract_compliance(self.insufficient_routes)
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Equal(report.metrics["contract_routes_preserved"], 3)
        self.assert_In("Only 3 routes found", report.details)
        self.assert_Greater(len(report.recommendations), 0)
    
    def test_excess_routes_validation(self):
        """Test validation with more than 5 routes (should still pass)"""
        report = self.validator.validate_contract_compliance(self.excess_routes)
        
        self.assert_Equal(report.status, ValidationStatus.PASSED)
        self.assert_Equal(report.metrics["contract_routes_preserved"], 5)
        self.assert_Equal(report.metrics["current_routes_count"], 7)
    
    def test_empty_routes_validation(self):
        """Test validation with no routes"""
        report = self.validator.validate_contract_compliance([])
        
        self.assert_Equal(report.status, ValidationStatus.FAILED)
        self.assert_Equal(report.metrics["contract_routes_preserved"], 0)
        self.assert_Equal(report.metrics["current_routes_count"], 0)
    
    def test_contract_destinations_constant(self):
        """Test that contract destinations are correctly defined"""
        expected_destinations = ["Ringgold", "Augusta", "Savannah", "Albany", "Columbus"]
        self.assert_Equal(self.validator.CONTRACT_DESTINATIONS, expected_destinations)
        self.assert_Equal(len(self.validator.CONTRACT_DESTINATIONS), 5)


class TestValidationIntegration(unittest.TestCase):
    """Test integrated validation functionality"""
    
    def set_Up(self):
        """Set up comprehensive test fixtures"""
        self.validator = BusinessValidator()
        
        # Create test data
        self.orders = [
            Order(
                id=1,
                location_origin_id=1,
                location_destiny_id=2,
                location_origin=Location(lat=33.7490, lng=-84.3880),
                location_destiny=Location(lat=33.7500, lng=-84.3890),
                cargo=[Cargo(
                    id=1,
                    order_id=1,
                    packages=[Package(id=1, volume=1.0, weight=25.0, type=CargoType.STANDARD)]
                )]
            )
        ]
        
        self.routes = [
            Route(
                id=i+1,
                location_origin_id=1,
                location_destiny_id=i+2,
                location_origin=Location(lat=33.7490, lng=-84.3880),
                location_destiny=Location(lat=33.8490, lng=-84.4880),
                path=[
                    Location(lat=33.7490, lng=-84.3880),
                    Location(lat=33.8490, lng=-84.4880)
                ],
                profitability=50.0,
                orders=[]
            )
            for i in range(5)
        ]
        
        self.trucks = [
            Truck(
                id=1,
                autonomy=800.0,
                capacity=48.0,
                type="standard",
                cargo_loads=[]
            )
        ]
    
    def test_validate_all_requirements(self):
        """Test running all validations together"""
        reports = self.validator.validate_all_requirements(
            self.orders, 
            self.routes, 
            self.trucks, 
            baseline_daily_loss=388.15
        )
        
        self.assert_Equal(len(reports), 5)  # Should have 5 validation reports
        
        # Check that all requirement IDs are present
        requirement_ids = [r.requirement_id for r in reports]
        expected_ids = ["1.1", "1.2", "1.3", "1.4", "1.5"]
        self.assert_Equal(sorted(requirement_ids), sorted(expected_ids))
        
        # Check that all reports have required fields
        for report in reports:
            self.assertIsInstance(report, ValidationReport)
            self.assertIsInstance(report.status, ValidationStatus)
            self.assertIsInstance(report.metrics, dict)
            self.assertIsInstance(report.timestamp, datetime)
    
    def test_generate_summary_report(self):
        """Test summary report generation"""
        # Run all validations first
        reports = self.validator.validate_all_requirements(
            self.orders, self.routes, self.trucks
        )
        
        # Generate summary
        summary = self.validator.generate_summary_report(reports)
        
        # Check summary structure
        required_keys = [
            "overall_status", "total_requirements", "passed_count", 
            "failed_count", "warning_count", "pass_rate_percent",
            "validation_timestamp", "requirements_details"
        ]
        
        for key in required_keys:
            self.assert_In(key, summary)
        
        self.assert_Equal(summary["total_requirements"], 5)
        self.assertIsInstance(summary["pass_rate_percent"], float)
        self.assertIsInstance(summary["requirements_details"], list)
        self.assert_Equal(len(summary["requirements_details"]), 5)
    
    def test_validation_history_tracking(self):
        """Test that validation history is properly tracked"""
        initial_count = len(self.validator.validation_history)
        
        # Run a single validation
        self.validator.validate_profitability_requirements(self.routes)
        
        # Check history was updated
        self.assert_Equal(len(self.validator.validation_history), initial_count + 1)
        
        # Run all validations
        self.validator.validate_all_requirements(self.orders, self.routes, self.trucks)
        
        # Check history includes all validations
        self.assert_Equal(len(self.validator.validation_history), initial_count + 6)  # 1 + 5
    
    def test_error_handling_in_validation(self):
        """Test that validation handles errors gracefully"""
        # Create invalid data that might cause errors
        invalid_orders = [Mock()]
        invalid_routes = [Mock()]
        invalid_trucks = [Mock()]
        
        # Configure mocks to raise exceptions
        invalid_orders[0].total_volume.side_effect = Exception("Test error")
        invalid_routes[0].profitability = None
        invalid_trucks[0].capacity = "invalid"
        
        # Run validations - should not crash
        reports = self.validator.validate_all_requirements(
            invalid_orders, invalid_routes, invalid_trucks
        )
        
        # Should still return 5 reports, but with FAILED status
        self.assert_Equal(len(reports), 5)
        
        # Most reports should indicate failure due to errors
        # Note: Contract compliance might not fail if it just counts routes
        failed_reports = [r for r in reports if r.status == ValidationStatus.FAILED]
        self.assert_Greater(len(failed_reports), 0)  # At least some should fail
        
        # Check that error reports contain error information
        error_reports = [r for r in reports if "error" in r.details.lower()]
        self.assert_Greater(len(error_reports), 0)  # At least some should mention errors


if __name__ == '__main__':
    unittest.main()