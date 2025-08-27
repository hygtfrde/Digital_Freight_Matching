"""
Unit tests for Order Processing Engine

Tests all validation constraints and business rules:
- Proximity constraint validation (1km limit)
- Time calculation logic (15-minute stops + deviation)
- Capacity checking (volume CBM and weight pounds)
- Cargo compatibility validation
"""

import unittest
import math
from unittest.mock import Mock, patch

from order_processor import (
    OrderProcessor, 
    OrderProcessingConstants, 
    ValidationResult, 
    ValidationError, 
    ProcessingResult
)
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


class TestOrderProcessingConstants(unittest.TestCase):
    """Test that constants match documentation exactly"""
    
    def test_cost_constants(self):
        """Verify cost constants from documentation"""
        constants = OrderProcessingConstants()
        
        self.assertEqual(constants.TOTAL_COST_PER_MILE, 1.693846154)
        self.assertEqual(constants.TRUCKER_COST_PER_MILE, 0.78)
        self.assertEqual(constants.FUEL_COST_PER_MILE, 0.37)
        self.assertEqual(constants.LEASING_COST_PER_MILE, 0.27)
        self.assertEqual(constants.MAINTENANCE_COST_PER_MILE, 0.17)
        self.assertEqual(constants.INSURANCE_COST_PER_MILE, 0.1)
    
    def test_performance_constants(self):
        """Verify performance constants from documentation"""
        constants = OrderProcessingConstants()
        
        self.assertEqual(constants.MILES_PER_GALLON, 6.5)
        self.assertEqual(constants.GAS_PRICE, 2.43)
        self.assertEqual(constants.AVG_SPEED_MPH, 50)
    
    def test_cargo_constants(self):
        """Verify cargo constants from documentation"""
        constants = OrderProcessingConstants()
        
        self.assertEqual(constants.MAX_WEIGHT_LBS, 9180)
        self.assertEqual(constants.TOTAL_VOLUME_CUBIC_FEET, 1700)
        self.assertEqual(constants.PALLETS_PER_TRUCK, 26.6)
        self.assertEqual(constants.PALLET_COST_PER_MILE, 0.06376832579)
        self.assertEqual(constants.PALLET_WEIGHT_LBS, 440)
        self.assertEqual(constants.PALLET_VOLUME_CUBIC_FEET, 64)
    
    def test_business_rule_constants(self):
        """Verify business rule constants"""
        constants = OrderProcessingConstants()
        
        self.assertEqual(constants.MAX_PROXIMITY_KM, 1.0)
        self.assertEqual(constants.STOP_TIME_MINUTES, 15)
        self.assertEqual(constants.MAX_ROUTE_HOURS, 10.0)


class TestProximityValidation(unittest.TestCase):
    """Test 1km proximity constraint validation using haversine distance"""
    
    def setUp(self):
        self.processor = OrderProcessor()
        
        # Create test locations
        self.atlanta = Location(lat=33.7490, lng=-84.3880)  # Atlanta
        self.nearby_location = Location(lat=33.7500, lng=-84.3890)  # ~1km from Atlanta
        self.far_location = Location(lat=34.0522, lng=-118.2437)  # Los Angeles - very far
        
        # Create test route
        self.route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.atlanta,
            location_destiny=Location(lat=33.8490, lng=-84.4880),
            path=[self.atlanta, Location(lat=33.8490, lng=-84.4880)]
        )
    
    def test_valid_proximity(self):
        """Test order with locations within 1km of route"""
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.nearby_location,
            location_destiny=self.nearby_location
        )
        
        result = self.processor._validate_proximity_constraint(order, self.route)
        self.assertIsNone(result)
    
    def test_invalid_pickup_proximity(self):
        """Test order with pickup location too far from route"""
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.far_location,  # Too far
            location_destiny=self.nearby_location
        )
        
        result = self.processor._validate_proximity_constraint(order, self.route)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_PROXIMITY)
        self.assertIn("Pickup location too far", result.message)
        self.assertGreater(result.details['pickup_distance_km'], 1.0)
    
    def test_invalid_dropoff_proximity(self):
        """Test order with dropoff location too far from route"""
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.nearby_location,
            location_destiny=self.far_location  # Too far
        )
        
        result = self.processor._validate_proximity_constraint(order, self.route)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_PROXIMITY)
        self.assertIn("Dropoff location too far", result.message)
        self.assertGreater(result.details['dropoff_distance_km'], 1.0)
    
    def test_missing_locations(self):
        """Test order with missing pickup or dropoff locations"""
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=None,  # Missing
            location_destiny=self.nearby_location
        )
        
        result = self.processor._validate_proximity_constraint(order, self.route)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_PROXIMITY)
        self.assertIn("missing pickup or dropoff", result.message)
    
    def test_empty_route_path(self):
        """Test validation with route that has no defined path"""
        empty_route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            path=[]
        )
        
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.nearby_location,
            location_destiny=self.nearby_location
        )
        
        result = self.processor._validate_proximity_constraint(order, empty_route)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_PROXIMITY)
        self.assertIn("no defined path", result.message)


class TestCapacityValidation(unittest.TestCase):
    """Test capacity validation with volume (CBM) and weight (pounds)"""
    
    def setUp(self):
        self.processor = OrderProcessor()
        
        # Create test truck with standard capacity
        self.truck = Truck(
            autonomy=800.0,
            capacity=48.0,  # 48 cubic meters
            type="standard",
            cargo_loads=[]
        )
        
        # Create test packages
        self.small_package = Package(
            volume=1.0,  # 1 cubic meter
            weight=25.0,  # 25 kg
            type=CargoType.STANDARD
        )
        
        self.large_package = Package(
            volume=50.0,  # 50 cubic meters - exceeds truck capacity
            weight=1000.0,  # 1000 kg
            type=CargoType.STANDARD
        )
    
    def test_valid_capacity(self):
        """Test order that fits within truck capacity"""
        cargo = Cargo(order_id=1, packages=[self.small_package])
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[cargo]
        )
        
        result = self.processor._validate_capacity_constraint(order, self.truck)
        self.assertIsNone(result)
    
    def test_invalid_volume_capacity(self):
        """Test order that exceeds volume capacity"""
        cargo = Cargo(order_id=1, packages=[self.large_package])
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[cargo]
        )
        
        result = self.processor._validate_capacity_constraint(order, self.truck)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_CAPACITY)
        self.assertIn("Insufficient volume capacity", result.message)
    
    def test_invalid_weight_capacity(self):
        """Test order that exceeds weight capacity"""
        # Create very heavy package
        heavy_package = Package(
            volume=1.0,  # Small volume
            weight=5000.0,  # 5000 kg = ~11,000 lbs (exceeds 9,180 lbs limit)
            type=CargoType.STANDARD
        )
        
        cargo = Cargo(order_id=1, packages=[heavy_package])
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[cargo]
        )
        
        result = self.processor._validate_capacity_constraint(order, self.truck)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_WEIGHT)
        self.assertIn("Insufficient weight capacity", result.message)
    
    def test_capacity_with_existing_cargo(self):
        """Test capacity validation with existing cargo in truck"""
        # Add existing cargo to truck
        existing_cargo = Cargo(order_id=1, packages=[
            Package(volume=40.0, weight=1000.0, type=CargoType.STANDARD)
        ])
        self.truck.cargo_loads = [existing_cargo]
        
        # Try to add more cargo
        new_cargo = Cargo(order_id=2, packages=[
            Package(volume=10.0, weight=500.0, type=CargoType.STANDARD)  # Would exceed capacity
        ])
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[new_cargo]
        )
        
        result = self.processor._validate_capacity_constraint(order, self.truck)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INVALID_CAPACITY)


class TestTimeValidation(unittest.TestCase):
    """Test time calculation with 15-minute stops plus deviation time"""
    
    def setUp(self):
        self.processor = OrderProcessor()
        
        # Create test route with known time
        self.route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7490, lng=-84.3880),
            location_destiny=Location(lat=34.7490, lng=-85.3880),  # ~100km away
            path=[
                Location(lat=33.7490, lng=-84.3880),
                Location(lat=34.7490, lng=-85.3880)
            ]
        )
        
        self.order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7500, lng=-84.3890),
            location_destiny=Location(lat=34.7500, lng=-85.3890)
        )
    
    def test_valid_time_constraint(self):
        """Test order that doesn't exceed 10-hour limit"""
        result = self.processor._validate_time_constraint(self.order, self.route)
        # Should be valid for reasonable distances
        self.assertIsNone(result)
    
    def test_invalid_time_constraint(self):
        """Test order that would exceed 10-hour limit"""
        # Create a route that's already close to the limit
        long_route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7490, lng=-84.3880),
            location_destiny=Location(lat=40.7490, lng=-90.3880),  # Very far
            path=[
                Location(lat=33.7490, lng=-84.3880),
                Location(lat=40.7490, lng=-90.3880)
            ]
        )
        
        # Mock the Route class's total_time method to return close to limit
        with patch('schemas.schemas.Route.total_time', return_value=9.5):
            result = self.processor._validate_time_constraint(self.order, long_route)
            # Adding 30 minutes (2 stops) + deviation should exceed 10 hours
            self.assertIsNotNone(result)
            self.assertEqual(result.result, ValidationResult.INVALID_TIME)
            self.assertIn("exceed maximum time", result.message)
    
    def test_time_calculation_components(self):
        """Test that time calculation includes all components"""
        result = self.processor._validate_time_constraint(self.order, self.route)
        
        if result:  # If validation failed, check the details
            details = result.details
            self.assertIn('current_time_hours', details)
            self.assertIn('additional_stop_time_hours', details)
            self.assertIn('deviation_time_hours', details)
            self.assertIn('new_total_time_hours', details)
            
            # Verify 15-minute stops are included (2 stops = 30 minutes = 0.5 hours)
            self.assertEqual(details['additional_stop_time_hours'], 0.5)


class TestCargoCompatibility(unittest.TestCase):
    """Test cargo type compatibility validation"""
    
    def setUp(self):
        self.processor = OrderProcessor()
        
        # Create truck with existing hazmat cargo
        hazmat_package = Package(volume=1.0, weight=25.0, type=CargoType.HAZMAT)
        existing_cargo = Cargo(order_id=1, packages=[hazmat_package])
        
        self.truck = Truck(
            autonomy=800.0,
            capacity=48.0,
            type="standard",
            cargo_loads=[existing_cargo]
        )
    
    def test_compatible_cargo(self):
        """Test adding compatible cargo types"""
        # Standard cargo should be compatible with hazmat
        standard_package = Package(volume=1.0, weight=25.0, type=CargoType.STANDARD)
        new_cargo = Cargo(order_id=2, packages=[standard_package])
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[new_cargo]
        )
        
        result = self.processor._validate_cargo_compatibility(order, self.truck)
        self.assertIsNone(result)
    
    def test_incompatible_cargo(self):
        """Test adding incompatible cargo types"""
        # Fragile cargo should be incompatible with hazmat
        fragile_package = Package(volume=1.0, weight=25.0, type=CargoType.FRAGILE)
        new_cargo = Cargo(order_id=2, packages=[fragile_package])
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[new_cargo]
        )
        
        result = self.processor._validate_cargo_compatibility(order, self.truck)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, ValidationResult.INCOMPATIBLE_CARGO)
        self.assertIn("Incompatible cargo types", result.message)
    
    def test_empty_cargo(self):
        """Test order with no cargo"""
        order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            cargo=[]
        )
        
        result = self.processor._validate_cargo_compatibility(order, self.truck)
        self.assertIsNone(result)


class TestOrderMetrics(unittest.TestCase):
    """Test order metrics calculation"""
    
    def setUp(self):
        self.processor = OrderProcessor()
        
        self.truck = Truck(
            autonomy=800.0,
            capacity=48.0,
            type="standard",
            cargo_loads=[]
        )
        
        self.route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7490, lng=-84.3880),
            location_destiny=Location(lat=34.7490, lng=-85.3880),
            path=[
                Location(lat=33.7490, lng=-84.3880),
                Location(lat=34.7490, lng=-85.3880)
            ]
        )
        
        package = Package(volume=2.0, weight=50.0, type=CargoType.STANDARD)
        cargo = Cargo(order_id=1, packages=[package])
        self.order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=33.7500, lng=-84.3890),
            location_destiny=Location(lat=34.7500, lng=-85.3890),
            cargo=[cargo]
        )
    
    def test_metrics_calculation(self):
        """Test comprehensive metrics calculation"""
        metrics = self.processor._calculate_order_metrics(self.order, self.route, self.truck)
        
        # Check that all expected metrics are present
        expected_metrics = [
            'order_volume_m3', 'order_volume_cf',
            'order_weight_kg', 'order_weight_lbs',
            'order_distance_km', 'order_distance_miles',
            'volume_utilization_percent', 'weight_utilization_percent',
            'deviation_distance_miles', 'additional_cost_usd'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], (int, float))
    
    def test_unit_conversions(self):
        """Test that unit conversions are correct"""
        metrics = self.processor._calculate_order_metrics(self.order, self.route, self.truck)
        
        # Test volume conversion (m³ to cubic feet)
        volume_m3 = metrics['order_volume_m3']
        volume_cf = metrics['order_volume_cf']
        expected_cf = volume_m3 / OrderProcessingConstants.CUBIC_FEET_TO_CUBIC_METERS
        self.assertAlmostEqual(volume_cf, expected_cf, places=3)
        
        # Test weight conversion (kg to lbs)
        weight_kg = metrics['order_weight_kg']
        weight_lbs = metrics['order_weight_lbs']
        expected_lbs = weight_kg / OrderProcessingConstants.LBS_TO_KG
        self.assertAlmostEqual(weight_lbs, expected_lbs, places=3)


class TestBatchProcessing(unittest.TestCase):
    """Test batch processing of multiple orders"""
    
    def setUp(self):
        self.processor = OrderProcessor()
        
        # Create test data
        self.trucks = [
            Truck(autonomy=800.0, capacity=48.0, type="standard", cargo_loads=[])
        ]
        
        self.routes = [
            Route(
                location_origin_id=1,
                location_destiny_id=2,
                location_origin=Location(lat=33.7490, lng=-84.3880),
                location_destiny=Location(lat=34.7490, lng=-85.3880),
                path=[
                    Location(lat=33.7490, lng=-84.3880),
                    Location(lat=34.7490, lng=-85.3880)
                ]
            )
        ]
        
        # Create test orders
        package1 = Package(volume=1.0, weight=25.0, type=CargoType.STANDARD)
        cargo1 = Cargo(order_id=1, packages=[package1])
        
        package2 = Package(volume=2.0, weight=50.0, type=CargoType.STANDARD)
        cargo2 = Cargo(order_id=2, packages=[package2])
        
        self.orders = [
            Order(
                id=1,
                location_origin_id=1,
                location_destiny_id=2,
                location_origin=Location(lat=33.7500, lng=-84.3890),
                location_destiny=Location(lat=34.7500, lng=-85.3890),
                cargo=[cargo1]
            ),
            Order(
                id=2,
                location_origin_id=1,
                location_destiny_id=2,
                location_origin=Location(lat=33.7600, lng=-84.3900),
                location_destiny=Location(lat=34.7600, lng=-85.3900),
                cargo=[cargo2]
            )
        ]
    
    def test_batch_processing(self):
        """Test processing multiple orders"""
        results = self.processor.process_order_batch(self.orders, self.routes, self.trucks)
        
        self.assertEqual(len(results), 2)
        self.assertIn(1, results)
        self.assertIn(2, results)
        
        for order_id, result in results.items():
            self.assertIsInstance(result, ProcessingResult)
            self.assertIsInstance(result.is_valid, bool)
            self.assertIsInstance(result.errors, list)
            self.assertIsInstance(result.metrics, dict)
    
    def test_efficiency_scoring(self):
        """Test efficiency scoring for route selection"""
        # Test with metrics that should give a good score
        good_metrics = {
            'volume_utilization_percent': 80.0,
            'weight_utilization_percent': 70.0,
            'additional_cost_usd': 5.0,
            'deviation_distance_miles': 1.0
        }
        
        score = self.processor._calculate_efficiency_score(good_metrics)
        self.assertGreater(score, 0)
        
        # Test with metrics that should give a poor score
        poor_metrics = {
            'volume_utilization_percent': 10.0,
            'weight_utilization_percent': 10.0,
            'additional_cost_usd': 100.0,
            'deviation_distance_miles': 50.0
        }
        
        poor_score = self.processor._calculate_efficiency_score(poor_metrics)
        self.assertLess(poor_score, score)


if __name__ == '__main__':
    unittest.main()