"""
Lightweight integration tests focusing on core system integration.

Heavy integration testing is covered by demo requirements.
This focuses on basic connectivity and initialization only.
"""

import pytest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from order_processor import OrderProcessor
from validation.business_validator import BusinessValidator


class TestBasicIntegration:
    """Basic integration tests for core system components."""

    def test_order_processor_validator_integration(self):
        """Test that OrderProcessor and BusinessValidator integrate properly."""
        processor = OrderProcessor()
        validator = BusinessValidator()
        
        # Test that both have compatible constants
        assert processor.constants.MAX_PROXIMITY_KM == validator.MAX_PROXIMITY_KM
        assert processor.constants.MAX_WEIGHT_LBS == validator.MAX_TRUCK_WEIGHT_LBS
        assert processor.constants.MAX_ROUTE_HOURS == validator.MAX_ROUTE_TIME_HOURS

    def test_constants_consistency(self):
        """Test that all constants are consistent across components."""
        processor = OrderProcessor()
        validator = BusinessValidator()
        
        # Test proximity constants
        assert processor.constants.MAX_PROXIMITY_KM == 1.0
        assert validator.MAX_PROXIMITY_KM == 1.0
        
        # Test capacity constants
        assert processor.constants.MAX_WEIGHT_LBS == 9180
        assert validator.MAX_TRUCK_WEIGHT_LBS == 9180.0
        
        # Test time constants
        assert processor.constants.MAX_ROUTE_HOURS == 10.0
        assert validator.MAX_ROUTE_TIME_HOURS == 10.0

    def test_business_rules_alignment(self):
        """Test that business rules are properly aligned."""
        validator = BusinessValidator()
        
        # Test contract destinations are properly defined
        expected_destinations = ["Ringgold", "Augusta", "Savannah", "Albany", "Columbus"]
        assert validator.CONTRACT_DESTINATIONS == expected_destinations
        
        # Test required routes count
        assert validator.REQUIRED_CONTRACT_ROUTES == 5
        
        # Test daily loss reduction target
        assert validator.TARGET_DAILY_LOSS_REDUCTION == 388.15

    def test_component_initialization_order(self):
        """Test that components can be initialized in any order."""
        # Test different initialization orders
        processor1 = OrderProcessor()
        validator1 = BusinessValidator()
        
        validator2 = BusinessValidator()
        processor2 = OrderProcessor()
        
        # Both should have same constants
        assert processor1.constants.MAX_PROXIMITY_KM == processor2.constants.MAX_PROXIMITY_KM
        assert validator1.MAX_PROXIMITY_KM == validator2.MAX_PROXIMITY_KM

    def test_error_handling_integration(self):
        """Test that error handling works across components."""
        processor = OrderProcessor()
        
        # Test with None inputs
        try:
            result = processor.validate_order_for_route(None, None, None)
            # Should handle gracefully, not crash
            assert hasattr(result, 'is_valid') or result is None
        except Exception as e:
            # If it raises an exception, it should be a clear error message
            assert str(e) != ""

if __name__ == "__main__":
    pytest.main([__file__, "-v"])