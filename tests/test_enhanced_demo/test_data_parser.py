"""
Unit tests for TestDataParser

Tests JSON parsing, validation, and schema object conversion functionality.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open

from demos.enhanced_demo_testing.test_data_parser import TestDataParser, TestOrder
from schemas.schemas import Order, Cargo, Package, Location, CargoType


class TestTestDataParser:
    """Test cases for TestDataParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = TestDataParser()
        
        # Sample valid test data
        self.valid_test_data = [
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
                    "packages": [15, 2000, "hazmat"]
                },
                "pick-up": {
                    "latitude": 33.748,
                    "longitude": -84.389
                },
                "drop-off": {
                    "latitude": 32.082,
                    "longitude": -81.100
                }
            }
        ]
    
    def test_init(self):
        """Test parser initialization"""
        parser = TestDataParser()
        assert parser.test_data_path == "tests/test_routes/test_data.json"
        assert parser.test_orders == []
        assert parser.test_routes == []
        assert parser.test_trucks == []
    
    def test_validate_json_structure_valid(self):
        """Test validation with valid JSON structure"""
        assert self.parser.validate_json_structure(self.valid_test_data) is True
    
    def test_validate_json_structure_invalid_not_list(self):
        """Test validation fails when data is not a list"""
        invalid_data = {"not": "a list"}
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_validate_json_structure_missing_keys(self):
        """Test validation fails when required keys are missing"""
        invalid_data = [
            {
                "cargo": {"packages": [10, 1500, "general"]},
                # Missing pick-up and drop-off
            }
        ]
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_validate_json_structure_invalid_cargo(self):
        """Test validation fails with invalid cargo structure"""
        invalid_data = [
            {
                "cargo": {"not_packages": "invalid"},
                "pick-up": {"latitude": 33.753, "longitude": -84.390},
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            }
        ]
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_validate_json_structure_invalid_packages(self):
        """Test validation fails with invalid package structure"""
        invalid_data = [
            {
                "cargo": {"packages": [10, 1500]},  # Missing cargo type
                "pick-up": {"latitude": 33.753, "longitude": -84.390},
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            }
        ]
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_validate_json_structure_invalid_coordinates(self):
        """Test validation fails with invalid coordinates"""
        invalid_data = [
            {
                "cargo": {"packages": [10, 1500, "general"]},
                "pick-up": {"latitude": 200, "longitude": -84.390},  # Invalid latitude
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            }
        ]
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_validate_json_structure_invalid_cargo_type(self):
        """Test validation fails with invalid cargo type"""
        invalid_data = [
            {
                "cargo": {"packages": [10, 1500, "invalid_type"]},
                "pick-up": {"latitude": 33.753, "longitude": -84.390},
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            }
        ]
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_validate_json_structure_negative_values(self):
        """Test validation fails with negative volume/weight"""
        invalid_data = [
            {
                "cargo": {"packages": [-10, 1500, "general"]},  # Negative volume
                "pick-up": {"latitude": 33.753, "longitude": -84.390},
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            }
        ]
        assert self.parser.validate_json_structure(invalid_data) is False
    
    def test_normalize_cargo_type(self):
        """Test cargo type normalization"""
        assert self.parser._normalize_cargo_type("general") == CargoType.STANDARD
        assert self.parser._normalize_cargo_type("STANDARD") == CargoType.STANDARD
        assert self.parser._normalize_cargo_type("hazmat") == CargoType.HAZMAT
        assert self.parser._normalize_cargo_type("HAZARDOUS") == CargoType.HAZMAT
        assert self.parser._normalize_cargo_type("fragile") == CargoType.FRAGILE
        assert self.parser._normalize_cargo_type("refrigerated") == CargoType.REFRIGERATED
        assert self.parser._normalize_cargo_type("cold") == CargoType.REFRIGERATED
        assert self.parser._normalize_cargo_type("unknown") == CargoType.STANDARD
    
    def test_convert_to_schema_objects(self):
        """Test conversion of JSON data to schema objects"""
        test_orders = self.parser.convert_to_schema_objects(self.valid_test_data)
        
        assert len(test_orders) == 2
        
        # Test first order
        first_order = test_orders[0]
        assert isinstance(first_order, TestOrder)
        assert isinstance(first_order.order, Order)
        assert isinstance(first_order.order.location_origin, Location)
        assert isinstance(first_order.order.location_destiny, Location)
        
        # Check location coordinates
        assert first_order.order.location_origin.lat == 33.753
        assert first_order.order.location_origin.lng == -84.390
        assert first_order.order.location_destiny.lat == 32.460
        assert first_order.order.location_destiny.lng == -84.985
        
        # Check cargo and packages
        assert len(first_order.order.cargo) == 1
        cargo = first_order.order.cargo[0]
        assert isinstance(cargo, Cargo)
        assert len(cargo.packages) == 1
        
        package = cargo.packages[0]
        assert isinstance(package, Package)
        assert package.volume == 10.0
        assert package.weight == 1500.0
        assert package.type == CargoType.STANDARD
        
        # Test second order (hazmat)
        second_order = test_orders[1]
        second_package = second_order.order.cargo[0].packages[0]
        assert second_package.type == CargoType.HAZMAT
    
    def test_convert_to_schema_objects_with_error(self):
        """Test conversion handles errors gracefully"""
        invalid_data = [
            {
                "cargo": {"packages": [10, 1500, "general"]},
                "pick-up": {"latitude": "invalid", "longitude": -84.390},  # Invalid latitude
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            }
        ]
        
        # Should return empty list when conversion fails
        test_orders = self.parser.convert_to_schema_objects(invalid_data)
        assert len(test_orders) == 0
    
    def test_load_test_data_file_not_found(self):
        """Test load_test_data raises FileNotFoundError for missing file"""
        with pytest.raises(FileNotFoundError):
            self.parser.load_test_data("nonexistent_file.json")
    
    def test_load_test_data_invalid_json(self):
        """Test load_test_data raises ValueError for invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON format"):
                self.parser.load_test_data(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_load_test_data_invalid_structure(self):
        """Test load_test_data raises ValueError for invalid structure"""
        invalid_data = {"not": "a list"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON structure"):
                self.parser.load_test_data(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_load_test_data_success(self):
        """Test successful loading of test data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_test_data, f)
            temp_file = f.name
        
        try:
            test_orders = self.parser.load_test_data(temp_file)
            assert len(test_orders) == 2
            assert all(isinstance(order, TestOrder) for order in test_orders)
            assert self.parser.test_orders == test_orders
        finally:
            os.unlink(temp_file)
    
    def test_create_test_routes_no_orders(self):
        """Test create_test_routes raises error when no orders loaded"""
        with pytest.raises(ValueError, match="No test orders loaded"):
            self.parser.create_test_routes()
    
    def test_create_test_routes_success(self):
        """Test successful creation of test routes"""
        # Load test data first
        self.parser.test_orders = self.parser.convert_to_schema_objects(self.valid_test_data)
        
        routes = self.parser.create_test_routes()
        
        # Should create routes for unique origin-destination pairs
        assert len(routes) == 2  # Two different routes in test data
        assert all(route.id is not None for route in routes)
        assert all(route.location_origin is not None for route in routes)
        assert all(route.location_destiny is not None for route in routes)
    
    def test_create_test_routes_deduplication(self):
        """Test that duplicate routes are not created"""
        # Create test data with duplicate routes
        duplicate_data = [
            {
                "cargo": {"packages": [10, 1500, "general"]},
                "pick-up": {"latitude": 33.753, "longitude": -84.390},
                "drop-off": {"latitude": 32.460, "longitude": -84.985}
            },
            {
                "cargo": {"packages": [15, 2000, "general"]},
                "pick-up": {"latitude": 33.753, "longitude": -84.390},  # Same pickup
                "drop-off": {"latitude": 32.460, "longitude": -84.985}   # Same dropoff
            }
        ]
        
        self.parser.test_orders = self.parser.convert_to_schema_objects(duplicate_data)
        routes = self.parser.create_test_routes()
        
        # Should only create one route for the duplicate origin-destination pair
        assert len(routes) == 1
    
    def test_create_test_trucks(self):
        """Test creation of test trucks"""
        trucks = self.parser.create_test_trucks()
        
        assert len(trucks) == 6  # Should create 6 different trucks
        assert all(truck.id is not None for truck in trucks)
        assert all(truck.autonomy > 0 for truck in trucks)
        assert all(truck.capacity > 0 for truck in trucks)
        
        # Check for different truck types
        truck_types = [truck.type for truck in trucks]
        assert "standard" in truck_types
        assert "hazmat" in truck_types
        assert "refrigerated" in truck_types
        
        # Check that trucks have different capacities
        capacities = [truck.capacity for truck in trucks]
        assert len(set(capacities)) > 1  # Should have different capacities
    
    def test_get_test_summary_no_data(self):
        """Test get_test_summary with no data loaded"""
        summary = self.parser.get_test_summary()
        assert "error" in summary
        assert summary["error"] == "No test data loaded"
    
    def test_get_test_summary_with_data(self):
        """Test get_test_summary with loaded data"""
        self.parser.test_orders = self.parser.convert_to_schema_objects(self.valid_test_data)
        self.parser.create_test_routes()
        self.parser.create_test_trucks()
        
        summary = self.parser.get_test_summary()
        
        assert summary["total_orders"] == 2
        assert "cargo_types" in summary
        assert "distance_categories" in summary
        assert summary["total_volume"] > 0
        assert summary["total_weight"] > 0
        assert summary["total_packages"] == 2
        assert summary["average_volume_per_order"] > 0
        assert summary["average_weight_per_order"] > 0
        assert summary["test_routes_created"] == 2
        assert summary["test_trucks_created"] == 6


class TestTestOrder:
    """Test cases for TestOrder dataclass"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a sample order
        origin = Location(lat=33.753, lng=-84.390)
        destiny = Location(lat=32.460, lng=-84.985)
        
        package = Package(volume=10.0, weight=1500.0, type=CargoType.STANDARD)
        cargo = Cargo(order_id=1, packages=[package])
        
        self.order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=origin,
            location_destiny=destiny,
            cargo=[cargo]
        )
    
    def test_test_order_initialization(self):
        """Test TestOrder initialization and auto-generation of fields"""
        test_order = TestOrder(
            order=self.order,
            test_description="",
            cargo_type="",
            distance_category="",
            order_index=0
        )
        
        # Check that fields are auto-generated
        assert test_order.test_description != ""
        assert test_order.cargo_type == "general"
        assert test_order.distance_category in ["short", "medium", "long", "very_long"]
        assert "Order 1:" in test_order.test_description
        assert "1 packages" in test_order.test_description
        assert "10m³" in test_order.test_description
        assert "1500kg" in test_order.test_description
    
    def test_test_order_hazmat_cargo(self):
        """Test TestOrder with hazmat cargo"""
        # Create hazmat package
        hazmat_package = Package(volume=15.0, weight=2000.0, type=CargoType.HAZMAT)
        hazmat_cargo = Cargo(order_id=1, packages=[hazmat_package])
        
        hazmat_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.order.location_origin,
            location_destiny=self.order.location_destiny,
            cargo=[hazmat_cargo]
        )
        
        test_order = TestOrder(
            order=hazmat_order,
            test_description="",
            cargo_type="",
            distance_category="",
            order_index=1
        )
        
        assert test_order.cargo_type == "hazmat"
        assert "hazmat cargo" in test_order.test_description
    
    def test_test_order_distance_categories(self):
        """Test distance categorization"""
        # Test short distance (< 50km)
        short_destiny = Location(lat=33.800, lng=-84.400)  # Very close
        short_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.order.location_origin,
            location_destiny=short_destiny,
            cargo=self.order.cargo
        )
        
        test_order = TestOrder(
            order=short_order,
            test_description="",
            cargo_type="",
            distance_category="",
            order_index=0
        )
        
        assert test_order.distance_category == "short"
        
        # Test very long distance (> 300km)
        far_destiny = Location(lat=30.000, lng=-80.000)  # Very far
        far_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.order.location_origin,
            location_destiny=far_destiny,
            cargo=self.order.cargo
        )
        
        test_order_far = TestOrder(
            order=far_order,
            test_description="",
            cargo_type="",
            distance_category="",
            order_index=0
        )
        
        assert test_order_far.distance_category == "very_long"
    
    def test_test_order_no_cargo(self):
        """Test TestOrder with no cargo"""
        no_cargo_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.order.location_origin,
            location_destiny=self.order.location_destiny,
            cargo=[]
        )
        
        test_order = TestOrder(
            order=no_cargo_order,
            test_description="",
            cargo_type="",
            distance_category="",
            order_index=0
        )
        
        assert test_order.cargo_type == "unknown"
        assert "Unknown cargo" in test_order.test_description


if __name__ == "__main__":
    pytest.main([__file__])