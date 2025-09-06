"""
Performance Assessment and Monitoring System for Digital Freight Matching

Implements comprehensive performance profiling, benchmarking, and monitoring
for order processing, load testing, memory usage tracking, and regression testing.

Requirements addressed:
- 4.1: Order processing execution time measurement (< 5 seconds per order)
- 4.2: Batch processing capabilities without performance degradation
- 4.3: Clear error messages and graceful failure handling
- 4.4: Stable performance over extended periods
"""

import time
import psutil
import gc
import threading
import statistics
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import tracemalloc
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Order, Route, Truck
from order_processor import OrderProcessor



@dataclass
class PerformanceMetrics:
    """Detailed performance metrics for a single operation"""
    operation_name: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestResults:
    """Results from load testing operations"""
    test_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_duration_seconds: float
    average_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    percentile_95_ms: float
    throughput_ops_per_second: float
    memory_peak_mb: float
    cpu_peak_percent: float
    error_rate_percent: float
    errors: List[str] = field(default_factory=list)


@dataclass
class MemoryReport:
    """Memory usage monitoring report"""
    process_id: int
    peak_memory_mb: float
    current_memory_mb: float
    memory_growth_mb: float
    gc_collections: Dict[str, int]
    potential_leaks: List[str]
    monitoring_duration_seconds: float
    samples_count: int
    memory_timeline: List[Tuple[datetime, float]] = field(default_factory=list)


@dataclass
class BenchmarkResults:
    """Benchmark comparison results"""
    benchmark_name: str
    current_performance: PerformanceMetrics
    baseline_performance: Optional[PerformanceMetrics]
    performance_change_percent: Optional[float]
    regression_detected: bool
    improvement_detected: bool
    meets_requirements: bool
    recommendations: List[str] = field(default_factory=list)


class PerformanceAssessor:
    """
    Comprehensive performance assessment and monitoring system

    Provides profiling, load testing, memory monitoring, and benchmarking
    capabilities for the Digital Freight Matching system.
    """

    def __init__(self):
        """Initialize the performance assessor"""
        self.order_processor = OrderProcessor()
        self.baseline_metrics: Dict[str, PerformanceMetrics] = {}
        self.performance_history: List[PerformanceMetrics] = []
        self.memory_monitor_active = False
        self.memory_samples: List[Tuple[datetime, float]] = []

        # Performance thresholds from requirements
        self.max_order_processing_time_ms = 5000  # 5 seconds per order
        self.max_acceptable_error_rate = 5.0  # 5% error rate
        self.memory_leak_threshold_mb = 100  # 100MB growth indicates potential leak

    def profile_order_processing(self, orders: List[Order], routes: List[Route],
                               trucks: List[Truck]) -> PerformanceMetrics:
        """
        Profile order processing execution time and resource usage

        Args:
            orders: List of orders to process
            routes: Available routes
            trucks: Available trucks

        Returns:
            PerformanceMetrics with detailed performance data
        """
        operation_name = f"order_processing_{len(orders)}_orders"

        # Start memory and CPU monitoring
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Start execution timing
        start_time = time.perf_counter()
        start_cpu_times = process.cpu_times()

        success = True
        error_message = None
        additional_data = {}

        try:
            # Process orders using the order processor
            results = self.order_processor.process_order_batch(orders, routes, trucks)

            # Calculate success metrics
            successful_orders = sum(1 for result in results.values() if result.is_valid)
            total_orders = len(orders)
            success_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0

            additional_data = {
                'total_orders': total_orders,
                'successful_orders': successful_orders,
                'success_rate_percent': success_rate,
                'validation_errors': sum(len(result.errors) for result in results.values())
            }

        except Exception as e:
            success = False
            error_message = str(e)
            additional_data['exception_type'] = type(e).__name__

        # Calculate execution time
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        # Calculate memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage_mb = final_memory - initial_memory

        # Calculate CPU usage (approximate)
        end_cpu_times = process.cpu_times()
        cpu_time_used = (end_cpu_times.user - start_cpu_times.user) + (end_cpu_times.system - start_cpu_times.system)
        wall_time = end_time - start_time
        cpu_usage_percent = (cpu_time_used / wall_time * 100) if wall_time > 0 else 0

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            success=success,
            error_message=error_message,
            additional_data=additional_data
        )

        # Store in history
        self.performance_history.append(metrics)

        return metrics

    def run_load_tests(self, order_generator: Callable[[], Order], routes: List[Route],
                      trucks: List[Truck], concurrent_users: int = 10,
                      operations_per_user: int = 100) -> LoadTestResults:
        """
        Run load testing with concurrent order processing

        Args:
            order_generator: Function that generates test orders
            routes: Available routes
            trucks: Available trucks
            concurrent_users: Number of concurrent threads
            operations_per_user: Operations per thread

        Returns:
            LoadTestResults with comprehensive load test metrics
        """
        test_name = f"load_test_{concurrent_users}users_{operations_per_user}ops"
        total_operations = concurrent_users * operations_per_user

        # Track performance metrics
        response_times = []
        errors = []
        successful_operations = 0
        failed_operations = 0

        # Memory and CPU monitoring
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = initial_memory
        peak_cpu = 0.0

        def worker_thread(thread_id: int) -> List[float]:
            """Worker thread for load testing"""
            thread_response_times = []

            for op_num in range(operations_per_user):
                try:
                    # Generate test order
                    order = order_generator()

                    # Time the operation
                    start_time = time.perf_counter()

                    # Process single order
                    result = self.order_processor.validate_order_for_route(
                        order, routes[0] if routes else None, trucks[0] if trucks else None
                    )

                    end_time = time.perf_counter()
                    response_time_ms = (end_time - start_time) * 1000
                    thread_response_times.append(response_time_ms)

                    if result.is_valid:
                        nonlocal successful_operations
                        successful_operations += 1
                    else:
                        nonlocal failed_operations
                        failed_operations += 1

                except Exception as e:
                    failed_operations += 1
                    errors.append(f"Thread {thread_id}, Op {op_num}: {str(e)}")
                    thread_response_times.append(0.0)  # Failed operation

            return thread_response_times

        # Start load test
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit all worker threads
            futures = [executor.submit(worker_thread, i) for i in range(concurrent_users)]

            # Monitor system resources during test
            monitor_thread = threading.Thread(target=self._monitor_resources_during_test,
                                            args=(lambda: peak_memory, lambda: peak_cpu))
            monitor_thread.daemon = True
            monitor_thread.start()

            # Collect results
            for future in as_completed(futures):
                try:
                    thread_times = future.result()
                    response_times.extend(thread_times)

                    # Update peak memory
                    current_memory = process.memory_info().rss / 1024 / 1024
                    peak_memory = max(peak_memory, current_memory)

                    # Update peak CPU
                    current_cpu = process.cpu_percent()
                    peak_cpu = max(peak_cpu, current_cpu)

                except Exception as e:
                    errors.append(f"Thread execution error: {str(e)}")

        end_time = time.perf_counter()
        total_duration = end_time - start_time

        # Calculate statistics
        valid_response_times = [t for t in response_times if t > 0]

        if valid_response_times:
            avg_response_time = statistics.mean(valid_response_times)
            min_response_time = min(valid_response_times)
            max_response_time = max(valid_response_times)
            percentile_95 = statistics.quantiles(valid_response_times, n=20)[18]  # 95th percentile
        else:
            avg_response_time = min_response_time = max_response_time = percentile_95 = 0.0

        throughput = total_operations / total_duration if total_duration > 0 else 0.0
        error_rate = (failed_operations / total_operations * 100) if total_operations > 0 else 0.0

        return LoadTestResults(
            test_name=test_name,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            total_duration_seconds=total_duration,
            average_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            percentile_95_ms=percentile_95,
            throughput_ops_per_second=throughput,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            error_rate_percent=error_rate,
            errors=errors[:100]  # Limit error list size
        )

    def monitor_memory_usage(self, duration_seconds: int = 300,
                           sample_interval_seconds: float = 1.0) -> MemoryReport:
        """
        Monitor memory usage over time with leak detection

        Args:
            duration_seconds: How long to monitor (default 5 minutes)
            sample_interval_seconds: How often to sample memory

        Returns:
            MemoryReport with memory usage analysis
        """
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = initial_memory

        # Start memory tracing
        tracemalloc.start()
        initial_gc_stats = {str(i): gc.get_count()[i] for i in range(3)}

        memory_samples = []
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)

        self.memory_monitor_active = True

        try:
            while datetime.now() < end_time and self.memory_monitor_active:
                current_time = datetime.now()
                current_memory = process.memory_info().rss / 1024 / 1024

                memory_samples.append((current_time, current_memory))
                peak_memory = max(peak_memory, current_memory)

                time.sleep(sample_interval_seconds)

        finally:
            self.memory_monitor_active = False

        # Analyze memory usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Get garbage collection stats
        final_gc_stats = {str(i): gc.get_count()[i] for i in range(3)}
        gc_collections = {
            gen: final_gc_stats[gen] - initial_gc_stats[gen]
            for gen in initial_gc_stats
        }

        # Detect potential memory leaks
        potential_leaks = []
        if memory_growth > self.memory_leak_threshold_mb:
            potential_leaks.append(f"Memory growth of {memory_growth:.1f}MB exceeds threshold")

        # Check for consistent memory growth pattern
        if len(memory_samples) > 10:
            recent_samples = memory_samples[-10:]
            early_samples = memory_samples[:10]

            recent_avg = statistics.mean([sample[1] for sample in recent_samples])
            early_avg = statistics.mean([sample[1] for sample in early_samples])

            if recent_avg > early_avg * 1.2:  # 20% growth
                potential_leaks.append("Consistent memory growth pattern detected")

        # Get memory tracing snapshot
        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')[:10]

            for stat in top_stats:
                if stat.size > 1024 * 1024:  # > 1MB
                    potential_leaks.append(f"Large allocation: {stat.size / 1024 / 1024:.1f}MB at {stat.traceback}")
        except Exception:
            pass  # Memory tracing might not be available

        tracemalloc.stop()

        return MemoryReport(
            process_id=process.pid,
            peak_memory_mb=peak_memory,
            current_memory_mb=final_memory,
            memory_growth_mb=memory_growth,
            gc_collections=gc_collections,
            potential_leaks=potential_leaks,
            monitoring_duration_seconds=duration_seconds,
            samples_count=len(memory_samples),
            memory_timeline=memory_samples
        )

    def run_benchmarks(self, test_scenarios: Dict[str, Callable[[], PerformanceMetrics]]) -> Dict[str, BenchmarkResults]:
        """
        Run benchmark tests comparing against baseline performance

        Args:
            test_scenarios: Dictionary of test name to test function

        Returns:
            Dictionary of benchmark results
        """
        results = {}

        for test_name, test_function in test_scenarios.items():
            try:
                # Run the test
                current_metrics = test_function()

                # Get baseline if available
                baseline_metrics = self.baseline_metrics.get(test_name)

                # Calculate performance change
                performance_change = None
                if baseline_metrics and baseline_metrics.execution_time_ms > 0:
                    performance_change = (
                        (current_metrics.execution_time_ms - baseline_metrics.execution_time_ms)
                        / baseline_metrics.execution_time_ms * 100
                    )

                # Detect regression/improvement
                regression_detected = False
                improvement_detected = False

                if performance_change is not None:
                    if performance_change > 20:  # 20% slower
                        regression_detected = True
                    elif performance_change < -10:  # 10% faster
                        improvement_detected = True

                # Check if meets requirements
                meets_requirements = (
                    current_metrics.execution_time_ms <= self.max_order_processing_time_ms and
                    current_metrics.success
                )

                # Generate recommendations
                recommendations = []
                if current_metrics.execution_time_ms > self.max_order_processing_time_ms:
                    recommendations.append(f"Execution time {current_metrics.execution_time_ms:.1f}ms exceeds 5-second limit")

                if regression_detected:
                    recommendations.append(f"Performance regression detected: {performance_change:.1f}% slower")

                if current_metrics.memory_usage_mb > 100:
                    recommendations.append(f"High memory usage: {current_metrics.memory_usage_mb:.1f}MB")

                if not current_metrics.success:
                    recommendations.append(f"Test failed: {current_metrics.error_message}")

                results[test_name] = BenchmarkResults(
                    benchmark_name=test_name,
                    current_performance=current_metrics,
                    baseline_performance=baseline_metrics,
                    performance_change_percent=performance_change,
                    regression_detected=regression_detected,
                    improvement_detected=improvement_detected,
                    meets_requirements=meets_requirements,
                    recommendations=recommendations
                )

            except Exception as e:
                # Create error result
                error_metrics = PerformanceMetrics(
                    operation_name=test_name,
                    execution_time_ms=0.0,
                    memory_usage_mb=0.0,
                    cpu_usage_percent=0.0,
                    success=False,
                    error_message=str(e)
                )

                results[test_name] = BenchmarkResults(
                    benchmark_name=test_name,
                    current_performance=error_metrics,
                    baseline_performance=None,
                    performance_change_percent=None,
                    regression_detected=False,
                    improvement_detected=False,
                    meets_requirements=False,
                    recommendations=[f"Benchmark failed: {str(e)}"]
                )

        return results

    def set_baseline_metrics(self, test_name: str, metrics: PerformanceMetrics):
        """Set baseline performance metrics for comparison"""
        self.baseline_metrics[test_name] = metrics

    def get_performance_history(self, operation_name: Optional[str] = None) -> List[PerformanceMetrics]:
        """Get performance history, optionally filtered by operation name"""
        if operation_name:
            return [m for m in self.performance_history if m.operation_name == operation_name]
        return self.performance_history.copy()

    def stop_memory_monitoring(self):
        """Stop active memory monitoring"""
        self.memory_monitor_active = False

    def _monitor_resources_during_test(self, peak_memory_ref, peak_cpu_ref):
        """Internal method to monitor resources during load testing"""
        process = psutil.Process()

        while True:
            try:
                current_memory = process.memory_info().rss / 1024 / 1024
                current_cpu = process.cpu_percent()

                # Update peaks (this is a simplified approach)
                # In a real implementation, you'd use proper shared state

                time.sleep(0.5)  # Sample every 500ms

            except Exception:
                break  # Exit if process monitoring fails

    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance assessment report

        Returns:
            Dictionary containing performance analysis and recommendations
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'metrics_history': [],
            'recommendations': [],
            'compliance': {}
        }

        if self.performance_history:
            # Calculate summary statistics
            recent_metrics = self.performance_history[-10:]  # Last 10 operations

            execution_times = [m.execution_time_ms for m in recent_metrics if m.success]
            memory_usage = [m.memory_usage_mb for m in recent_metrics if m.success]
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics) * 100

            if execution_times:
                report['summary'] = {
                    'average_execution_time_ms': statistics.mean(execution_times),
                    'max_execution_time_ms': max(execution_times),
                    'min_execution_time_ms': min(execution_times),
                    'success_rate_percent': success_rate,
                    'average_memory_usage_mb': statistics.mean(memory_usage) if memory_usage else 0,
                    'total_operations': len(self.performance_history)
                }

            # Check compliance with requirements
            avg_time = statistics.mean(execution_times) if execution_times else 0
            report['compliance'] = {
                'meets_5_second_requirement': avg_time <= self.max_order_processing_time_ms,
                'acceptable_success_rate': success_rate >= (100 - self.max_acceptable_error_rate),
                'performance_stable': max(execution_times) - min(execution_times) <= 2000 if len(execution_times) > 1 else True
            }

            # Generate recommendations
            if avg_time > self.max_order_processing_time_ms:
                report['recommendations'].append(
                    f"Average execution time ({avg_time:.1f}ms) exceeds 5-second requirement"
                )

            if success_rate < (100 - self.max_acceptable_error_rate):
                report['recommendations'].append(
                    f"Success rate ({success_rate:.1f}%) below acceptable threshold"
                )

            # Add recent metrics to report
            report['metrics_history'] = [
                {
                    'operation': m.operation_name,
                    'execution_time_ms': m.execution_time_ms,
                    'memory_usage_mb': m.memory_usage_mb,
                    'success': m.success,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in recent_metrics
            ]

        return report
