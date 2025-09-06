"""
Unit tests for route calculation data models and utilities.

Tests the BoundingBox, DistanceResult, RouteResult classes and coordinate validation utilities.
"""

import pytest
from unittest.mock import Mock
from services.route_calculation import (
    BoundingBox, DistanceResult, RouteResult,
    validate_coordinates, validate_location_object, validate_location_list,
    safe_distance_calculation, create_error_result, create_error_route_result,
    CoordinateValidationError, RouteCalculationError
)


class TestBoundingBox:
    """Test cases for BoundingBox class."""

    def test_valid_bounding_box_creation(self):
        """Test creating a valid bounding box."""
        bbox = BoundingBox(north=34.0, south=33.0, east=-84.0, west=-85.0)
        assert bbox.north == 34.0
        assert bbox.south == 33.0
        assert bbox.east == -84.0
        assert bbox.west == -85.0

    def test_invalid_coordinates_validation(self):
        """Test validation of invalid coordinates."""
        # Invalid latitude range
        with pytest.raises(ValueError):
            BoundingBox(north=91.0, south=33.0, east=-84.0, west=-85.0)

        # Invalid longitude range
        with pytest.raises(ValueError):
            BoundingBox(north=34.0, south=33.0, east=181.0, west=-85.0)

        # South >= North
        with pytest.raises(ValueError):
            BoundingBox(north=33.0, south=34.0, east=-84.0, west=-85.0)

        # West >= East
        with pytest.raises(ValueError):
            BoundingBox(north=34.0, south=33.0, east=-85.0, west=-84.0)

    def test_from_locations_single_location(self):
        """Test creating bounding box from single location."""
        location = Mock()
        location.lat = 33.7490
        location.lng = -84.3880

        bbox = BoundingBox.from_locations([location], padding_km=10.0)

        # Should have padding around the single point
        assert bbox.north > location.lat
        assert bbox.south < location.lat
        assert bbox.east > location.lng
        assert bbox.west < location.lng

    def test_from_locations_multiple_locations(self):
        """Test creating bounding box from multiple locations."""
        loc1 = Mock()
        loc1.lat = 33.7490
        loc1.lng = -84.3880

        loc2 = Mock()
        loc2.lat = 34.5085
        loc2.lng = -85.0007

        bbox = BoundingBox.from_locations([loc1, loc2], padding_km=5.0)

        # Should encompass both locations with padding
        assert bbox.north > max(loc1.lat, loc2.lat)
        assert bbox.south < min(loc1.lat, loc2.lat)
        assert bbox.east > max(loc1.lng, loc2.lng)
        assert bbox.west < min(loc1.lng, loc2.lng)

    def test_from_locations_empty_list(self):
        """Test error handling for empty location list."""
        with pytest.raises(ValueError, match="empty locations list"):
            BoundingBox.from_locations([])

    def test_from_locations_invalid_location(self):
        """Test error handling for invalid location objects."""
        invalid_location = object()  # Simple object without lat/lng attributes

        with pytest.raises(ValueError, match="missing lat/lng attributes"):
            BoundingBox.from_locations([invalid_location])

    def test_adaptive_padding_short_route(self):
        """Test adaptive padding for short routes (<50km)."""
        loc1 = Mock()
        loc1.lat = 33.7490
        loc1.lng = -84.3880

        loc2 = Mock()
        loc2.lat = 33.8490  # About 11km north
        loc2.lng = -84.3880

        bbox = BoundingBox.adaptive_padding([loc1, loc2])

        # Should use 10km base padding for short routes
        assert bbox is not None
        assert bbox.north > loc2.lat
        assert bbox.south < loc1.lat

    def test_adaptive_padding_medium_route(self):
        """Test adaptive padding for medium routes (50-200km)."""
        loc1 = Mock()
        loc1.lat = 33.7490
        loc1.lng = -84.3880

        loc2 = Mock()
        loc2.lat = 34.5085  # About 85km away
        loc2.lng = -85.0007

        bbox = BoundingBox.adaptive_padding([loc1, loc2])

        # Should use percentage-based padding for medium routes
        assert bbox is not None
        assert bbox.north > max(loc1.lat, loc2.lat)
        assert bbox.south < min(loc1.lat, loc2.lat)

    def test_adaptive_padding_single_location(self):
        """Test adaptive padding with single location."""
        location = Mock()
        location.lat = 33.7490
        location.lng = -84.3880

        bbox = BoundingBox.adaptive_padding([location])

        # Should use base padding for single location
        assert bbox is not None
        assert bbox.north > location.lat
        assert bbox.south < location.lat

    def test_area_calculation(self):
        """Test bounding box area calculation."""
        bbox = BoundingBox(north=34.0, south=33.0, east=-84.0, west=-85.0)
        area = bbox.area_km2()

        # Should return positive area
        assert area > 0
        assert isinstance(area, float)

    def test_reasonable_size_check(self):
        """Test reasonable size validation."""
        # Small bounding box should be reasonable
        small_bbox = BoundingBox(north=33.8, south=33.7, east=-84.3, west=-84.4)
        assert small_bbox.is_reasonable_size()

        # Very large bounding box should not be reasonable
        large_bbox = BoundingBox(north=40.0, south=30.0, east=-80.0, west=-90.0)
        assert not large_bbox.is_reasonable_size(max_area_km2=1000)

    def test_string_representation(self):
        """Test string representation of bounding box."""
        bbox = BoundingBox(north=34.0, south=33.0, east=-84.0, west=-85.0)
        str_repr = str(bbox)

        assert "BoundingBox" in str_repr
        assert "34.0000" in str_repr
        assert "33.0000" in str_repr


class TestDistanceResult:
    """Test cases for DistanceResult class."""

    def test_valid_distance_result(self):
        """Test creating valid distance result."""
        result = DistanceResult(
            distance_km=100.5,
            calculation_method="osmnx",
            drive_time_hours=1.25
        )

        assert result.distance_km == 100.5
        assert result.calculation_method == "osmnx"
        assert result.drive_time_hours == 1.25
        assert result.is_successful
        assert result.used_road_network

    def test_invalid_distance_validation(self):
        """Test validation of invalid distance values."""
        with pytest.raises(ValueError, match="Distance cannot be negative"):
            DistanceResult(distance_km=-10.0, calculation_method="osmnx")

    def test_invalid_calculation_method(self):
        """Test validation of invalid calculation method."""
        with pytest.raises(ValueError, match="Invalid calculation method"):
            DistanceResult(distance_km=100.0, calculation_method="invalid")

    def test_invalid_drive_time(self):
        """Test validation of invalid drive time."""
        with pytest.raises(ValueError, match="Drive time cannot be negative"):
            DistanceResult(
                distance_km=100.0,
                calculation_method="osmnx",
                drive_time_hours=-1.0
            )

    def test_error_result(self):
        """Test distance result with error."""
        result = DistanceResult(
            distance_km=0.0,
            calculation_method="osmnx",
            error="Network unavailable"
        )

        assert not result.is_successful
        assert result.error == "Network unavailable"

    def test_speed_calculation(self):
        """Test average speed calculation."""
        result = DistanceResult(
            distance_km=100.0,
            calculation_method="osmnx",
            drive_time_hours=1.25
        )

        speed = result.get_speed_kmh()
        assert speed == 80.0  # 100km / 1.25h = 80 km/h

    def test_speed_calculation_no_time(self):
        """Test speed calculation when no time available."""
        result = DistanceResult(distance_km=100.0, calculation_method="osmnx")
        assert result.get_speed_kmh() is None

    def test_road_network_detection(self):
        """Test detection of road network usage."""
        osmnx_result = DistanceResult(distance_km=100.0, calculation_method="osmnx")
        assert osmnx_result.used_road_network

        haversine_result = DistanceResult(distance_km=100.0, calculation_method="haversine")
        assert not haversine_result.used_road_network

    def test_string_representation(self):
        """Test string representation."""
        result = DistanceResult(
            distance_km=100.5,
            calculation_method="osmnx",
            drive_time_hours=1.25
        )

        str_repr = str(result)
        assert "100.50km" in str_repr
        assert "1.25h" in str_repr
        assert "osmnx" in str_repr


class TestRouteResult:
    """Test cases for RouteResult class."""

    def test_valid_route_result(self):
        """Test creating valid route result."""
        result = RouteResult(
            total_distance_km=250.0,
            total_time_hours=3.5,
            waypoint_distances=[100.0, 75.0, 75.0],
            calculation_method="osmnx",
            network_available=True
        )

        assert result.total_distance_km == 250.0
        assert result.total_time_hours == 3.5
        assert len(result.waypoint_distances) == 3
        assert result.is_successful
        assert result.used_road_network

    def test_invalid_distance_validation(self):
        """Test validation of invalid distances."""
        with pytest.raises(ValueError, match="Total distance cannot be negative"):
            RouteResult(
                total_distance_km=-100.0,
                total_time_hours=1.0,
                waypoint_distances=[],
                calculation_method="osmnx",
                network_available=True
            )

    def test_invalid_time_validation(self):
        """Test validation of invalid time."""
        with pytest.raises(ValueError, match="Total time cannot be negative"):
            RouteResult(
                total_distance_km=100.0,
                total_time_hours=-1.0,
                waypoint_distances=[],
                calculation_method="osmnx",
                network_available=True
            )

    def test_invalid_waypoint_distances(self):
        """Test validation of invalid waypoint distances."""
        with pytest.raises(ValueError, match="Waypoint distances cannot be negative"):
            RouteResult(
                total_distance_km=100.0,
                total_time_hours=1.0,
                waypoint_distances=[50.0, -25.0, 75.0],
                calculation_method="osmnx",
                network_available=True
            )

    def test_waypoint_calculations(self):
        """Test waypoint-related calculations."""
        result = RouteResult(
            total_distance_km=250.0,
            total_time_hours=3.5,
            waypoint_distances=[100.0, 75.0, 75.0],
            calculation_method="osmnx",
            network_available=True
        )

        assert result.num_waypoints == 4  # 3 segments = 4 waypoints
        assert result.get_longest_segment_km() == 100.0
        assert result.get_shortest_segment_km() == 75.0

    def test_average_speed_calculation(self):
        """Test average speed calculation."""
        result = RouteResult(
            total_distance_km=200.0,
            total_time_hours=2.5,
            waypoint_distances=[100.0, 100.0],
            calculation_method="osmnx",
            network_available=True
        )

        speed = result.get_average_speed_kmh()
        assert speed == 80.0  # 200km / 2.5h = 80 km/h

    def test_consistency_validation(self):
        """Test validation of waypoint distance consistency."""
        # Consistent result
        consistent_result = RouteResult(
            total_distance_km=250.0,
            total_time_hours=3.0,
            waypoint_distances=[100.0, 75.0, 75.0],  # Sum = 250.0
            calculation_method="osmnx",
            network_available=True
        )
        assert consistent_result.validate_consistency()

        # Inconsistent result (within tolerance)
        slightly_off_result = RouteResult(
            total_distance_km=250.0,
            total_time_hours=3.0,
            waypoint_distances=[100.0, 75.0, 74.5],  # Sum = 249.5
            calculation_method="osmnx",
            network_available=True
        )
        assert slightly_off_result.validate_consistency()

        # Very inconsistent result
        inconsistent_result = RouteResult(
            total_distance_km=250.0,
            total_time_hours=3.0,
            waypoint_distances=[100.0, 75.0, 50.0],  # Sum = 225.0
            calculation_method="osmnx",
            network_available=True
        )
        assert not inconsistent_result.validate_consistency()


class TestCoordinateValidation:
    """Test cases for coordinate validation utilities."""

    def test_valid_coordinates(self):
        """Test validation of valid coordinates."""
        # Should not raise exception
        validate_coordinates(33.7490, -84.3880)
        validate_coordinates(0.0, 0.0)
        validate_coordinates(90.0, 180.0)
        validate_coordinates(-90.0, -180.0)

    def test_invalid_latitude(self):
        """Test validation of invalid latitude values."""
        with pytest.raises(CoordinateValidationError, match="Latitude must be between"):
            validate_coordinates(91.0, -84.3880)

        with pytest.raises(CoordinateValidationError, match="Latitude must be between"):
            validate_coordinates(-91.0, -84.3880)

    def test_invalid_longitude(self):
        """Test validation of invalid longitude values."""
        with pytest.raises(CoordinateValidationError, match="Longitude must be between"):
            validate_coordinates(33.7490, 181.0)

        with pytest.raises(CoordinateValidationError, match="Longitude must be between"):
            validate_coordinates(33.7490, -181.0)

    def test_nan_coordinates(self):
        """Test validation of NaN coordinates."""
        with pytest.raises(CoordinateValidationError, match="cannot be NaN"):
            validate_coordinates(float('nan'), -84.3880)

        with pytest.raises(CoordinateValidationError, match="cannot be NaN"):
            validate_coordinates(33.7490, float('nan'))

    def test_infinite_coordinates(self):
        """Test validation of infinite coordinates."""
        with pytest.raises(CoordinateValidationError, match="cannot be infinite"):
            validate_coordinates(float('inf'), -84.3880)

        with pytest.raises(CoordinateValidationError, match="cannot be infinite"):
            validate_coordinates(33.7490, float('-inf'))

    def test_non_numeric_coordinates(self):
        """Test validation of non-numeric coordinates."""
        with pytest.raises(CoordinateValidationError, match="must be numeric"):
            validate_coordinates("33.7490", -84.3880)

        with pytest.raises(CoordinateValidationError, match="must be numeric"):
            validate_coordinates(33.7490, "-84.3880")


class TestLocationValidation:
    """Test cases for location object validation."""

    def test_valid_location_object(self):
        """Test validation of valid location object."""
        location = Mock()
        location.lat = 33.7490
        location.lng = -84.3880

        # Should not raise exception
        validate_location_object(location)

    def test_none_location(self):
        """Test validation of None location."""
        with pytest.raises(CoordinateValidationError, match="cannot be None"):
            validate_location_object(None)

    def test_missing_attributes(self):
        """Test validation of location missing attributes."""
        location = object()  # Simple object without lat/lng attributes

        with pytest.raises(CoordinateValidationError, match="must have 'lat' and 'lng'"):
            validate_location_object(location)

    def test_location_list_validation(self):
        """Test validation of location lists."""
        loc1 = Mock()
        loc1.lat = 33.7490
        loc1.lng = -84.3880

        loc2 = Mock()
        loc2.lat = 34.5085
        loc2.lng = -85.0007

        # Valid list should not raise exception
        validate_location_list([loc1, loc2])

        # Empty list should raise exception
        with pytest.raises(CoordinateValidationError, match="cannot be empty"):
            validate_location_list([])

        # Insufficient locations should raise exception
        with pytest.raises(CoordinateValidationError, match="At least 2 locations"):
            validate_location_list([loc1], min_locations=2)


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_safe_distance_calculation_success(self):
        """Test safe distance calculation with successful function."""
        def successful_calc(a, b):
            return a + b

        result = safe_distance_calculation(successful_calc, 10, 20)
        assert result == 30.0

    def test_safe_distance_calculation_error(self):
        """Test safe distance calculation with error."""
        def failing_calc(a, b):
            raise Exception("Calculation failed")

        result = safe_distance_calculation(failing_calc, 10, 20, fallback_value=50.0)
        assert result == 50.0

    def test_safe_distance_calculation_invalid_result(self):
        """Test safe distance calculation with invalid result."""
        def invalid_calc(a, b):
            return -10  # Negative distance is invalid

        result = safe_distance_calculation(invalid_calc, 10, 20, fallback_value=0.0)
        assert result == 0.0

    def test_create_error_result(self):
        """Test creation of error distance result."""
        result = create_error_result("Test error", "error")

        assert result.distance_km == 0.0
        assert result.calculation_method == "error"
        assert result.error == "Test error"
        assert not result.is_successful

    def test_create_error_route_result(self):
        """Test creation of error route result."""
        result = create_error_route_result("Test error", "error")

        assert result.total_distance_km == 0.0
        assert result.total_time_hours == 0.0
        assert result.waypoint_distances == []
        assert result.calculation_method == "error"
        assert result.error == "Test error"
        assert not result.is_successful
        assert not result.network_available


if __name__ == "__main__":
    pytest.main([__file__])
