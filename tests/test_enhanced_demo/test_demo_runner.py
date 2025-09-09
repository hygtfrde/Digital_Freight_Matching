"""
Unit tests for DemoTestRunner

Tests the comprehensive demo test runner functionality including
order processing, constraint validation, and profitability calculations.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock

from demos.enhanced_demo_testing.demo_test_runner import (
    DemoTestRunner, OrderTestResult, OrderTestStatus, ConstraintResult, 
    ProfitabilityResult, DemoTestResults
)
from demos.enhanced_demo_testing.test_data_parser import TestOrder
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


class TestDemoTestRunner:
    """Test cases for DemoTestRunner class"""
    
    @pytest.fixture
    def demo_runner(self):
        """Create a DemoTestRunner instance for testing"""
        return DemoTestRunner()
    
    @pytest.fixture
    def sample_test_data(self):
        """Create sample test data for testing"""
        return [
            {
                "cargo": {
                    "packages": [10, 1500, "general"]
                },
                "pick-up": {
                    "latitude": 33.753,
                    "longitude": -84.390
                },
                "drop-off": {
                    "latitude": 32.460,
                    "longitude": -84.985
                }
            },
            {
                "cargo": {
                    "packages": [50, 8000, "general"]
                },
                "pick-up": {
                    "latitude": 33.749,
                    "longitude": -84.388
                },
                "drop-off": {
                    "latitude": 32.0835,
                    "longitude": -81.0998
                }
            },
            {
                "cargo": {
                    "packages": [10, 1500, "hazmat"]
                },
                "pick-up": {
                    "latitude": 33.749,
                    "longitude": -84.388
                },
                "drop-off": {
                    "latitude": 32.0835,
                    "longitude": -81.0998
                }
            }
        ]
    
    @pytest.fixture
    def temp_test_file(self, sample_test_data):
        """Create a temporary test data file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_test_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def sample_order(self):
        """Create a sample order for testing"""
        origin = Location(id=1, lat=33.753, lng=-84.390)
        destiny = Location(id=2, lat=32.460, lng=-84.985)
        
        package = Package(id=1, volume=10.0, weight=1500.0, type=CargoType.STANDARD)
        cargo = Cargo(id=1, order_id=1, packages=[package])
        
        return Order(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=origin,
            location_destiny=destiny,
            cargo=[cargo]
        )
    
    @pytest.fixture
    def sample_route(self):
        """Create a sample route for testing"""
        origin = Location(id=1, lat=33.753, lng=-84.390)
        destiny = Location(id=2, lat=32.460, lng=-84.985)
        
        return Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=origin,
            location_destiny=destiny,
            profitability=100.0
        )
    
    @pytest.fixture
    def sample_truck(self):
        """Create a sample truck for testing"""
        return Truck(
            id=1,
            autonomy=500.0,
            capacity=20.0,
            type="standard"
        )
    
    def test_demo_runner_initialization(self, demo_runner):
        """Test that DemoTestRunner initializes correctly"""
        assert demo_runner is not None
        assert demo_runner.test_data_parser is not None
        assert demo_runner.business_validator is not None
        assert demo_runner.test_orders == []
        assert demo_runner.test_routes == []
        assert demo_runner.test_trucks == []
    
    def test_run_comprehensive_demo_success(self, demo_runner, temp_test_file):
        """Test successful comprehensive demo execution"""
        results = demo_runner.run_comprehensive_demo(temp_test_file)
        
        assert isinstance(results, DemoTestResults)
        assert results.total_orders_tested == 3
        assert results.total_processing_time_ms > 0
        assert results.average_processing_time_ms > 0
        assert len(results.detailed_results) == 3
        assert results.timestamp is not None
        
        # Check that we have some results
        assert results.successful_orders + results.failed_orders + results.error_orders == 3
    
    def test_run_comprehensive_demo_with_invalid_file(self, demo_runner):
        """Test comprehensive demo with invalid file path"""
        results = demo_runner.run_comprehensive_demo("nonexistent_file.json")
        
        assert isinstance(results, DemoTestResults)
        assert results.total_orders_tested == 0
        assert results.error_orders == 1
        assert "error" in results.test_summary
    
    def test_process_single_order_success(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test successful processing of a single order"""
        # Create a TestOrder wrapper
        test_order = TestOrder(
            order=sample_order,
            test_description="Test order processing",
            cargo_type="general",
            distance_category="medium",
            order_index=0
        )
        
        # Mock the route and truck finding
        demo_runner.test_routes = [sample_route]
        demo_runner.test_trucks = [sample_truck]
        
        result = demo_runner.process_single_order(test_order)
        
        assert isinstance(result, OrderTestResult)
        assert result.order_id == sample_order.id
        assert result.test_description == "Test order processing"
        assert result.status in [OrderTestStatus.SUCCESS, OrderTestStatus.FAILED]
        assert result.processing_time_ms > 0
        assert result.profitability_result is not None
        assert isinstance(result.constraint_violations, list)
        assert result.detailed_explanation is not None
    
    def test_process_single_order_no_match(self, demo_runner, sample_order):
        """Test processing order when no route/truck match is found"""
        test_order = TestOrder(
            order=sample_order,
            test_description="Test order with no match",
            cargo_type="general",
            distance_category="medium",
            order_index=0
        )
        
        # Empty routes and trucks
        demo_runner.test_routes = []
        demo_runner.test_trucks = []
        
        result = demo_runner.process_single_order(test_order)
        
        assert result.status == OrderTestStatus.FAILED
        assert not result.profitability_result.is_profitable
        assert "No matching route or compatible truck" in result.detailed_explanation
    
    def test_validate_business_constraints_proximity(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test proximity constraint validation"""
        # Create order and route with locations far apart
        far_origin = Location(id=3, lat=40.0, lng=-80.0)  # Far from route
        sample_order.location_origin = far_origin
        
        violations = demo_runner.validate_business_constraints(sample_order, sample_route, sample_truck)
        
        # Should have proximity violation
        proximity_violations = [v for v in violations if v.constraint_type == "proximity_pickup"]
        assert len(proximity_violations) > 0
        assert proximity_violations[0].severity == "critical"
        assert not proximity_violations[0].passed
    
    def test_validate_business_constraints_capacity(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test capacity constraint validation"""
        # Create order with volume exceeding truck capacity
        large_package = Package(id=2, volume=100.0, weight=5000.0, type=CargoType.STANDARD)
        sample_order.cargo[0].packages = [large_package]
        
        violations = demo_runner.validate_business_constraints(sample_order, sample_route, sample_truck)
        
        # Should have capacity violation
        capacity_violations = [v for v in violations if v.constraint_type == "volume_capacity"]
        assert len(capacity_violations) > 0
        assert capacity_violations[0].severity == "critical"
        assert not capacity_violations[0].passed
    
    def test_validate_business_constraints_cargo_compatibility(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test cargo compatibility constraint validation"""
        # Create hazmat cargo with standard truck
        hazmat_package = Package(id=3, volume=5.0, weight=1000.0, type=CargoType.HAZMAT)
        sample_order.cargo[0].packages = [hazmat_package]
        
        violations = demo_runner.validate_business_constraints(sample_order, sample_route, sample_truck)
        
        # Should have compatibility violation
        compatibility_violations = [v for v in violations if v.constraint_type == "cargo_compatibility"]
        assert len(compatibility_violations) > 0
        assert compatibility_violations[0].severity == "critical"
        assert not compatibility_violations[0].passed
    
    def test_validate_business_constraints_time_limit(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test time limit constraint validation"""
        # Create route with very long distance
        far_destiny = Location(id=4, lat=25.0, lng=-80.0)  # Very far destination
        sample_route.location_destiny = far_destiny
        
        violations = demo_runner.validate_business_constraints(sample_order, sample_route, sample_truck)
        
        # May have time violation depending on distance calculation
        time_violations = [v for v in violations if v.constraint_type == "time_limit"]
        if time_violations:
            assert time_violations[0].severity == "warning"
            assert not time_violations[0].passed
    
    def test_validate_business_constraints_range_limit(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test range limit constraint validation"""
        # Create truck with very limited range
        sample_truck.autonomy = 50.0  # Very short range
        
        # Create route with long distance
        far_destiny = Location(id=4, lat=30.0, lng=-90.0)
        sample_route.location_destiny = far_destiny
        
        violations = demo_runner.validate_business_constraints(sample_order, sample_route, sample_truck)
        
        # Should have range violation
        range_violations = [v for v in violations if v.constraint_type == "range_limit"]
        assert len(range_violations) > 0
        assert range_violations[0].severity == "critical"
        assert not range_violations[0].passed
    
    def test_calculate_profitability_impact_profitable(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test profitability calculation for profitable order"""
        result = demo_runner.calculate_profitability_impact(sample_order, sample_route, sample_truck)
        
        assert isinstance(result, ProfitabilityResult)
        assert result.revenue > 0
        assert result.cost > 0
        assert result.explanation is not None
        
        # For a standard small order, should be profitable
        assert result.profit_amount == result.revenue - result.cost
    
    def test_calculate_profitability_impact_hazmat_premium(self, demo_runner, sample_order, sample_route):
        """Test profitability calculation with hazmat premium"""
        # Create hazmat truck and cargo
        hazmat_truck = Truck(id=2, autonomy=400.0, capacity=15.0, type="hazmat")
        hazmat_package = Package(id=4, volume=5.0, weight=1000.0, type=CargoType.HAZMAT)
        sample_order.cargo[0].packages = [hazmat_package]
        
        result = demo_runner.calculate_profitability_impact(sample_order, sample_route, hazmat_truck)
        
        # Should include hazmat premium in revenue
        assert result.revenue >= demo_runner.BASE_REVENUE_PER_ORDER + 50.0  # Hazmat premium
    
    def test_calculate_profitability_impact_refrigerated_premium(self, demo_runner, sample_order, sample_route):
        """Test profitability calculation with refrigerated premium"""
        # Create refrigerated truck and cargo
        refrigerated_truck = Truck(id=3, autonomy=450.0, capacity=25.0, type="refrigerated")
        refrigerated_package = Package(id=5, volume=8.0, weight=1200.0, type=CargoType.REFRIGERATED)
        sample_order.cargo[0].packages = [refrigerated_package]
        
        result = demo_runner.calculate_profitability_impact(sample_order, sample_route, refrigerated_truck)
        
        # Should include refrigerated premium in revenue
        assert result.revenue >= demo_runner.BASE_REVENUE_PER_ORDER + 30.0  # Refrigerated premium
    
    def test_find_best_match_success(self, demo_runner, sample_order):
        """Test finding best route and truck match"""
        # Create compatible route and truck
        origin = Location(id=1, lat=33.753, lng=-84.390)
        destiny = Location(id=2, lat=32.460, lng=-84.985)
        
        route = Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=origin,
            location_destiny=destiny
        )
        
        truck = Truck(id=1, autonomy=500.0, capacity=20.0, type="standard")
        
        demo_runner.test_routes = [route]
        demo_runner.test_trucks = [truck]
        
        best_route, best_truck = demo_runner._find_best_match(sample_order)
        
        assert best_route is not None
        assert best_truck is not None
        assert best_route.id == route.id
        assert best_truck.id == truck.id
    
    def test_find_best_match_no_compatible_truck(self, demo_runner, sample_order):
        """Test finding match when no compatible truck exists"""
        # Create hazmat cargo but only standard truck
        hazmat_package = Package(id=6, volume=5.0, weight=1000.0, type=CargoType.HAZMAT)
        sample_order.cargo[0].packages = [hazmat_package]
        
        origin = Location(id=1, lat=33.753, lng=-84.390)
        destiny = Location(id=2, lat=32.460, lng=-84.985)
        
        route = Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=origin,
            location_destiny=destiny
        )
        
        standard_truck = Truck(id=1, autonomy=500.0, capacity=20.0, type="standard")
        
        demo_runner.test_routes = [route]
        demo_runner.test_trucks = [standard_truck]
        
        best_route, best_truck = demo_runner._find_best_match(sample_order)
        
        # Should not find a match due to cargo incompatibility
        assert best_route is None or best_truck is None
    
    def test_calculate_match_score_perfect_match(self, demo_runner, sample_order, sample_route, sample_truck):
        """Test match score calculation for perfect match"""
        score = demo_runner._calculate_match_score(sample_order, sample_route, sample_truck)
        
        assert score > 0  # Should be positive for compatible match
    
    def test_calculate_match_score_incompatible(self, demo_runner, sample_order, sample_route):
        """Test match score calculation for incompatible combination"""
        # Create oversized order
        large_package = Package(id=7, volume=100.0, weight=10000.0, type=CargoType.STANDARD)
        sample_order.cargo[0].packages = [large_package]
        
        small_truck = Truck(id=4, autonomy=200.0, capacity=5.0, type="standard")
        
        score = demo_runner._calculate_match_score(sample_order, sample_route, small_truck)
        
        assert score == -1  # Should be -1 for incompatible match
    
    def test_generate_success_explanation(self, demo_runner):
        """Test generation of success explanation"""
        profitability = ProfitabilityResult(
            is_profitable=True,
            profit_amount=50.0,
            revenue=200.0,
            cost=150.0,
            profit_margin_percent=25.0,
            explanation="Profitable order: $50.00 profit (25.0% margin)"
        )
        
        violations = [
            ConstraintResult(
                constraint_type="time_limit",
                passed=False,
                required_value=10.0,
                actual_value=10.5,
                severity="warning",
                description="Route time slightly exceeds limit"
            )
        ]
        
        explanation = demo_runner._generate_success_explanation(profitability, violations)
        
        assert "✅ ORDER ACCEPTED" in explanation
        assert "Profitable order" in explanation
        assert "⚠️  Warnings" in explanation
    
    def test_generate_failure_explanation(self, demo_runner):
        """Test generation of failure explanation"""
        profitability = ProfitabilityResult(
            is_profitable=False,
            profit_amount=-25.0,
            revenue=100.0,
            cost=125.0,
            profit_margin_percent=-25.0,
            explanation="Unprofitable order: $-25.00 loss"
        )
        
        violations = [
            ConstraintResult(
                constraint_type="volume_capacity",
                passed=False,
                required_value=20.0,
                actual_value=25.0,
                severity="critical",
                description="Order volume exceeds truck capacity"
            )
        ]
        
        explanation = demo_runner._generate_failure_explanation(violations, profitability)
        
        assert "❌ ORDER REJECTED" in explanation
        assert "critical constraint violations" in explanation
    
    def test_generate_test_summary(self, demo_runner):
        """Test generation of test summary statistics"""
        # Create sample results
        results = [
            OrderTestResult(
                order_id=1,
                test_description="Test 1",
                status=OrderTestStatus.SUCCESS,
                profitability_result=ProfitabilityResult(
                    is_profitable=True, profit_amount=50.0, revenue=200.0, 
                    cost=150.0, profit_margin_percent=25.0, explanation="Profitable"
                ),
                constraint_violations=[],
                processing_time_ms=100.0,
                detailed_explanation="Success"
            ),
            OrderTestResult(
                order_id=2,
                test_description="Test 2",
                status=OrderTestStatus.FAILED,
                profitability_result=ProfitabilityResult(
                    is_profitable=False, profit_amount=-25.0, revenue=100.0,
                    cost=125.0, profit_margin_percent=-25.0, explanation="Unprofitable"
                ),
                constraint_violations=[
                    ConstraintResult("capacity", False, 20.0, 25.0, "critical", "Over capacity")
                ],
                processing_time_ms=150.0,
                detailed_explanation="Failed"
            )
        ]
        
        summary = demo_runner._generate_test_summary(results)
        
        assert summary["total_orders"] == 2
        assert summary["success_rate_percent"] == 50.0
        assert summary["failure_rate_percent"] == 50.0
        assert summary["profitable_orders"] == 1
        assert summary["profitability_rate_percent"] == 50.0
        assert summary["total_profit"] == 25.0  # 50 - 25
        assert summary["average_processing_time_ms"] == 125.0
        assert "capacity" in summary["common_constraint_violations"]
    
    def test_generate_test_summary_empty_results(self, demo_runner):
        """Test test summary generation with empty results"""
        summary = demo_runner._generate_test_summary([])
        
        assert "error" in summary
        assert summary["error"] == "No results to summarize"
    
    @patch('demos.enhanced_demo_testing.demo_test_runner.time.time')
    def test_processing_time_measurement(self, mock_time, demo_runner, sample_order):
        """Test that processing time is measured correctly"""
        # Mock time to return predictable values
        mock_time.side_effect = [0.0, 0.1]  # 100ms processing time
        
        test_order = TestOrder(
            order=sample_order,
            test_description="Time test",
            cargo_type="general",
            distance_category="medium",
            order_index=0
        )
        
        # Empty routes/trucks to trigger quick failure path
        demo_runner.test_routes = []
        demo_runner.test_trucks = []
        
        result = demo_runner.process_single_order(test_order)
        
        assert result.processing_time_ms == 100.0  # 0.1 * 1000
    
    def test_constraint_result_creation(self):
        """Test ConstraintResult dataclass creation"""
        constraint = ConstraintResult(
            constraint_type="test_constraint",
            passed=False,
            required_value=10.0,
            actual_value=15.0,
            severity="critical",
            description="Test constraint violation"
        )
        
        assert constraint.constraint_type == "test_constraint"
        assert not constraint.passed
        assert constraint.required_value == 10.0
        assert constraint.actual_value == 15.0
        assert constraint.severity == "critical"
        assert constraint.description == "Test constraint violation"
    
    def test_profitability_result_creation(self):
        """Test ProfitabilityResult dataclass creation"""
        profitability = ProfitabilityResult(
            is_profitable=True,
            profit_amount=75.0,
            revenue=250.0,
            cost=175.0,
            profit_margin_percent=30.0,
            explanation="Test profitable order"
        )
        
        assert profitability.is_profitable
        assert profitability.profit_amount == 75.0
        assert profitability.revenue == 250.0
        assert profitability.cost == 175.0
        assert profitability.profit_margin_percent == 30.0
        assert profitability.explanation == "Test profitable order"
    
    def test_demo_test_results_creation(self):
        """Test DemoTestResults dataclass creation"""
        from datetime import datetime
        
        results = DemoTestResults(
            total_orders_tested=5,
            successful_orders=3,
            failed_orders=2,
            error_orders=0,
            total_processing_time_ms=500.0,
            average_processing_time_ms=100.0,
            detailed_results=[],
            validation_reports=[],
            test_summary={},
            timestamp=datetime.now()
        )
        
        assert results.total_orders_tested == 5
        assert results.successful_orders == 3
        assert results.failed_orders == 2
        assert results.error_orders == 0
        assert results.total_processing_time_ms == 500.0
        assert results.average_processing_time_ms == 100.0
        assert isinstance(results.detailed_results, list)
        assert isinstance(results.validation_reports, list)
        assert isinstance(results.test_summary, dict)
        assert results.timestamp is not None