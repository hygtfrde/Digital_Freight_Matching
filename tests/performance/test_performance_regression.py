"""
Performance Regression Tests for Digital Freight Matching System

Implements automated performance regression testing to prevent performance
degradation and ensure system meets performance requirements over time.

Requirements addressed:
- 4.1: Order processing execution time measurement (< 5 seconds per order)
- 4.2: Batch processing capabilities without performance degradation
- 4.3: Clear error messages and graceful failure handling
- 4.4: Stable performance over extended periods
"""

import unittest
import time
import statistics
from typing import List, Dict, Any
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from performance.performance_assessor import PerformanceAssessor, PerformanceMetrics
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType
from order_processor import OrderProcessor


class TestPerformanceRegression(unittest.TestCase):
    """
    Performance regression test suite
    
    Tests system performance against established baselines and requirements
    to detect performance degradation over time.
    """
    
    def setUp(self):
        """Set up test environment"""
        self.assessor = PerformanceAssessor()
        self.order_processor = OrderProcessor()
        
        # Create test data
        self.test_locations = [
            Location(lat=33.7490, lng=-84.3880),  # Atlanta
            Location(lat=32.0835, lng=-81.0998),  # Savannah
            Location(lat=33.2085, lng=-87.5691),  # Tuscaloosa
            Location(lat=32.4609, lng=-84.9877),  # Columbus
            Location(lat=31.5804, lng=-84.1557),  # Albany
        ]
        
        self.test_trucks = [
            Truck(capacity=48.0, autonomy=600.0, type="standard"),
            Truck(capacity=48.0, autonomy=600.0, type="refrigerated"),
        ]
        
        self.test_routes = [
            Route(
                location_origin_id=0,
                location_destiny_id=1,
                location_origin=self.test_locations[0],
                location_destiny=self.test_locations[1],
                truck_id=0
            ),
            Route(
                location_origin_id=0,
                location_destiny_id=2,
                location_origin=self.test_locations[0],
                location_destiny=self.test_locations[2],
                truck_id=1
            ),
        ]
        
        # Performance thresholds
        self.max_single_order_time_ms = 5000  # 5 seconds
        self.max_batch_processing_time_ms = 10000  # 10 seconds for batch
        self.max_acceptable_regression_percent = 20  # 20% performance degradation
        self.min_success_rate_percent = 95  # 95% success rate
    
    def _create_test_order(self, complexity: str = "simple") -> Order:
        """Create test order with varying complexity"""
        if complexity == "simple":
            packages = [Package(volume=5.0, weight=10.0, type=CargoType.STANDARD)]
        elif complexity == "medium":
            packages = [
                Package(volume=10.0, weight=20.0, type=CargoType.STANDARD),
                Package(volume=5.0, weight=15.0, type=CargoType.FRAGILE),
            ]
        else:  # complex
            packages = [
                Package(volume=15.0, weight=30.0, type=CargoType.STANDARD),
                Package(volume=8.0, weight=25.0, type=CargoType.FRAGILE),
                Package(volume=12.0, weight=40.0, type=CargoType.REFRIGERATED),
            ]
        
        cargo = Cargo(order_id=1, packages=packages)
        
        return Order(
            id=1,
            location_origin_id=0,
            location_destiny_id=1,
            location_origin=self.test_locations[0],
            location_destiny=self.test_locations[1],
            cargo=[cargo]
        )
    
    def test_single_order_processing_performance(self):
        """Test that single order processing meets 5-second requirement"""
        order = self._create_test_order("medium")
        
        # Measure performance
        metrics = self.assessor.profile_order_processing(
            orders=[order],
            routes=self.test_routes,
            trucks=self.test_trucks
        )
        
        # Assert performance requirements
        self.assertTrue(metrics.success, f"Order processing failed: {metrics.error_message}")
        self.assertLessEqual(
            metrics.execution_time_ms, 
            self.max_single_order_time_ms,
            f"Single order processing took {metrics.execution_time_ms:.1f}ms, exceeds 5-second limit"
        )
        
        # Check additional metrics
        self.assertGreater(metrics.additional_data.get('success_rate_percent', 0), 90)
        
    def test_batch_order_processing_performance(self):
        """Test batch processing performance without degradation"""
        # Create batch of orders with varying complexity
        orders = [
            self._create_test_order("simple") for _ in range(5)
        ] + [
            self._create_test_order("medium") for _ in range(3)
        ] + [
            self._create_test_order("complex") for _ in range(2)
        ]
        
        # Measure batch processing performance
        metrics = self.assessor.profile_order_processing(
            orders=orders,
            routes=self.test_routes,
            trucks=self.test_trucks
        )
        
        # Assert batch processing requirements
        self.assertTrue(metrics.success, f"Batch processing failed: {metrics.error_message}")
        self.assertLessEqual(
            metrics.execution_time_ms,
            self.max_batch_processing_time_ms,
            f"Batch processing took {metrics.execution_time_ms:.1f}ms, exceeds 10-second limit"
        )
        
        # Check success rate
        success_rate = metrics.additional_data.get('success_rate_percent', 0)
        self.assertGreaterEqual(
            success_rate,
            self.min_success_rate_percent,
            f"Success rate {success_rate:.1f}% below minimum {self.min_success_rate_percent}%"
        )
    
    def test_performance_consistency_over_time(self):
        """Test that performance remains consistent over multiple runs"""
        execution_times = []
        success_rates = []
        
        # Run multiple iterations
        for i in range(5):
            order = self._create_test_order("medium")
            
            metrics = self.assessor.profile_order_processing(
                orders=[order],
                routes=self.test_routes,
                trucks=self.test_trucks
            )
            
            if metrics.success:
                execution_times.append(metrics.execution_time_ms)
                success_rates.append(metrics.additional_data.get('success_rate_percent', 0))
        
        # Check consistency
        self.assertGreater(len(execution_times), 0, "No successful runs to analyze")
        
        # Calculate coefficient of variation (std dev / mean)
        if len(execution_times) > 1:
            mean_time = statistics.mean(execution_times)
            std_dev = statistics.stdev(execution_times)
            coefficient_of_variation = (std_dev / mean_time) * 100
            
            # Performance should be consistent (CV < 30%)
            self.assertLess(
                coefficient_of_variation,
                30.0,
                f"Performance inconsistent: CV = {coefficient_of_variation:.1f}%"
            )
        
        # All runs should meet time requirements
        max_time = max(execution_times)
        self.assertLessEqual(
            max_time,
            self.max_single_order_time_ms,
            f"Worst case time {max_time:.1f}ms exceeds limit"
        )
    
    def test_load_testing_performance(self):
        """Test system performance under load"""
        def order_generator():
            return self._create_test_order("medium")
        
        # Run load test with moderate load
        load_results = self.assessor.run_load_tests(
            order_generator=order_generator,
            routes=self.test_routes,
            trucks=self.test_trucks,
            concurrent_users=5,
            operations_per_user=20
        )
        
        # Assert load test requirements
        self.assertGreaterEqual(
            load_results.error_rate_percent,
            0.0,
            "Error rate should be non-negative"
        )
        self.assertLessEqual(
            load_results.error_rate_percent,
            10.0,  # Allow up to 10% error rate under load
            f"Error rate {load_results.error_rate_percent:.1f}% too high under load"
        )
        
        # Check average response time
        self.assertLessEqual(
            load_results.average_response_time_ms,
            self.max_single_order_time_ms,
            f"Average response time {load_results.average_response_time_ms:.1f}ms exceeds limit"
        )
        
        # Check throughput is reasonable
        self.assertGreater(
            load_results.throughput_ops_per_second,
            0.1,  # At least 0.1 operations per second
            "Throughput too low"
        )
    
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during processing"""
        # Run short memory monitoring test
        memory_report = self.assessor.monitor_memory_usage(
            duration_seconds=30,  # Short test for unit testing
            sample_interval_seconds=1.0
        )
        
        # Check for memory leaks
        self.assertLess(
            memory_report.memory_growth_mb,
            50.0,  # Allow up to 50MB growth in short test
            f"Memory growth {memory_report.memory_growth_mb:.1f}MB indicates potential leak"
        )
        
        # Check that we have reasonable number of samples
        self.assertGreater(
            memory_report.samples_count,
            20,  # Should have at least 20 samples in 30 seconds
            "Insufficient memory samples collected"
        )
        
        # Check for leak indicators
        self.assertEqual(
            len([leak for leak in memory_report.potential_leaks if "exceeds threshold" in leak]),
            0,
            f"Memory leak detected: {memory_report.potential_leaks}"
        )
    
    def test_error_handling_performance(self):
        """Test that error handling doesn't significantly impact performance"""
        # Create invalid order (no locations)
        invalid_order = Order(
            id=999,
            location_origin_id=None,
            location_destiny_id=None,
            location_origin=None,
            location_destiny=None,
            cargo=[]
        )
        
        # Measure error handling performance
        start_time = time.perf_counter()
        
        metrics = self.assessor.profile_order_processing(
            orders=[invalid_order],
            routes=self.test_routes,
            trucks=self.test_trucks
        )
        
        end_time = time.perf_counter()
        error_handling_time_ms = (end_time - start_time) * 1000
        
        # Error handling should be fast
        self.assertLessEqual(
            error_handling_time_ms,
            1000.0,  # Error handling should take < 1 second
            f"Error handling took {error_handling_time_ms:.1f}ms, too slow"
        )
        
        # Should have proper error information
        self.assertFalse(metrics.success, "Invalid order should fail processing")
        self.assertIsNotNone(metrics.error_message, "Should have error message")
    
    def test_benchmark_regression_detection(self):
        """Test that benchmark system can detect performance regressions"""
        # Create baseline performance
        baseline_order = self._create_test_order("simple")
        baseline_metrics = self.assessor.profile_order_processing(
            orders=[baseline_order],
            routes=self.test_routes,
            trucks=self.test_trucks
        )
        
        # Set as baseline
        self.assessor.set_baseline_metrics("simple_order_test", baseline_metrics)
        
        # Create test scenarios
        def simple_order_test():
            order = self._create_test_order("simple")
            return self.assessor.profile_order_processing(
                orders=[order],
                routes=self.test_routes,
                trucks=self.test_trucks
            )
        
        test_scenarios = {
            "simple_order_test": simple_order_test
        }
        
        # Run benchmarks
        benchmark_results = self.assessor.run_benchmarks(test_scenarios)
        
        # Check benchmark results
        self.assertIn("simple_order_test", benchmark_results)
        result = benchmark_results["simple_order_test"]
        
        self.assertTrue(result.meets_requirements, "Benchmark should meet requirements")
        self.assertIsNotNone(result.current_performance, "Should have current performance data")
        self.assertIsNotNone(result.baseline_performance, "Should have baseline performance data")
    
    def test_performance_report_generation(self):
        """Test comprehensive performance report generation"""
        # Generate some performance history
        for i in range(3):
            order = self._create_test_order("medium")
            self.assessor.profile_order_processing(
                orders=[order],
                routes=self.test_routes,
                trucks=self.test_trucks
            )
        
        # Generate performance report
        report = self.assessor.generate_performance_report()
        
        # Validate report structure
        self.assertIn('timestamp', report)
        self.assertIn('summary', report)
        self.assertIn('metrics_history', report)
        self.assertIn('recommendations', report)
        self.assertIn('compliance', report)
        
        # Check summary data
        if report['summary']:
            self.assertIn('average_execution_time_ms', report['summary'])
            self.assertIn('success_rate_percent', report['summary'])
            self.assertIn('total_operations', report['summary'])
        
        # Check compliance data
        self.assertIn('meets_5_second_requirement', report['compliance'])
        self.assertIn('acceptable_success_rate', report['compliance'])
        self.assertIn('performance_stable', report['compliance'])


class TestPerformanceAssessorIntegration(unittest.TestCase):
    """
    Integration tests for PerformanceAssessor with real system components
    """
    
    def setUp(self):
        """Set up integration test environment"""
        self.assessor = PerformanceAssessor()
    
    def test_integration_with_order_processor(self):
        """Test integration with OrderProcessor"""
        # Create realistic test data
        locations = [
            Location(lat=33.7490, lng=-84.3880),  # Atlanta
            Location(lat=32.0835, lng=-81.0998),  # Savannah
        ]
        
        trucks = [Truck(capacity=48.0, autonomy=600.0, type="standard")]
        
        routes = [Route(
            location_origin_id=0,
            location_destiny_id=1,
            location_origin=locations[0],
            location_destiny=locations[1],
            truck_id=0
        )]
        
        # Create test order
        packages = [Package(volume=10.0, weight=20.0, type=CargoType.STANDARD)]
        cargo = Cargo(order_id=1, packages=packages)
        order = Order(
            id=1,
            location_origin_id=0,
            location_destiny_id=1,
            location_origin=locations[0],
            location_destiny=locations[1],
            cargo=[cargo]
        )
        
        # Test performance assessment
        metrics = self.assessor.profile_order_processing([order], routes, trucks)
        
        # Validate integration
        self.assertTrue(metrics.success, "Integration test should succeed")
        self.assertGreater(metrics.execution_time_ms, 0, "Should have execution time")
        self.assertIsNotNone(metrics.additional_data, "Should have additional data")


if __name__ == '__main__':
    # Run performance regression tests
    unittest.main(verbosity=2)