"""
Unit tests for RouteCalculationService with mocked OSMnx calls.

Tests the basic distance calculation functionality with OSMnx integration
and fallback to Haversine calculations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from services.route_calculation import (
    RouteCalculationService, DistanceResult, RouteResult,
    CoordinateValidationError, RouteCalculationError
)


class TestRouteCalculationService:
    """Test cases for RouteCalculationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = RouteCalculationService()

        # Create mock locations
        self.atlanta = Mock()
        self.atlanta.lat = 33.7490
        self.atlanta.lng = -84.3880

        self.ringgold = Mock()
        self.ringgold.lat = 34.9161
        self.ringgold.lng = -85.1077

        # Mock distance_to method for Haversine fallback
        self.atlanta.distance_to = Mock(return_value=120.5)
        self.ringgold.distance_to = Mock(return_value=120.5)

    def test_service_initialization(self):
        """Test service initialization."""
        service = RouteCalculationService()
        assert service is not None
        assert hasattr(service, 'cache')
        assert hasattr(service, 'config')

    def test_service_initialization_with_config(self):
        """Test service initialization with custom config."""
        config = {
            'cache_enabled': False,
            'fallback_speed_kmh': 90.0,
            'base_padding_km': 15.0
        }
        service = RouteCalculationService(config)
        assert service.config['fallback_speed_kmh'] == 90.0
        assert service.config['base_padding_km'] == 15.0

    def test_calculate_distance_invalid_locations(self):
        """Test distance calculation with invalid locations."""
        # Test with None locations
        result = self.service.calculate_distance(None, self.atlanta)
        assert not result.is_successful
        assert "cannot be None" in result.error

        # Test with invalid coordinates
        invalid_location = Mock()
        invalid_location.lat = 91.0  # Invalid latitude
        invalid_location.lng = -84.3880

        result = self.service.calculate_distance(invalid_location, self.atlanta)
        assert not result.is_successful
        assert "Latitude must be between" in result.error

    def test_calculate_distance_haversine_fallback_osmnx_unavailable(self):
        """Test distance calculation falls back to Haversine when OSMnx unavailable."""
        # Mock OSMnx as unavailable
        with patch.object(self.service, 'osmnx_available', False):
            result = self.service.calculate_distance(self.atlanta, self.ringgold)

            assert result.is_successful
            assert result.calculation_method == "haversine"
            assert result.distance_km == 120.5
            assert result.drive_time_hours is not None
            assert not result.used_road_network

    @patch('services.route_calculation.ox')
    @patch('services.route_calculation.nx')
    def test_calculate_distance_osmnx_success(self, mock_nx, mock_ox):
        """Test successful OSMnx distance calculation."""
        # Mock OSMnx as available
        with patch.object(self.service, 'osmnx_available', True):
            # Mock network graph
            mock_graph = Mock()
            mock_ox.graph_from_bbox.return_value = mock_graph
            mock_ox.nearest_nodes.side_effect = [123, 456]  # orig_node, dest_node

            # Mock shortest path calculation
            mock_route = [123, 234, 345, 456]
            mock_nx.shortest_path.return_value = mock_route
            mock_nx.shortest_path_length.return_value = 125000  # 125 km in meters

            # Mock graph edge data for drive time calculation
            mock_graph.__getitem__ = Mock()
            edge_data = {0: {'length': 25000, 'highway': 'primary', 'maxspeed': '70'}}
            mock_graph.__getitem__.return_value = {456: edge_data}

            result = self.service.calculate_distance(self.atlanta, self.ringgold)

            assert result.is_successful
            assert result.calculation_method == "osmnx"
            assert result.distance_km == 125.0
            assert result.drive_time_hours is not None
            assert result.used_road_network
            assert result.route_nodes == mock_route

    @patch('services.route_calculation.ox')
    def test_calculate_distance_osmnx_no_path(self, mock_ox):
        """Test OSMnx calculation when no path exists between locations."""
        # Mock OSMnx as available
        with patch.object(self.service, 'osmnx_available', True):
            # Mock network graph
            mock_graph = Mock()
            mock_ox.graph_from_bbox.return_value = mock_graph
            mock_ox.nearest_nodes.side_effect = [123, 456]

            # Mock NetworkXNoPath exception
            import networkx as nx
            with patch('services.route_calculation.nx.shortest_path',
                      side_effect=nx.NetworkXNoPath("No path")):

                result = self.service.calculate_distance(self.atlanta, self.ringgold)

                assert result.is_successful
                assert result.calculation_method == "haversine"
                assert "No road path found" in result.error

    @patch('services.route_calculation.ox')
    def test_calculate_distance_osmnx_error_fallback(self, mock_ox):
        """Test OSMnx calculation falls back to Haversine on error."""
        # Mock OSMnx as available
        with patch.object(self.service, 'osmnx_available', True):
            # Mock OSMnx to raise an exception
            mock_ox.graph_from_bbox.side_effect = Exception("Network download failed")

            result = self.service.calculate_distance(self.atlanta, self.ringgold)

            assert result.is_successful
            assert result.calculation_method == "haversine"
            assert "Network download failed" in result.error

    def test_calculate_distance_large_bounding_box_fallback(self):
        """Test fallback when bounding box is too large."""
        # Create locations very far apart
        far_location = Mock()
        far_location.lat = 60.0  # Very far north
        far_location.lng = -120.0  # Very far west
        far_location.distance_to = Mock(return_value=3000.0)

        # Mock OSMnx as available
        with patch.object(self.service, 'osmnx_available', True):
            result = self.service.calculate_distance(self.atlanta, far_location)

            assert result.is_successful
            assert result.calculation_method == "haversine"
            assert "Bounding box too large" in result.error

    @patch('services.route_calculation.ox')
    def test_calculate_distance_cached_network(self, mock_ox):
        """Test distance calculation using cached network."""
        # Mock OSMnx as available
        with patch.object(self.service, 'osmnx_available', True):
            # Mock cached network
            mock_graph = Mock()
            with patch.object(self.service.cache, 'get_network', return_value=mock_graph):
                mock_ox.nearest_nodes.side_effect = [123, 456]

                # Mock shortest path calculation
                with patch('services.route_calculation.nx.shortest_path', return_value=[123, 456]):
                    with patch('services.route_calculation.nx.shortest_path_length', return_value=100000):

                        result = self.service.calculate_distance(self.atlanta, self.ringgold)

                        # Should not call graph_from_bbox since we have cached network
                        mock_ox.graph_from_bbox.assert_not_called()
                        assert result.is_successful
                        assert result.calculation_method == "osmnx"

    def test_haversine_calculation_method(self):
        """Test the internal Haversine calculation method."""
        result = self.service._calculate_haversine_distance(self.atlanta, self.ringgold)

        assert result.is_successful
        assert result.calculation_method == "haversine"
        assert result.distance_km == 120.5
        assert result.drive_time_hours is not None

        # Check drive time calculation
        expected_time = 120.5 / 80.0  # distance / default speed
        assert abs(result.drive_time_hours - expected_time) < 0.01

    def test_haversine_calculation_with_fallback_reason(self):
        """Test Haversine calculation with fallback reason."""
        result = self.service._calculate_haversine_distance(
            self.atlanta, self.ringgold, fallback_reason="Test fallback"
        )

        assert result.is_successful
        assert result.error == "Fallback used: Test fallback"

    def test_get_edge_speed_maxspeed_kmh(self):
        """Test edge speed extraction with maxspeed in km/h."""
        edge_data = {'maxspeed': '70'}
        speed = self.service._get_edge_speed(edge_data)
        assert speed == 70.0

    def test_get_edge_speed_maxspeed_mph(self):
        """Test edge speed extraction with maxspeed in mph."""
        edge_data = {'maxspeed': '45 mph'}
        speed = self.service._get_edge_speed(edge_data)
        expected_kmh = 45 * 1.60934
        assert abs(speed - expected_kmh) < 0.1

    def test_get_edge_speed_highway_type(self):
        """Test edge speed extraction using highway type."""
        edge_data = {'highway': 'motorway'}
        speed = self.service._get_edge_speed(edge_data)
        assert speed == 110.0  # Default motorway speed

        edge_data = {'highway': 'residential'}
        speed = self.service._get_edge_speed(edge_data)
        assert speed == 30.0  # Default residential speed

    def test_get_edge_speed_highway_list(self):
        """Test edge speed extraction with highway type as list."""
        edge_data = {'highway': ['primary', 'trunk']}
        speed = self.service._get_edge_speed(edge_data)
        assert speed == 70.0  # Should use first highway type (primary)

    def test_get_edge_speed_clamping(self):
        """Test edge speed clamping to reasonable values."""
        # Test very high speed gets clamped
        edge_data = {'maxspeed': '200'}
        speed = self.service._get_edge_speed(edge_data)
        assert speed == 130.0  # Should be clamped to max

        # Test very low speed gets clamped
        edge_data = {'maxspeed': '1'}
        speed = self.service._get_edge_speed(edge_data)
        assert speed == 5.0  # Should be clamped to min

    def test_get_default_speed_for_highway(self):
        """Test default speed assignment for highway types."""
        assert self.service._get_default_speed_for_highway('motorway') == 110
        assert self.service._get_default_speed_for_highway('primary') == 70
        assert self.service._get_default_speed_for_highway('residential') == 30
        assert self.service._get_default_speed_for_highway('unknown_type') == 50

    def test_network_drive_time_calculation(self):
        """Test network-based drive time calculation."""
        # Mock route and graph
        route = [123, 234, 345]
        mock_graph = Mock()

        # Mock edge data
        edge_data_1 = {0: {'length': 50000, 'highway': 'primary'}}  # 50km at 70 km/h
        edge_data_2 = {0: {'length': 30000, 'maxspeed': '60'}}      # 30km at 60 km/h

        mock_graph.__getitem__ = Mock()
        mock_graph.__getitem__.side_effect = [
            {234: edge_data_1},  # First edge
            {345: edge_data_2}   # Second edge
        ]

        drive_time = self.service._calculate_network_drive_time(mock_graph, route)

        # Expected: (50/70) + (30/60) = 0.714 + 0.5 = 1.214 hours
        expected_time = (50.0 / 70.0) + (30.0 / 60.0)
        assert abs(drive_time - expected_time) < 0.01

    def test_network_drive_time_calculation_error(self):
        """Test network drive time calculation with error."""
        route = [123, 234]
        mock_graph = MagicMock()

        # Mock graph to raise exception
        mock_graph.__getitem__.side_effect = Exception("Graph error")

        drive_time = self.service._calculate_network_drive_time(mock_graph, route)
        assert drive_time == 0.0  # Should return 0 on error


class TestRouteCalculationServiceIntegration:
    """Integration tests for RouteCalculationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = RouteCalculationService()

        # Create test locations (Atlanta to Ringgold route from existing tests)
        self.atlanta = Mock()
        self.atlanta.lat = 33.7490
        self.atlanta.lng = -84.3880
        self.atlanta.distance_to = Mock(return_value=120.5)

        self.ringgold = Mock()
        self.ringgold.lat = 34.9161
        self.ringgold.lng = -85.1077
        self.ringgold.distance_to = Mock(return_value=120.5)

    def test_distance_calculation_consistency(self):
        """Test that distance calculations are consistent."""
        # Calculate distance multiple times
        result1 = self.service.calculate_distance(self.atlanta, self.ringgold)
        result2 = self.service.calculate_distance(self.atlanta, self.ringgold)

        assert result1.is_successful
        assert result2.is_successful
        assert result1.distance_km == result2.distance_km
        assert result1.calculation_method == result2.calculation_method

    def test_distance_calculation_symmetry(self):
        """Test that distance calculation is symmetric (A->B == B->A)."""
        result_ab = self.service.calculate_distance(self.atlanta, self.ringgold)
        result_ba = self.service.calculate_distance(self.ringgold, self.atlanta)

        assert result_ab.is_successful
        assert result_ba.is_successful
        # Distance should be the same regardless of direction
        assert abs(result_ab.distance_km - result_ba.distance_km) < 0.1

    def test_zero_distance_same_location(self):
        """Test distance calculation for same location."""
        # Mock the distance_to method to return 0 for same location
        self.atlanta.distance_to = Mock(return_value=0.0)

        result = self.service.calculate_distance(self.atlanta, self.atlanta)

        assert result.is_successful
        # Distance should be very small (essentially zero)
        assert result.distance_km < 0.1

    def test_service_error_recovery(self):
        """Test service recovers from errors gracefully."""
        # Test with completely invalid location
        invalid_location = "not a location object"

        result = self.service.calculate_distance(invalid_location, self.atlanta)

        # Should return error result, not crash
        assert not result.is_successful
        assert result.error is not None
        assert result.distance_km == 0.0


class TestMultiWaypointRouteCalculation:
    """Test cases for multi-waypoint route calculation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = RouteCalculationService()

        # Create test locations for multi-waypoint routes
        self.atlanta = Mock()
        self.atlanta.lat = 33.7490
        self.atlanta.lng = -84.3880
        self.atlanta.distance_to = Mock(return_value=120.5)

        self.macon = Mock()
        self.macon.lat = 32.8407
        self.macon.lng = -83.6324
        self.macon.distance_to = Mock(return_value=85.2)

        self.savannah = Mock()
        self.savannah.lat = 32.0835
        self.savannah.lng = -81.0998
        self.savannah.distance_to = Mock(return_value=160.8)

        self.ringgold = Mock()
        self.ringgold.lat = 34.9161
        self.ringgold.lng = -85.1077
        self.ringgold.distance_to = Mock(return_value=120.5)

        # Mock distance_to method for all combinations
        self._setup_distance_mocks()

    def _setup_distance_mocks(self):
        """Set up distance mocks for all location pairs."""
        # Atlanta distances
        self.atlanta.distance_to = Mock(side_effect=lambda other: {
            self.macon: 120.5,
            self.savannah: 250.0,
            self.ringgold: 180.0,
            self.atlanta: 0.0
        }.get(other, 100.0))

        # Macon distances
        self.macon.distance_to = Mock(side_effect=lambda other: {
            self.atlanta: 120.5,
            self.savannah: 160.8,
            self.ringgold: 200.0,
            self.macon: 0.0
        }.get(other, 100.0))

        # Savannah distances
        self.savannah.distance_to = Mock(side_effect=lambda other: {
            self.atlanta: 250.0,
            self.macon: 160.8,
            self.ringgold: 350.0,
            self.savannah: 0.0
        }.get(other, 100.0))

        # Ringgold distances
        self.ringgold.distance_to = Mock(side_effect=lambda other: {
            self.atlanta: 180.0,
            self.macon: 200.0,
            self.savannah: 350.0,
            self.ringgold: 0.0
        }.get(other, 100.0))

    def test_calculate_route_distance_two_waypoints(self):
        """Test route calculation with two waypoints (simple case)."""
        waypoints = [self.atlanta, self.macon]

        result = self.service.calculate_route_distance(waypoints)

        assert result.is_successful
        assert len(result.waypoint_distances) == 1
        assert result.waypoint_distances[0] == 120.5
        assert result.total_distance_km == 120.5
        assert result.total_time_hours > 0
        assert result.num_waypoints == 2
        assert result.validate_consistency()

    def test_calculate_route_distance_three_waypoints(self):
        """Test route calculation with three waypoints."""
        waypoints = [self.atlanta, self.macon, self.savannah]

        result = self.service.calculate_route_distance(waypoints)

        assert result.is_successful
        assert len(result.waypoint_distances) == 2
        assert result.waypoint_distances[0] == 120.5  # Atlanta -> Macon
        assert result.waypoint_distances[1] == 160.8  # Macon -> Savannah
        assert result.total_distance_km == 281.3  # 120.5 + 160.8
        assert result.num_waypoints == 3
        assert result.validate_consistency()

        # Check that stop time was added for intermediate waypoint (Macon)
        expected_drive_time = (120.5 + 160.8) / 80.0  # distance / speed
        expected_stop_time = 1 * 0.25  # 1 intermediate stop * 15 minutes
        expected_total_time = expected_drive_time + expected_stop_time
        assert abs(result.total_time_hours - expected_total_time) < 0.01

    def test_calculate_route_distance_four_waypoints(self):
        """Test route calculation with four waypoints."""
        waypoints = [self.atlanta, self.macon, self.savannah, self.ringgold]

        result = self.service.calculate_route_distance(waypoints)

        assert result.is_successful
        assert len(result.waypoint_distances) == 3
        assert result.num_waypoints == 4
        assert result.validate_consistency()

        # Check that stop time was added for 2 intermediate waypoints
        expected_stop_time = 2 * 0.25  # 2 intermediate stops * 15 minutes
        assert result.total_time_hours > expected_stop_time

    def test_calculate_route_distance_empty_waypoints(self):
        """Test route calculation with empty waypoints list."""
        result = self.service.calculate_route_distance([])

        assert not result.is_successful
        assert "empty" in result.error.lower()

    def test_calculate_route_distance_single_waypoint(self):
        """Test route calculation with single waypoint."""
        result = self.service.calculate_route_distance([self.atlanta])

        assert not result.is_successful
        assert "at least 2 locations" in result.error.lower()

    def test_calculate_route_distance_invalid_waypoint(self):
        """Test route calculation with invalid waypoint."""
        invalid_location = Mock()
        invalid_location.lat = 91.0  # Invalid latitude
        invalid_location.lng = -84.3880

        waypoints = [self.atlanta, invalid_location]
        result = self.service.calculate_route_distance(waypoints)

        assert not result.is_successful
        assert "latitude must be between" in result.error.lower()

    def test_calculate_route_distance_segment_calculation_failure(self):
        """Test route calculation when a segment calculation fails."""
        # Mock calculate_distance to fail for one segment
        original_method = self.service.calculate_distance

        def mock_calculate_distance(loc1, loc2):
            if loc1 == self.atlanta and loc2 == self.macon:
                return DistanceResult(
                    distance_km=0.0,
                    calculation_method="error",
                    error="Mock calculation failure"
                )
            return original_method(loc1, loc2)

        self.service.calculate_distance = mock_calculate_distance

        waypoints = [self.atlanta, self.macon, self.savannah]
        result = self.service.calculate_route_distance(waypoints)

        assert not result.is_successful
        assert "segment 0 calculation failed" in result.error.lower()

    def test_optimize_waypoint_order_no_optimization_needed(self):
        """Test waypoint optimization with only 2 waypoints."""
        waypoints = [self.atlanta, self.macon]
        optimized = self.service._optimize_waypoint_order(waypoints)

        assert optimized == waypoints

    def test_optimize_waypoint_order_three_waypoints(self):
        """Test waypoint optimization with 3 waypoints."""
        # Original order: Atlanta -> Savannah -> Macon
        # Optimal order should be: Atlanta -> Macon -> Savannah
        # (since Macon is closer to Atlanta than Savannah)
        waypoints = [self.atlanta, self.savannah, self.macon]
        optimized = self.service._optimize_waypoint_order(waypoints)

        assert len(optimized) == 3
        assert optimized[0] == self.atlanta  # Start point unchanged
        assert optimized[-1] == self.macon   # End point unchanged
        assert optimized[1] == self.savannah # Intermediate point

    def test_optimize_waypoint_order_four_waypoints(self):
        """Test waypoint optimization with 4 waypoints."""
        waypoints = [self.atlanta, self.savannah, self.ringgold, self.macon]
        optimized = self.service._optimize_waypoint_order(waypoints)

        assert len(optimized) == 4
        assert optimized[0] == self.atlanta  # Start point unchanged
        assert optimized[-1] == self.macon   # End point unchanged
        # Intermediate points should be optimized
        assert len(optimized[1:-1]) == 2

    def test_calculate_route_distance_with_optimization(self):
        """Test route calculation with waypoint optimization enabled."""
        waypoints = [self.atlanta, self.savannah, self.macon]

        result = self.service.calculate_route_distance(waypoints, optimize_order=True)

        assert result.is_successful
        assert len(result.waypoint_distances) == 2
        assert result.validate_consistency()

    def test_calculate_route_distance_with_validation_success(self):
        """Test route calculation with validation for normal distances."""
        waypoints = [self.atlanta, self.macon, self.savannah]

        result = self.service.calculate_route_distance_with_validation(waypoints)

        assert result.is_successful
        assert result.validate_consistency()

    def test_calculate_route_distance_with_validation_unreachable(self):
        """Test route calculation with validation for unreachable segments."""
        # Create a very distant location
        distant_location = Mock()
        distant_location.lat = 60.0  # Very far north
        distant_location.lng = -120.0  # Very far west
        distant_location.distance_to = Mock(return_value=5000.0)  # 5000 km away

        # Mock atlanta's distance_to method to return 5000 km to distant_location
        self.atlanta.distance_to = Mock(side_effect=lambda other: {
            distant_location: 5000.0,
            self.macon: 120.5,
            self.savannah: 250.0,
            self.ringgold: 180.0,
            self.atlanta: 0.0
        }.get(other, 100.0))

        waypoints = [self.atlanta, distant_location]

        result = self.service.calculate_route_distance_with_validation(
            waypoints, max_segment_distance_km=1000.0
        )

        assert not result.is_successful
        assert "unreachable segments" in result.error.lower()

    def test_route_result_properties(self):
        """Test RouteResult properties and methods."""
        waypoints = [self.atlanta, self.macon, self.savannah]
        result = self.service.calculate_route_distance(waypoints)

        assert result.is_successful
        assert result.num_waypoints == 3
        assert result.get_longest_segment_km() >= result.get_shortest_segment_km()
        assert result.get_average_speed_kmh() > 0
        assert result.validate_consistency()

    def test_route_calculation_consistency(self):
        """Test that route calculations are consistent across multiple calls."""
        waypoints = [self.atlanta, self.macon, self.savannah]

        result1 = self.service.calculate_route_distance(waypoints)
        result2 = self.service.calculate_route_distance(waypoints)

        assert result1.is_successful
        assert result2.is_successful
        assert result1.total_distance_km == result2.total_distance_km
        assert result1.total_time_hours == result2.total_time_hours
        assert result1.waypoint_distances == result2.waypoint_distances

    def test_route_calculation_mixed_methods(self):
        """Test route calculation when segments use different calculation methods."""
        # Mock one segment to use OSMnx and another to use Haversine
        original_method = self.service.calculate_distance

        def mock_calculate_distance(loc1, loc2):
            if loc1 == self.atlanta and loc2 == self.macon:
                return DistanceResult(
                    distance_km=120.5,
                    calculation_method="osmnx",
                    drive_time_hours=1.5
                )
            else:
                return DistanceResult(
                    distance_km=160.8,
                    calculation_method="haversine",
                    drive_time_hours=2.0
                )

        self.service.calculate_distance = mock_calculate_distance

        waypoints = [self.atlanta, self.macon, self.savannah]
        result = self.service.calculate_route_distance(waypoints)

        assert result.is_successful
        assert result.calculation_method == "mixed"
        assert result.validate_consistency()

    def test_waypoint_optimization_error_handling(self):
        """Test waypoint optimization with distance calculation errors."""
        # Mock distance_to to raise exception
        self.atlanta.distance_to = Mock(side_effect=Exception("Distance calculation error"))

        waypoints = [self.atlanta, self.macon, self.savannah]
        optimized = self.service._optimize_waypoint_order(waypoints)

        # Should return original order on optimization failure
        assert optimized == waypoints

    def test_complex_multi_stop_route(self):
        """Test complex multi-stop route with many waypoints."""
        # Create a 5-waypoint route
        waypoint5 = Mock()
        waypoint5.lat = 31.5804
        waypoint5.lng = -84.1557
        waypoint5.distance_to = Mock(return_value=95.0)

        waypoints = [self.atlanta, self.macon, self.savannah, self.ringgold, waypoint5]

        result = self.service.calculate_route_distance(waypoints)

        assert result.is_successful
        assert len(result.waypoint_distances) == 4
        assert result.num_waypoints == 5
        assert result.validate_consistency()

        # Check that stop time was added for 3 intermediate waypoints
        expected_stop_time = 3 * 0.25  # 3 intermediate stops * 15 minutes
        assert result.total_time_hours > expected_stop_time

        # Verify all segments are positive distances
        assert all(d > 0 for d in result.waypoint_distances)


if __name__ == "__main__":
    pytest.main([__file__])
