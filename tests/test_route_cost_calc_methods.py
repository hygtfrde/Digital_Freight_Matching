import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.database import Route, Location, Order
from utils.distance_utils import haversine


class TestRouteMethods:
    """Unit tests for Route class methods"""

    def setup_method(self):
        """Set up test data before each test"""
        # Create test locations
        self.origin = Location(lat=40.7128, lng=-74.0060)  # NYC
        self.destination = Location(lat=34.0522, lng=-118.2437)  # LA
        self.waypoint1 = Location(lat=41.8781, lng=-87.6298)  # Chicago
        self.waypoint2 = Location(lat=39.9526, lng=-75.1652)  # Philadelphia

        # Create basic route
        self.route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.origin,
            location_destiny=self.destination,
            path=[self.waypoint1, self.waypoint2]
        )

        # Create test order
        self.test_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.origin,
            location_destiny=self.destination
        )

    def test_haversine_distance_calculation(self):
        """Test the haversine distance calculation"""
        # Distance between NYC and LA should be approximately 3944 km
        distance = haversine(
            self.origin.lng, self.origin.lat,
            self.destination.lng, self.destination.lat
        )
        # Allow 1% tolerance
        expected = 3944
        assert abs(distance - expected) < expected * 0.01

    def test_is_within_km_with_path_points(self):
        """Test is_within_km when location is near path points"""
        # Test location very close to Chicago (waypoint1)
        chicago_nearby = (41.8800, -87.6200)  # Slightly different coordinates

        result = self.route.is_within_km(chicago_nearby, km=5.0)
        assert result is True

    def test_is_within_km_with_origin_destination(self):
        """Test is_within_km when location is near origin/destination"""
        # Test location very close to NYC origin
        nyc_nearby = (40.7130, -74.0070)

        result = self.route.is_within_km(nyc_nearby, km=1.0)
        assert result is True

    def test_is_within_km_far_location(self):
        """Test is_within_km when location is far from route"""
        # Test location in Miami (far from route)
        miami = (25.7617, -80.1918)

        result = self.route.is_within_km(miami, km=1.0)
        assert result is False

    def test_is_within_km_empty_path(self):
        """Test is_within_km when path is empty"""
        empty_route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.origin,
            location_destiny=self.destination,
            path=[]  # Empty path
        )

        # Should still check origin and destination
        nyc_nearby = (40.7130, -74.0070)
        result = empty_route.is_within_km(nyc_nearby, km=1.0)
        assert result is True

    def test_deviation_time_for_stop_within_route(self):
        """Test deviation time when stop is within 1km of route"""
        # Location close to Chicago waypoint
        chicago_nearby = (41.8800, -87.6200)

        time = self.route.deviation_time_for_stop(chicago_nearby)
        assert time == 15  # Just stop time, no detour

    def test_deviation_time_for_stop_outside_route(self):
        """Test deviation time when stop requires detour"""
        # Location requiring detour (Miami)
        miami = (25.7617, -80.1918)

        time = self.route.deviation_time_for_stop(miami, avg_speed_kmh=60)
        assert time > 15  # Should include detour time

    def test_deviation_time_custom_speed(self):
        """Test deviation time with different speeds"""
        miami = (25.7617, -80.1918)

        time_slow = self.route.deviation_time_for_stop(miami, avg_speed_kmh=30)
        time_fast = self.route.deviation_time_for_stop(miami, avg_speed_kmh=60)

        # Slower speed should result in longer time
        assert time_slow > time_fast

    def test_calculate_added_cost_valid_order(self):
        """Test calculate_added_cost with valid order"""
        result = self.route.calculate_added_cost(self.test_order)

        assert "pickup_time" in result
        assert "dropoff_time" in result
        assert "total_time" in result
        assert result["total_time"] == result["pickup_time"] + result["dropoff_time"]
        assert all(isinstance(v, (int, float)) for v in result.values())

    def test_calculate_added_cost_missing_locations(self):
        """Test calculate_added_cost with incomplete order"""
        incomplete_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=None,  # Missing origin
            location_destiny=self.destination
        )

        result = self.route.calculate_added_cost(incomplete_order)

        assert "error" in result
        assert result["pickup_time"] == 0
        assert result["dropoff_time"] == 0
        assert result["total_time"] == 0

    def test_calculate_added_cost_order_on_route(self):
        """Test cost calculation when order locations are on route"""
        # Order with pickup/dropoff near route points
        on_route_order = Order(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=Location(lat=41.8785, lng=-87.6300),  # Near Chicago
            location_destiny=Location(lat=39.9530, lng=-75.1650)   # Near Philadelphia
        )

        result = self.route.calculate_added_cost(on_route_order)

        # Both should be minimal time (just stop time)
        assert result["pickup_time"] == 15
        assert result["dropoff_time"] == 15
        assert result["total_time"] == 30

    def test_edge_case_same_location_pickup_dropoff(self):
        """Test edge case where pickup and dropoff are same location"""
        same_location = Location(lat=40.7128, lng=-74.0060)
        same_loc_order = Order(
            location_origin_id=1,
            location_destiny_id=1,
            location_origin=same_location,
            location_destiny=same_location
        )

        result = self.route.calculate_added_cost(same_loc_order)

        # Should handle gracefully
        assert result["pickup_time"] == result["dropoff_time"]
        assert result["total_time"] == result["pickup_time"] + result["dropoff_time"]

    def test_is_within_km_edge_cases(self):
        """Test edge cases for is_within_km"""
        # Test with km=0 (exact match only)
        exact_chicago = (self.waypoint1.lat, self.waypoint1.lng)
        assert self.route.is_within_km(exact_chicago, km=0.001) is True

        # Test with very large km
        miami = (25.7617, -80.1918)
        assert self.route.is_within_km(miami, km=10000) is True

    def test_performance_large_path(self):
        """Test performance with large number of path points"""
        # Create route with many waypoints
        large_path = [
            Location(lat=40 + i*0.1, lng=-74 + i*0.1)
            for i in range(100)
        ]

        large_route = Route(
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=self.origin,
            location_destiny=self.destination,
            path=large_path
        )

        test_location = (45.0, -70.0)

        # Should complete quickly even with many points
        import time
        start = time.time()
        result = large_route.is_within_km(test_location, km=1.0)
        end = time.time()

        assert (end - start) < 1.0  # Should complete in less than 1 second
        assert isinstance(result, bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
