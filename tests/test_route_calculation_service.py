"""
Optimized unit tests for RouteCalculationService with no hanging network calls.

Tests basic functionality only, avoiding OSMnx network downloads.
Complex routing tests are covered by demo requirements.
"""

import pytest
from unittest.mock import Mock, patch

from services.route_calculation import (
    RouteCalculationService, DistanceResult, RouteResult,
    CoordinateValidationError, RouteCalculationError
)


class TestRouteCalculationServiceBasic:
    """Minimal test cases for RouteCalculationService without network operations."""

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

    def test_calculate_distance_haversine_fallback(self):
        """Test distance calculation falls back to Haversine when OSMnx unavailable."""
        # Force OSMnx to be unavailable
        with patch.object(self.service, 'osmnx_available', False):
            result = self.service.calculate_distance(self.atlanta, self.ringgold)

            assert result.is_successful
            assert result.calculation_method == "haversine"
            assert result.distance_km == 120.5
            assert result.drive_time_hours is not None
            assert not result.used_road_network

    def test_service_basic_functionality(self):
        """Test that service has required functionality."""
        # Test that service has expected attributes/methods
        assert hasattr(self.service, 'calculate_distance')
        assert hasattr(self.service, 'cache')
        assert hasattr(self.service, 'config')
        assert hasattr(self.service, 'osmnx_available')

    def test_fallback_speed_configuration(self):
        """Test fallback speed configuration."""
        config = {'fallback_speed_kmh': 100.0}
        service = RouteCalculationService(config)
        
        # Test Haversine calculation uses configured speed
        with patch.object(service, 'osmnx_available', False):
            result = service.calculate_distance(self.atlanta, self.ringgold)
            
            # Drive time should use the configured speed
            expected_time = 120.5 / 100.0  # distance / speed
            assert abs(result.drive_time_hours - expected_time) < 0.1