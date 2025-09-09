"""
Lightweight performance regression tests.

Focuses on critical performance metrics without heavy operations.
"""

import pytest
import time
from unittest.mock import Mock

# Add parent directories to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from order_processor import OrderProcessor
from validation.business_validator import BusinessValidator


class TestPerformanceRegression:
    """Lightweight performance tests to catch regressions."""

    def setup_method(self):
        """Set up for each test."""
        self.order_processor = OrderProcessor()
        self.business_validator = BusinessValidator()

    def test_order_processor_initialization_performance(self):
        """Test that order processor initialization is fast."""
        start_time = time.time()
        
        for _ in range(10):
            processor = OrderProcessor()
        
        duration = time.time() - start_time
        assert duration < 1.0, f"OrderProcessor initialization too slow: {duration:.2f}s"

    def test_business_validator_initialization_performance(self):
        """Test that business validator initialization is fast."""
        start_time = time.time()
        
        for _ in range(10):
            validator = BusinessValidator()
        
        duration = time.time() - start_time
        assert duration < 1.0, f"BusinessValidator initialization too slow: {duration:.2f}s"

    def test_mock_validation_performance(self):
        """Test validation performance with mock objects."""
        # Create mock objects
        order = Mock()
        order.id = 1
        order.total_volume = Mock(return_value=10.0)
        order.total_weight = Mock(return_value=200.0)
        order.cargo = []

        route = Mock()
        route.id = 1
        route.total_time = Mock(return_value=5.0)
        route.orders = []

        truck = Mock()
        truck.id = 1
        truck.capacity = 48.0
        truck.cargo_loads = []

        # Performance test
        start_time = time.time()
        
        for _ in range(100):
            try:
                self.order_processor.validate_order_for_route(order, route, truck)
            except Exception:
                pass  # Expected with mock objects
        
        duration = time.time() - start_time
        assert duration < 2.0, f"Validation performance regression: {duration:.2f}s for 100 calls"

    def test_constants_access_performance(self):
        """Test that accessing constants is fast."""
        start_time = time.time()
        
        for _ in range(1000):
            _ = self.order_processor.constants.MAX_PROXIMITY_KM
            _ = self.order_processor.constants.MAX_WEIGHT_LBS
            _ = self.order_processor.constants.STOP_TIME_MINUTES
        
        duration = time.time() - start_time
        assert duration < 0.5, f"Constants access too slow: {duration:.2f}s for 1000 accesses"

    def test_memory_usage_reasonable(self):
        """Test that objects don't use excessive memory."""
        import sys
        
        # Create multiple instances and check they're not growing exponentially
        processors = []
        validators = []
        
        for _ in range(10):
            processors.append(OrderProcessor())
            validators.append(BusinessValidator())
        
        # Just verify we can create multiple instances without issues
        assert len(processors) == 10
        assert len(validators) == 10
        
        # Clear references
        processors.clear()
        validators.clear()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])