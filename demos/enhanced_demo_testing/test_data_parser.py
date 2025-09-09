"""
Test Data Parser for Enhanced Demo Testing

This module handles parsing and validation of test data from JSON files,
converting them into schema objects for comprehensive testing.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from schemas.schemas import Order, Cargo, Package, Location, Route, Truck, CargoType


@dataclass
class TestOrder:
    """Enhanced order with test metadata and expected outcomes"""
    order: Order
    test_description: str
    cargo_type: str
    distance_category: str
    expected_outcome: Optional[str] = None
    order_index: int = 0
    
    def __post_init__(self):
        """Generate test description and categorization after initialization"""
        if not self.test_description:
            self.test_description = self._generate_description()
        if not self.cargo_type:
            self.cargo_type = self._determine_cargo_type()
        if not self.distance_category:
            self.distance_category = self._categorize_distance()
    
    def _generate_description(self) -> str:
        """Generate a descriptive test case description"""
        if not self.order.cargo:
            return f"Order {self.order_index + 1}: Unknown cargo"
        
        cargo = self.order.cargo[0]  # Assuming single cargo per order
        total_packages = len(cargo.packages)
        total_volume = cargo.total_volume()
        total_weight = cargo.total_weight()
        cargo_types = list(cargo.get_types())
        
        distance = self.order.total_distance()
        
        return (f"Order {self.order_index + 1}: {total_packages} packages, "
                f"{total_volume:.0f}m³, {total_weight:.0f}kg, "
                f"{cargo_types[0].value} cargo, {distance:.1f}km distance")
    
    def _determine_cargo_type(self) -> str:
        """Determine the primary cargo type for this order"""
        if not self.order.cargo:
            return "unknown"
        
        cargo_types = self.order.cargo[0].get_types()
        if CargoType.HAZMAT in cargo_types:
            return "hazmat"
        elif CargoType.FRAGILE in cargo_types:
            return "fragile"
        elif CargoType.REFRIGERATED in cargo_types:
            return "refrigerated"
        else:
            return "general"
    
    def _categorize_distance(self) -> str:
        """Categorize the order by distance"""
        distance = self.order.total_distance()
        if distance < 50:
            return "short"
        elif distance < 150:
            return "medium"
        elif distance < 300:
            return "long"
        else:
            return "very_long"


class TestDataParser:
    """
    Parser for test data JSON files that converts them into schema objects
    for comprehensive testing scenarios.
    """
    
    def __init__(self):
        self.test_data_path = "tests/test_routes/test_data.json"
        self.test_orders: List[TestOrder] = []
        self.test_routes: List[Route] = []
        self.test_trucks: List[Truck] = []
    
    def load_test_data(self, file_path: Optional[str] = None) -> List[TestOrder]:
        """
        Load and parse test data from JSON file
        
        Args:
            file_path: Optional path to JSON file, defaults to standard test data location
            
        Returns:
            List of TestOrder objects with parsed data
            
        Raises:
            FileNotFoundError: If the test data file doesn't exist
            ValueError: If JSON structure is invalid
        """
        if file_path:
            self.test_data_path = file_path
        
        if not os.path.exists(self.test_data_path):
            raise FileNotFoundError(f"Test data file not found: {self.test_data_path}")
        
        try:
            with open(self.test_data_path, 'r') as file:
                json_data = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {self.test_data_path}: {str(e)}")
        
        if not self.validate_json_structure(json_data):
            raise ValueError("Invalid JSON structure - missing required fields")
        
        self.test_orders = self.convert_to_schema_objects(json_data)
        return self.test_orders
    
    def validate_json_structure(self, data: Any) -> bool:
        """
        Validate that the JSON data has the expected structure
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if structure is valid, False otherwise
        """
        if not isinstance(data, list):
            return False
        
        for i, order_data in enumerate(data):
            if not isinstance(order_data, dict):
                print(f"Order {i}: Not a dictionary")
                return False
            
            # Check required top-level keys
            required_keys = ['cargo', 'pick-up', 'drop-off']
            for key in required_keys:
                if key not in order_data:
                    print(f"Order {i}: Missing required key '{key}'")
                    return False
            
            # Validate cargo structure
            cargo = order_data['cargo']
            if not isinstance(cargo, dict) or 'packages' not in cargo:
                print(f"Order {i}: Invalid cargo structure")
                return False
            
            packages = cargo['packages']
            if not isinstance(packages, list) or len(packages) != 3:
                print(f"Order {i}: Packages should be a list of [volume, weight, type]")
                return False
            
            # Validate package data types
            try:
                volume = float(packages[0])
                weight = float(packages[1])
                cargo_type = str(packages[2])
                
                if volume <= 0 or weight <= 0:
                    print(f"Order {i}: Volume and weight must be positive")
                    return False
                
                # Validate cargo type
                valid_types = ['general', 'standard', 'fragile', 'hazmat', 'refrigerated']
                if cargo_type not in valid_types:
                    print(f"Order {i}: Invalid cargo type '{cargo_type}'. Must be one of {valid_types}")
                    return False
                    
            except (ValueError, TypeError):
                print(f"Order {i}: Invalid package data types")
                return False
            
            # Validate location structures
            for location_key in ['pick-up', 'drop-off']:
                location = order_data[location_key]
                if not isinstance(location, dict):
                    print(f"Order {i}: {location_key} must be a dictionary")
                    return False
                
                for coord in ['latitude', 'longitude']:
                    if coord not in location:
                        print(f"Order {i}: {location_key} missing '{coord}'")
                        return False
                    
                    try:
                        coord_value = float(location[coord])
                        # Basic coordinate range validation
                        if coord == 'latitude' and not (-90 <= coord_value <= 90):
                            print(f"Order {i}: Invalid latitude {coord_value}")
                            return False
                        elif coord == 'longitude' and not (-180 <= coord_value <= 180):
                            print(f"Order {i}: Invalid longitude {coord_value}")
                            return False
                    except (ValueError, TypeError):
                        print(f"Order {i}: Invalid {coord} value")
                        return False
        
        return True
    
    def convert_to_schema_objects(self, json_data: List[Dict[str, Any]]) -> List[TestOrder]:
        """
        Convert JSON data into Order, Cargo, Package, and Location objects
        
        Args:
            json_data: List of order dictionaries from JSON
            
        Returns:
            List of TestOrder objects with schema objects
        """
        test_orders = []
        
        for i, order_data in enumerate(json_data):
            try:
                # Create Location objects
                origin = Location(
                    id=None,  # Will be set when saved to DB
                    lat=float(order_data['pick-up']['latitude']),
                    lng=float(order_data['pick-up']['longitude'])
                )
                
                destiny = Location(
                    id=None,  # Will be set when saved to DB
                    lat=float(order_data['drop-off']['latitude']),
                    lng=float(order_data['drop-off']['longitude'])
                )
                
                # Create Package objects
                packages = []
                pkg_data = order_data['cargo']['packages']
                
                # Handle both single package format [volume, weight, type] 
                # and multiple packages format [[volume, weight, type], ...]
                if isinstance(pkg_data[0], list):
                    # Multiple packages
                    for pkg in pkg_data:
                        package = Package(
                            id=None,
                            volume=float(pkg[0]),
                            weight=float(pkg[1]),
                            type=self._normalize_cargo_type(str(pkg[2])),
                            cargo_id=None  # Will be set when cargo is created
                        )
                        packages.append(package)
                else:
                    # Single package format
                    package = Package(
                        id=None,
                        volume=float(pkg_data[0]),
                        weight=float(pkg_data[1]),
                        type=self._normalize_cargo_type(str(pkg_data[2])),
                        cargo_id=None
                    )
                    packages.append(package)
                
                # Create Cargo object
                cargo = Cargo(
                    id=None,
                    order_id=0,  # Placeholder, will be set when order is created
                    truck_id=None,
                    packages=packages
                )
                
                # Create Order object
                order = Order(
                    id=None,
                    location_origin_id=0,  # Placeholder
                    location_destiny_id=0,  # Placeholder
                    client_id=None,
                    route_id=None,
                    location_origin=origin,
                    location_destiny=destiny,
                    cargo=[cargo]
                )
                
                # Create TestOrder with metadata
                test_order = TestOrder(
                    order=order,
                    test_description="",  # Will be generated in __post_init__
                    cargo_type="",  # Will be determined in __post_init__
                    distance_category="",  # Will be categorized in __post_init__
                    order_index=i
                )
                
                test_orders.append(test_order)
                
            except Exception as e:
                print(f"Error converting order {i}: {str(e)}")
                continue
        
        return test_orders
    
    def _normalize_cargo_type(self, cargo_type_str: str) -> CargoType:
        """
        Normalize cargo type string to CargoType enum
        
        Args:
            cargo_type_str: String representation of cargo type
            
        Returns:
            CargoType enum value
        """
        cargo_type_str = cargo_type_str.lower().strip()
        
        # Map common variations to standard types
        type_mapping = {
            'general': CargoType.STANDARD,
            'standard': CargoType.STANDARD,
            'fragile': CargoType.FRAGILE,
            'hazmat': CargoType.HAZMAT,
            'hazardous': CargoType.HAZMAT,
            'refrigerated': CargoType.REFRIGERATED,
            'cold': CargoType.REFRIGERATED
        }
        
        return type_mapping.get(cargo_type_str, CargoType.STANDARD)
    
    def create_test_routes(self) -> List[Route]:
        """
        Create test routes based on the loaded test data
        
        Returns:
            List of Route objects for testing
        """
        if not self.test_orders:
            raise ValueError("No test orders loaded. Call load_test_data() first.")
        
        routes = []
        route_id = 1
        
        # Create routes for unique origin-destination pairs
        seen_routes = set()
        
        for test_order in self.test_orders:
            order = test_order.order
            origin = order.location_origin
            destiny = order.location_destiny
            
            # Create a route key based on coordinates (rounded to avoid floating point issues)
            route_key = (
                round(origin.lat, 4), round(origin.lng, 4),
                round(destiny.lat, 4), round(destiny.lng, 4)
            )
            
            if route_key not in seen_routes:
                route = Route(
                    id=route_id,
                    location_origin_id=0,  # Placeholder
                    location_destiny_id=0,  # Placeholder
                    location_origin=origin,
                    location_destiny=destiny,
                    profitability=0.0,
                    truck_id=None
                )
                
                routes.append(route)
                seen_routes.add(route_key)
                route_id += 1
        
        self.test_routes = routes
        return routes
    
    def create_test_trucks(self) -> List[Truck]:
        """
        Create test trucks with various capacities and types for testing
        
        Returns:
            List of Truck objects for testing
        """
        trucks = [
            # Standard trucks with different capacities
            Truck(
                id=1,
                autonomy=500.0,  # 500km range
                capacity=20.0,   # 20m³ capacity
                type="standard"
            ),
            Truck(
                id=2,
                autonomy=400.0,  # 400km range
                capacity=35.0,   # 35m³ capacity
                type="standard"
            ),
            Truck(
                id=3,
                autonomy=600.0,  # 600km range
                capacity=50.0,   # 50m³ capacity
                type="standard"
            ),
            # Specialized trucks
            Truck(
                id=4,
                autonomy=300.0,  # 300km range
                capacity=15.0,   # 15m³ capacity
                type="hazmat"
            ),
            Truck(
                id=5,
                autonomy=450.0,  # 450km range
                capacity=25.0,   # 25m³ capacity
                type="refrigerated"
            ),
            # Small capacity truck for testing capacity constraints
            Truck(
                id=6,
                autonomy=200.0,  # 200km range
                capacity=5.0,    # 5m³ capacity - very small
                type="standard"
            )
        ]
        
        self.test_trucks = trucks
        return trucks
    
    def get_test_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the loaded test data
        
        Returns:
            Dictionary with test data statistics
        """
        if not self.test_orders:
            return {"error": "No test data loaded"}
        
        # Calculate statistics
        total_orders = len(self.test_orders)
        cargo_types = {}
        distance_categories = {}
        total_volume = 0.0
        total_weight = 0.0
        total_packages = 0
        
        for test_order in self.test_orders:
            # Count cargo types
            cargo_type = test_order.cargo_type
            cargo_types[cargo_type] = cargo_types.get(cargo_type, 0) + 1
            
            # Count distance categories
            dist_cat = test_order.distance_category
            distance_categories[dist_cat] = distance_categories.get(dist_cat, 0) + 1
            
            # Sum totals
            order = test_order.order
            total_volume += order.total_volume()
            total_weight += order.total_weight()
            for cargo in order.cargo:
                total_packages += len(cargo.packages)
        
        return {
            "total_orders": total_orders,
            "cargo_types": cargo_types,
            "distance_categories": distance_categories,
            "total_volume": round(total_volume, 2),
            "total_weight": round(total_weight, 2),
            "total_packages": total_packages,
            "average_volume_per_order": round(total_volume / total_orders, 2),
            "average_weight_per_order": round(total_weight / total_orders, 2),
            "test_routes_created": len(self.test_routes),
            "test_trucks_created": len(self.test_trucks)
        }