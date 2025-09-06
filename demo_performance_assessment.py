#!/usr/bin/env python3
"""
Performance Assessment Demo for Digital Freight Matching System

Demonstrates the comprehensive performance assessment and monitoring capabilities
including profiling, load testing, memory monitoring, and benchmarking.

This script showcases all the performance assessment features implemented
to meet requirements 4.1-4.4 of the MVP finalization specification.
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from performance.performance_test_runner import PerformanceTestRunner
from performance.performance_assessor import PerformanceAssessor
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


def demo_basic_performance_profiling():
    """Demonstrate basic performance profiling capabilities"""
    print("\n" + "="*50)
    print("DEMO: Basic Performance Profiling")
    print("="*50)

    assessor = PerformanceAssessor()

    # Create test data
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

    print("Profiling single order processing...")
    metrics = assessor.profile_order_processing([order], routes, trucks)

    print(f"Execution Time: {metrics.execution_time_ms:.1f}ms")
    print(f"Memory Usage: {metrics.memory_usage_mb:.1f}MB")
    print(f"CPU Usage: {metrics.cpu_usage_percent:.1f}%")
    print(f"Success: {metrics.success}")
    print(f"Meets 5-second requirement: {metrics.execution_time_ms <= 5000}")

    if metrics.additional_data:
        print(f"Success Rate: {metrics.additional_data.get('success_rate_percent', 0):.1f}%")


def demo_load_testing():
    """Demonstrate load testing capabilities"""
    print("\n" + "="*50)
    print("DEMO: Load Testing")
    print("="*50)

    assessor = PerformanceAssessor()

    # Create test data
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

    def order_generator():
        packages = [Package(volume=10.0, weight=20.0, type=CargoType.STANDARD)]
        cargo = Cargo(order_id=1, packages=packages)
        return Order(
            id=1,
            location_origin_id=0,
            location_destiny_id=1,
            location_origin=locations[0],
            location_destiny=locations[1],
            cargo=[cargo]
        )

    print("Running load test with 3 concurrent users, 10 operations each...")
    load_results = assessor.run_load_tests(
        order_generator=order_generator,
        routes=routes,
        trucks=trucks,
        concurrent_users=3,
        operations_per_user=10
    )

    print(f"Total Operations: {load_results.total_operations}")
    print(f"Successful: {load_results.successful_operations}")
    print(f"Failed: {load_results.failed_operations}")
    print(f"Error Rate: {load_results.error_rate_percent:.1f}%")
    print(f"Average Response Time: {load_results.average_response_time_ms:.1f}ms")
    print(f"Throughput: {load_results.throughput_ops_per_second:.2f} ops/sec")
    print(f"Peak Memory: {load_results.memory_peak_mb:.1f}MB")


def demo_memory_monitoring():
    """Demonstrate memory monitoring capabilities"""
    print("\n" + "="*50)
    print("DEMO: Memory Monitoring")
    print("="*50)

    assessor = PerformanceAssessor()

    print("Monitoring memory usage for 30 seconds...")
    print("(This will sample memory every 2 seconds)")

    memory_report = assessor.monitor_memory_usage(
        duration_seconds=30,
        sample_interval_seconds=2.0
    )

    print(f"Peak Memory: {memory_report.peak_memory_mb:.1f}MB")
    print(f"Current Memory: {memory_report.current_memory_mb:.1f}MB")
    print(f"Memory Growth: {memory_report.memory_growth_mb:.1f}MB")
    print(f"Samples Collected: {memory_report.samples_count}")
    print(f"Potential Leaks Detected: {len(memory_report.potential_leaks)}")

    if memory_report.potential_leaks:
        print("Potential Memory Issues:")
        for leak in memory_report.potential_leaks[:3]:  # Show first 3
            print(f"  - {leak}")


def demo_comprehensive_assessment():
    """Demonstrate comprehensive performance assessment"""
    print("\n" + "="*50)
    print("DEMO: Comprehensive Performance Assessment")
    print("="*50)

    runner = PerformanceTestRunner()

    print("Running comprehensive performance test suite...")
    print("This includes:")
    print("  - Single order profiling")
    print("  - Batch processing tests")
    print("  - Load testing")
    print("  - Memory monitoring")
    print("  - Benchmark comparisons")
    print("  - Compliance checking")

    results = runner.run_comprehensive_performance_tests()

    # Print summary
    runner.print_summary_report(results)

    return results


# TODO: This function 'main' is duplicated in db_manager.py

# TODO: This function 'main' is duplicated in db_manager.py

def main():
    """Main demo function"""
    print("Digital Freight Matching System")
    print("Performance Assessment and Monitoring Demo")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Demo 1: Basic Performance Profiling
        demo_basic_performance_profiling()

        # Demo 2: Load Testing
        demo_load_testing()

        # Demo 3: Memory Monitoring
        demo_memory_monitoring()

        # Demo 4: Comprehensive Assessment
        results = demo_comprehensive_assessment()

        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("All performance assessment capabilities demonstrated successfully!")
        print("\n_Key Features Demonstrated:")
        print("✓ Order processing performance profiling")
        print("✓ Load testing with concurrent users")
        print("✓ Memory usage monitoring and leak detection")
        print("✓ Benchmark testing and regression detection")
        print("✓ Comprehensive compliance checking")
        print("✓ Automated report generation")

        # Show compliance status
        if results and 'compliance_check' in results:
            compliance = results['compliance_check']
            print(f"\n_System Compliance Status:")
            print(f"  5-second requirement: {'✓' if compliance.get('meets_5_second_requirement') else '✗'}")
            print(f"  Batch processing stable: {'✓' if compliance.get('batch_processing_stable') else '✗'}")
            print(f"  Acceptable error rate: {'✓' if compliance.get('acceptable_error_rate') else '✗'}")
            print(f"  Memory stable: {'✓' if compliance.get('memory_stable') else '✗'}")
            print(f"  Overall compliant: {'✓' if compliance.get('overall_compliant') else '✗'}")

        print(f"\n_Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n_Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
