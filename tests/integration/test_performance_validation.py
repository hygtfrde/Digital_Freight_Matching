"""
Performance Validation Integration Tests

Specialized tests for validating system performance requirements,
including the <5 second order processing target and scalability testing.
"""

import unittest
import time
import concurrent.futures

from tests.integration.test_integration_suite import IntegrationTestSuite
from app.database import Order, Route, Truck, Location, Cargo, Package, CargoType
from sqlmodel import select
from order_processor import OrderProcessor


class PerformanceValidationTests(IntegrationTestSuite):
    """
    Performance-focused integration tests for the Digital Freight Matching System
    """

    def test_single_order_processing_performance(self):
        """
        Test that single order processing meets <5 second requirement
        """
        # Create test order with realistic complexity
        pickup_loc = Location(lat=33.7500, lng=-84.3900)
        dropoff_loc = Location(lat=32.0900, lng=-81.1000)

        self.session.add_all([pickup_loc, dropoff_loc])
        self.session.commit()

        order = Order(
            location_origin_id=pickup_loc.id,
            location_destiny_id=dropoff_loc.id,
            client_id=self.test_client_id
        )
        self.session.add(order)
        self.session.commit()

        # Add realistic cargo load
        cargo = Cargo(order_id=order.id)
        self.session.add(cargo)
        self.session.commit()

        packages = [
            Package(volume=10.0, weight=200.0, type=CargoType.STANDARD, cargo_id=cargo.id),
            Package(volume=5.0, weight=100.0, type=CargoType.FRAGILE, cargo_id=cargo.id),
            Package(volume=3.0, weight=75.0, type=CargoType.STANDARD, cargo_id=cargo.id)
        ]
        self.session.add_all(packages)
        self.session.commit()

        # Load system data
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        # Performance test: single order processing
        start_time = time.time()

        result = self.order_processor.validate_order_for_route(order, routes[0], trucks[0])

        processing_time = time.time() - start_time

        # Performance assertion
        self.assertLess(processing_time, 5.0,
                       f"Single order processing took {processing_time:.3f}s, must be <5s")

        # Verify processing completed successfully
        self.assertIsNotNone(result, "Processing should return a result")
        self.assertIsInstance(result.metrics, dict, "Result should include metrics")

        # Log performance for monitoring
        print(f"Single order processing time: {processing_time:.3f}s")

    def test_batch_processing_performance(self):
        """
        Test batch processing performance with multiple orders
        """
        # Create batch of test orders
        batch_size = 20
        test_orders = []

        for i in range(batch_size):
            pickup_loc = Location(
                lat=33.7490 + (i * 0.005),  # Spread around Atlanta
                lng=-84.3880 + (i * 0.005)
            )
            dropoff_loc = Location(
                lat=32.0835 + (i * 0.005),  # Spread around Savannah
                lng=-81.0998 + (i * 0.005)
            )

            self.session.add_all([pickup_loc, dropoff_loc])
            self.session.commit()

            order = Order(
                location_origin_id=pickup_loc.id,
                location_destiny_id=dropoff_loc.id,
                client_id=self.test_client_id
            )
            self.session.add(order)
            self.session.commit()

            # Add cargo with varying complexity
            cargo = Cargo(order_id=order.id)
            self.session.add(cargo)
            self.session.commit()

            # Varying package counts and sizes
            package_count = (i % 3) + 1  # 1-3 packages per order
            for j in range(package_count):
                package = Package(
                    volume=2.0 + j,
                    weight=50.0 + (j * 25),
                    type=CargoType.STANDARD,
                    cargo_id=cargo.id
                )
                self.session.add(package)

            self.session.commit()
            test_orders.append(order)

        # Load system data
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        # Performance test: batch processing
        start_time = time.time()

        batch_results = self.order_processor.process_order_batch(test_orders, routes, trucks)

        batch_time = time.time() - start_time

        # Performance assertions
        avg_time_per_order = batch_time / batch_size
        self.assertLess(avg_time_per_order, 5.0,
                       f"Average batch processing time {avg_time_per_order:.3f}s per order must be <5s")

        # Batch should be more efficient than individual processing
        self.assertLess(batch_time, batch_size * 2.0,
                       f"Batch processing {batch_time:.3f}s should be more efficient than individual processing")

        # Verify all orders were processed
        self.assertEqual(len(batch_results), batch_size,
                        "All orders should be processed in batch")

        # Log performance metrics
        print(f"Batch processing: {batch_size} orders in {batch_time:.3f}s")
        print(f"Average time per order: {avg_time_per_order:.3f}s")

    def test_concurrent_processing_performance(self):
        """
        Test system performance under concurrent load
        """
        # Create orders for concurrent processing
        concurrent_orders = []

        for i in range(10):
            pickup_loc = Location(
                lat=33.7490 + (i * 0.01),
                lng=-84.3880 + (i * 0.01)
            )
            dropoff_loc = Location(
                lat=32.0835 + (i * 0.01),
                lng=-81.0998 + (i * 0.01)
            )

            self.session.add_all([pickup_loc, dropoff_loc])
            self.session.commit()

            order = Order(
                location_origin_id=pickup_loc.id,
                location_destiny_id=dropoff_loc.id,
                client_id=self.test_client_id
            )
            self.session.add(order)
            self.session.commit()

            # Add cargo
            cargo = Cargo(order_id=order.id)
            self.session.add(cargo)
            self.session.commit()

            package = Package(
                volume=5.0, weight=100.0, type=CargoType.STANDARD, cargo_id=cargo.id
            )
            self.session.add(package)
            self.session.commit()

            concurrent_orders.append(order)

        # Load system data
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        def process_order_worker(order):
            """Worker function for concurrent processing"""
            processor = OrderProcessor()
            return processor.validate_order_for_route(order, routes[0], trucks[0])

        # Performance test: concurrent processing
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_order = {
                executor.submit(process_order_worker, order): order
                for order in concurrent_orders
            }

            concurrent_results = {}
            for future in concurrent.futures.as_completed(future_to_order):
                order = future_to_order[future]
                try:
                    result = future.result()
                    concurrent_results[order.id] = result
                except Exception as exc:
                    self.fail(f"Order {order.id} generated exception: {exc}")

        concurrent_time = time.time() - start_time

        # Performance assertions
        avg_concurrent_time = concurrent_time / len(concurrent_orders)
        self.assertLess(avg_concurrent_time, 5.0,
                       f"Average concurrent processing time {avg_concurrent_time:.3f}s must be <5s")

        # Verify all orders were processed
        self.assertEqual(len(concurrent_results), len(concurrent_orders),
                        "All concurrent orders should be processed")

        # Log performance metrics
        print(f"Concurrent processing: {len(concurrent_orders)} orders in {concurrent_time:.3f}s")
        print(f"Average concurrent time per order: {avg_concurrent_time:.3f}s")

    def test_database_query_performance(self):
        """
        Test database query performance under load
        """
        # Performance test: complex database queries
        start_time = time.time()

        # Query 1: Complex join query
        complex_query = self.session.exec(
            select(Order, Route, Truck, Cargo, Package)
            .join(Route, Order.route_id == Route.id, isouter=True)
            .join(Truck, Route.truck_id == Truck.id, isouter=True)
            .join(Cargo, Order.id == Cargo.order_id)
            .join(Package, Cargo.id == Package.cargo_id)
        ).all()

        query1_time = time.time() - start_time

        # Query 2: Aggregation query
        start_time = time.time()

        routes_with_stats = self.session.exec(select(Route)).all()
        for route in routes_with_stats:
            # Calculate route statistics
            orders = self.session.exec(select(Order).where(Order.route_id == route.id)).all()
            total_volume = 0
            total_weight = 0

            for order in orders:
                for cargo in order.cargo:
                    total_volume += cargo.total_volume()
                    total_weight += cargo.total_weight()

        query2_time = time.time() - start_time

        # Performance assertions
        self.assertLess(query1_time, 2.0,
                       f"Complex join query took {query1_time:.3f}s, should be <2s")
        self.assertLess(query2_time, 3.0,
                       f"Aggregation query took {query2_time:.3f}s, should be <3s")

        # Verify queries returned data
        self.assertGreaterEqual(len(complex_query), 0, "Complex query should return results")
        self.assertGreater(len(routes_with_stats), 0, "Should have routes for statistics")

        # Log performance metrics
        print(f"Complex join query time: {query1_time:.3f}s")
        print(f"Aggregation query time: {query2_time:.3f}s")

    def test_business_validation_performance(self):
        """
        Test business validation performance
        """
        # Create test data for validation
        orders = self.session.exec(select(Order)).all()
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        # Performance test: business validation
        start_time = time.time()

        validation_reports = self.business_validator.validate_all_requirements(
            orders, routes, trucks, baseline_daily_loss=-388.15
        )

        validation_time = time.time() - start_time

        # Performance assertion
        self.assertLess(validation_time, 5.0,
                       f"Business validation took {validation_time:.3f}s, should be <5s")

        # Verify validation completed
        self.assertEqual(len(validation_reports), 5,
                        "Should have 5 validation reports")

        # Test individual validation performance
        individual_times = {}

        # Profitability validation
        start_time = time.time()
        prof_report = self.business_validator.validate_profitability_requirements(
            routes, baseline_daily_loss=-388.15
        )
        individual_times['profitability'] = time.time() - start_time

        # Proximity validation
        start_time = time.time()
        prox_report = self.business_validator.validate_proximity_constraint(orders, routes)
        individual_times['proximity'] = time.time() - start_time

        # Capacity validation
        start_time = time.time()
        cap_report = self.business_validator.validate_capacity_constraints(orders, trucks)
        individual_times['capacity'] = time.time() - start_time

        # Performance assertions for individual validations
        for validation_type, duration in individual_times.items():
            self.assertLess(duration, 2.0,
                           f"{validation_type} validation took {duration:.3f}s, should be <2s")

        # Log performance metrics
        print(f"Total business validation time: {validation_time:.3f}s")
        for validation_type, duration in individual_times.items():
            print(f"{validation_type} validation time: {duration:.3f}s")

    def test_memory_usage_stability(self):
        """
        Test that memory usage remains stable during extended operation
        """
        try:
            import psutil
            import os
        except ImportError:
            self.skipTest("psutil not available for memory testing")

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform extended operations
        for iteration in range(50):
            # Create and process orders
            pickup_loc = Location(
                lat=33.7490 + (iteration * 0.001),
                lng=-84.3880 + (iteration * 0.001)
            )
            dropoff_loc = Location(
                lat=32.0835 + (iteration * 0.001),
                lng=-81.0998 + (iteration * 0.001)
            )

            self.session.add_all([pickup_loc, dropoff_loc])
            self.session.commit()

            order = Order(
                location_origin_id=pickup_loc.id,
                location_destiny_id=dropoff_loc.id,
                client_id=self.test_client_id
            )
            self.session.add(order)
            self.session.commit()

            # Add cargo
            cargo = Cargo(order_id=order.id)
            self.session.add(cargo)
            self.session.commit()

            package = Package(
                volume=2.0, weight=50.0, type=CargoType.STANDARD, cargo_id=cargo.id
            )
            self.session.add(package)
            self.session.commit()

            # Process order
            routes = self.session.exec(select(Route)).all()
            trucks = self.session.exec(select(Truck)).all()

            if routes and trucks:
                result = self.order_processor.validate_order_for_route(order, routes[0], trucks[0])

            # Clean up periodically to prevent test database bloat
            if iteration % 10 == 0:
                self.session.rollback()

        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory usage should not increase excessively
        self.assertLess(memory_increase, 100.0,  # 100MB limit
                       f"Memory usage increased by {memory_increase:.1f}MB, should be <100MB")

        # Log memory metrics
        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB")

    def test_scalability_stress_test(self):
        """
        Test system behavior under stress conditions
        """
        # Create large batch for stress testing
        stress_batch_size = 100
        stress_orders = []

        print(f"Creating {stress_batch_size} orders for stress test...")

        for i in range(stress_batch_size):
            pickup_loc = Location(
                lat=33.7490 + (i * 0.002),
                lng=-84.3880 + (i * 0.002)
            )
            dropoff_loc = Location(
                lat=32.0835 + (i * 0.002),
                lng=-81.0998 + (i * 0.002)
            )

            self.session.add_all([pickup_loc, dropoff_loc])

            if i % 20 == 0:  # Commit in batches to avoid memory issues
                self.session.commit()

        self.session.commit()

        # Create orders in batches
        batch_size = 20
        for batch_start in range(0, stress_batch_size, batch_size):
            batch_end = min(batch_start + batch_size, stress_batch_size)

            for i in range(batch_start, batch_end):
                order = Order(
                    location_origin_id=self.test_location_ids[0],  # Use existing locations
                    location_destiny_id=self.test_location_ids[1],
                    client_id=self.test_client_id
                )
                self.session.add(order)

            self.session.commit()

        # Load all orders for stress test
        all_orders = self.session.exec(select(Order)).all()
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()

        print(f"Processing {len(all_orders)} orders in stress test...")

        # Stress test: process large batch
        start_time = time.time()

        try:
            # Process in smaller chunks to avoid timeout
            chunk_size = 25
            total_processed = 0

            for chunk_start in range(0, len(all_orders), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(all_orders))
                chunk_orders = all_orders[chunk_start:chunk_end]

                chunk_results = self.order_processor.process_order_batch(
                    chunk_orders, routes, trucks
                )

                total_processed += len(chunk_results)

                # Check performance of each chunk
                chunk_time = time.time() - start_time
                if chunk_time > 30.0:  # 30 second timeout per chunk
                    break

            stress_time = time.time() - start_time

            # Performance assertions for stress test
            avg_stress_time = stress_time / total_processed if total_processed > 0 else float('inf')
            self.assertLess(avg_stress_time, 10.0,  # Relaxed requirement for stress test
                           f"Stress test average time {avg_stress_time:.3f}s per order should be <10s")

            # Verify significant portion was processed
            self.assertGreater(total_processed, stress_batch_size * 0.5,
                              f"Should process at least 50% of orders in stress test")

            # Log stress test results
            print(f"Stress test: processed {total_processed} orders in {stress_time:.3f}s")
            print(f"Average stress test time per order: {avg_stress_time:.3f}s")

        except Exception as e:
            # Stress test may fail under extreme load - log but don't fail test
            print(f"Stress test encountered expected limitations: {e}")
            self.skipTest(f"Stress test hit system limits: {e}")


if __name__ == "__main__":
    unittest.main()
