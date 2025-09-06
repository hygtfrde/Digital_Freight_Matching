"""
Performance Test Runner for Digital Freight Matching System

Comprehensive test runner that demonstrates all performance assessment capabilities
including profiling, load testing, memory monitoring, and benchmarking.
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance.performance_assessor import PerformanceAssessor
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


class PerformanceTestRunner:
    """
    Comprehensive performance test runner
    
    Executes all performance assessment capabilities and generates
    detailed reports for system evaluation.
    """
    
    def __init__(self):
        """Initialize the test runner"""
        self.assessor = PerformanceAssessor()
        self.test_data = self._create_test_data()
        
    def _create_test_data(self) -> Dict[str, Any]:
        """Create comprehensive test data for performance testing"""
        # Test locations (Georgia cities from business requirements)
        locations = [
            Location(lat=33.7490, lng=-84.3880),  # Atlanta
            Location(lat=32.0835, lng=-81.0998),  # Savannah  
            Location(lat=34.7465, lng=-83.3782),  # Ringgold
            Location(lat=33.4735, lng=-82.0105),  # Augusta
            Location(lat=31.5804, lng=-84.1557),  # Albany
            Location(lat=32.4609, lng=-84.9877),  # Columbus
        ]
        
        # Test trucks with business specifications
        trucks = [
            Truck(capacity=48.0, autonomy=600.0, type="standard"),
            Truck(capacity=48.0, autonomy=600.0, type="refrigerated"),
            Truck(capacity=48.0, autonomy=600.0, type="standard"),
            Truck(capacity=48.0, autonomy=600.0, type="refrigerated"),
            Truck(capacity=48.0, autonomy=600.0, type="standard"),
        ]
        
        # Test routes (5 contract routes from business requirements)
        routes = [
            Route(location_origin_id=0, location_destiny_id=2, 
                  location_origin=locations[0], location_destiny=locations[2], truck_id=0),
            Route(location_origin_id=0, location_destiny_id=3,
                  location_origin=locations[0], location_destiny=locations[3], truck_id=1),
            Route(location_origin_id=0, location_destiny_id=1,
                  location_origin=locations[0], location_destiny=locations[1], truck_id=2),
            Route(location_origin_id=0, location_destiny_id=4,
                  location_origin=locations[0], location_destiny=locations[4], truck_id=3),
            Route(location_origin_id=0, location_destiny_id=5,
                  location_origin=locations[0], location_destiny=locations[5], truck_id=4),
        ]
        
        return {
            'locations': locations,
            'trucks': trucks,
            'routes': routes
        }
    
    def create_test_order(self, complexity: str = "medium") -> Order:
        """Create test order with specified complexity"""
        locations = self.test_data['locations']
        
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
            location_origin=locations[0],
            location_destiny=locations[1],
            cargo=[cargo]
        )    

    def run_comprehensive_performance_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive performance test suite
        
        Returns:
            Dictionary containing all test results and analysis
        """
        print("Starting comprehensive performance assessment...")
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_summary': {},
            'profiling_results': {},
            'load_test_results': {},
            'memory_monitoring': {},
            'benchmark_results': {},
            'compliance_check': {},
            'recommendations': []
        }
        
        try:
            # 1. Single Order Processing Performance
            print("\n1. Testing single order processing performance...")
            single_order = self.create_test_order("medium")
            single_metrics = self.assessor.profile_order_processing(
                orders=[single_order],
                routes=self.test_data['routes'],
                trucks=self.test_data['trucks']
            )
            results['profiling_results']['single_order'] = {
                'execution_time_ms': single_metrics.execution_time_ms,
                'memory_usage_mb': single_metrics.memory_usage_mb,
                'success': single_metrics.success,
                'meets_5_second_requirement': single_metrics.execution_time_ms <= 5000
            }
            
            # 2. Batch Order Processing Performance
            print("2. Testing batch order processing performance...")
            batch_orders = [self.create_test_order("medium") for _ in range(10)]
            batch_metrics = self.assessor.profile_order_processing(
                orders=batch_orders,
                routes=self.test_data['routes'],
                trucks=self.test_data['trucks']
            )
            results['profiling_results']['batch_processing'] = {
                'execution_time_ms': batch_metrics.execution_time_ms,
                'memory_usage_mb': batch_metrics.memory_usage_mb,
                'success': batch_metrics.success,
                'orders_processed': len(batch_orders),
                'success_rate': batch_metrics.additional_data.get('success_rate_percent', 0)
            }
            
            # 3. Load Testing
            print("3. Running load tests...")
            load_results = self.assessor.run_load_tests(
                order_generator=lambda: self.create_test_order("medium"),
                routes=self.test_data['routes'],
                trucks=self.test_data['trucks'],
                concurrent_users=5,
                operations_per_user=20
            )
            results['load_test_results'] = {
                'total_operations': load_results.total_operations,
                'successful_operations': load_results.successful_operations,
                'error_rate_percent': load_results.error_rate_percent,
                'average_response_time_ms': load_results.average_response_time_ms,
                'throughput_ops_per_second': load_results.throughput_ops_per_second,
                'memory_peak_mb': load_results.memory_peak_mb
            }
            
            # 4. Memory Monitoring (short duration for demo)
            print("4. Monitoring memory usage...")
            memory_report = self.assessor.monitor_memory_usage(
                duration_seconds=60,  # 1 minute for demo
                sample_interval_seconds=2.0
            )
            results['memory_monitoring'] = {
                'peak_memory_mb': memory_report.peak_memory_mb,
                'memory_growth_mb': memory_report.memory_growth_mb,
                'potential_leaks_count': len(memory_report.potential_leaks),
                'samples_collected': memory_report.samples_count,
                'monitoring_duration': memory_report.monitoring_duration_seconds
            }
            
            # 5. Benchmark Testing
            print("5. Running benchmark tests...")
            
            # Set baseline metrics
            self.assessor.set_baseline_metrics("single_order_benchmark", single_metrics)
            
            def benchmark_single_order():
                order = self.create_test_order("medium")
                return self.assessor.profile_order_processing(
                    orders=[order],
                    routes=self.test_data['routes'],
                    trucks=self.test_data['trucks']
                )
            
            def benchmark_complex_order():
                order = self.create_test_order("complex")
                return self.assessor.profile_order_processing(
                    orders=[order],
                    routes=self.test_data['routes'],
                    trucks=self.test_data['trucks']
                )
            
            benchmark_scenarios = {
                "single_order_benchmark": benchmark_single_order,
                "complex_order_benchmark": benchmark_complex_order
            }
            
            benchmark_results = self.assessor.run_benchmarks(benchmark_scenarios)
            results['benchmark_results'] = {}
            
            for name, result in benchmark_results.items():
                results['benchmark_results'][name] = {
                    'meets_requirements': result.meets_requirements,
                    'regression_detected': result.regression_detected,
                    'improvement_detected': result.improvement_detected,
                    'performance_change_percent': result.performance_change_percent,
                    'recommendations': result.recommendations
                }
            
            # 6. Compliance Check
            print("6. Checking compliance with business requirements...")
            compliance = self._check_compliance(results)
            results['compliance_check'] = compliance
            
            # 7. Generate Recommendations
            recommendations = self._generate_recommendations(results)
            results['recommendations'] = recommendations
            
            # 8. Test Summary
            results['test_summary'] = {
                'total_tests_run': 6,
                'single_order_performance_ok': results['profiling_results']['single_order']['meets_5_second_requirement'],
                'batch_processing_ok': results['profiling_results']['batch_processing']['success'],
                'load_test_ok': results['load_test_results']['error_rate_percent'] < 10,
                'memory_stable': results['memory_monitoring']['potential_leaks_count'] == 0,
                'benchmarks_passed': all(r['meets_requirements'] for r in results['benchmark_results'].values()),
                'overall_compliance': compliance['overall_compliant']
            }
            
            print("\n_Performance assessment completed successfully!")
            
        except Exception as e:
            print(f"Error during performance testing: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _check_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with business requirements"""
        compliance = {}
        
        # Requirement 4.1: Order processing < 5 seconds
        single_order_time = results['profiling_results']['single_order']['execution_time_ms']
        compliance['meets_5_second_requirement'] = single_order_time <= 5000
        
        # Requirement 4.2: Batch processing without degradation
        batch_success_rate = results['profiling_results']['batch_processing']['success_rate']
        compliance['batch_processing_stable'] = batch_success_rate >= 95
        
        # Requirement 4.3: Error handling (low error rate)
        load_error_rate = results['load_test_results']['error_rate_percent']
        compliance['acceptable_error_rate'] = load_error_rate <= 10
        
        # Requirement 4.4: Stable performance (no memory leaks)
        memory_leaks = results['memory_monitoring']['potential_leaks_count']
        compliance['memory_stable'] = memory_leaks == 0
        
        # Overall compliance
        compliance['overall_compliant'] = all([
            compliance['meets_5_second_requirement'],
            compliance['batch_processing_stable'],
            compliance['acceptable_error_rate'],
            compliance['memory_stable']
        ])
        
        return compliance
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on test results"""
        recommendations = []
        
        # Check single order performance
        single_time = results['profiling_results']['single_order']['execution_time_ms']
        if single_time > 5000:
            recommendations.append(
                f"Single order processing time ({single_time:.1f}ms) exceeds 5-second requirement. "
                "Consider optimizing order validation logic."
            )
        elif single_time > 3000:
            recommendations.append(
                f"Single order processing time ({single_time:.1f}ms) is approaching the 5-second limit. "
                "Monitor for potential performance degradation."
            )
        
        # Check batch processing
        batch_success = results['profiling_results']['batch_processing']['success_rate']
        if batch_success < 95:
            recommendations.append(
                f"Batch processing success rate ({batch_success:.1f}%) is below 95%. "
                "Review error handling and validation logic."
            )
        
        # Check load test results
        error_rate = results['load_test_results']['error_rate_percent']
        if error_rate > 10:
            recommendations.append(
                f"Load test error rate ({error_rate:.1f}%) exceeds 10%. "
                "System may not handle concurrent load well."
            )
        
        throughput = results['load_test_results']['throughput_ops_per_second']
        if throughput < 1.0:
            recommendations.append(
                f"Low throughput ({throughput:.2f} ops/sec) under load. "
                "Consider performance optimization or scaling strategies."
            )
        
        # Check memory usage
        memory_growth = results['memory_monitoring']['memory_growth_mb']
        if memory_growth > 50:
            recommendations.append(
                f"Memory growth ({memory_growth:.1f}MB) during monitoring suggests potential memory leak. "
                "Review object lifecycle and garbage collection."
            )
        
        leak_count = results['memory_monitoring']['potential_leaks_count']
        if leak_count > 0:
            recommendations.append(
                f"Detected {leak_count} potential memory leaks. "
                "Review memory allocation patterns and ensure proper cleanup."
            )
        
        # Check benchmark results
        for name, benchmark in results['benchmark_results'].items():
            if benchmark['regression_detected']:
                recommendations.append(
                    f"Performance regression detected in {name}. "
                    f"Performance degraded by {benchmark['performance_change_percent']:.1f}%."
                )
        
        if not recommendations:
            recommendations.append("All performance tests passed. System meets performance requirements.")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save performance test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_results_{timestamp}.json"
        
        filepath = os.path.join("performance", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Performance results saved to: {filepath}")
        return filepath
    
    def print_summary_report(self, results: Dict[str, Any]):
        """Print a formatted summary report"""
        print("\n" + "="*60)
        print("PERFORMANCE ASSESSMENT SUMMARY REPORT")
        print("="*60)
        
        print(f"\n_Test Timestamp: {results['timestamp']}")
        
        # Test Summary
        summary = results['test_summary']
        print(f"\n_Overall Status: {'PASS' if summary.get('overall_compliance', False) else 'FAIL'}")
        print(f"Tests Run: {summary.get('total_tests_run', 0)}")
        
        # Individual Test Results
        print("\n_Individual Test Results:")
        print(f"  Single Order Performance: {'PASS' if summary.get('single_order_performance_ok') else 'FAIL'}")
        print(f"  Batch Processing: {'PASS' if summary.get('batch_processing_ok') else 'FAIL'}")
        print(f"  Load Testing: {'PASS' if summary.get('load_test_ok') else 'FAIL'}")
        print(f"  Memory Stability: {'PASS' if summary.get('memory_stable') else 'FAIL'}")
        print(f"  Benchmarks: {'PASS' if summary.get('benchmarks_passed') else 'FAIL'}")
        
        # Key Metrics
        print("\n_Key Performance Metrics:")
        single_time = results['profiling_results']['single_order']['execution_time_ms']
        print(f"  Single Order Time: {single_time:.1f}ms (limit: 5000ms)")
        
        batch_rate = results['profiling_results']['batch_processing']['success_rate']
        print(f"  Batch Success Rate: {batch_rate:.1f}% (target: >95%)")
        
        error_rate = results['load_test_results']['error_rate_percent']
        print(f"  Load Test Error Rate: {error_rate:.1f}% (target: <10%)")
        
        throughput = results['load_test_results']['throughput_ops_per_second']
        print(f"  Throughput: {throughput:.2f} ops/sec")
        
        memory_growth = results['memory_monitoring']['memory_growth_mb']
        print(f"  Memory Growth: {memory_growth:.1f}MB")
        
        # Recommendations
        print("\n_Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main function to run performance tests"""
    runner = PerformanceTestRunner()
    
    print("Digital Freight Matching System - Performance Assessment")
    print("=" * 60)
    
    # Run comprehensive tests
    results = runner.run_comprehensive_performance_tests()
    
    # Print summary report
    runner.print_summary_report(results)
    
    # Save results
    filepath = runner.save_results(results)
    
    print(f"\n_Detailed results saved to: {filepath}")
    print("Performance assessment complete!")


if __name__ == "__main__":
    main()