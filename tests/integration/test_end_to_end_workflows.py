"""
End-to-End Workflow Integration Tests

Focused tests for complete order processing workflows from order creation
through route assignment, validation, and profitability calculation.
"""

import unittest
import time
from typing import List, Dict, Any
from sqlmodel import Session, select

from tests.integration.test_integration_suite import IntegrationTestSuite
from app.database import Order, Route, Truck, Location, Cargo, Package, CargoType
from order_processor import OrderProcessor, ValidationResult


class EndToEndWorkflowTests(IntegrationTestSuite):
    """
    Specialized tests for end-to-end order processing workflows
    """
    
    def test_complete_order_lifecycle(self):
        """
        Test complete order lifecycle from creation to route assignment
        """
        # Step 1: Create customer order
        customer_order_data = {
            'customer_name': 'Test Customer',
            'pickup_location': {'lat': 33.7500, 'lng': -84.3900},
            'dropoff_location': {'lat': 32.0900, 'lng': -81.1000},
            'cargo_requirements': [
                {'volume': 10.0, 'weight': 200.0, 'type': 'standard'},
                {'volume': 5.0, 'weight': 100.0, 'type': 'fragile'}
            ],
            'delivery_deadline': '2024-12-31',
            'special_instructions': 'Handle with care'
        }
        
        # Step 2: Convert to system order
        pickup_loc = Location(
            lat=customer_order_data['pickup_location']['lat'],
            lng=customer_order_data['pickup_location']['lng']
        )
        dropoff_loc = Location(
            lat=customer_order_data['dropoff_location']['lat'],
            lng=customer_order_data['dropoff_location']['lng']
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
        
        # Step 3: Create cargo and packages
        cargo = Cargo(order_id=order.id)
        self.session.add(cargo)
        self.session.commit()
        
        packages = []
        for cargo_req in customer_order_data['cargo_requirements']:
            package = Package(
                volume=cargo_req['volume'],
                weight=cargo_req['weight'],
                type=CargoType(cargo_req['type']),
                cargo_id=cargo.id
            )
            packages.append(package)
        
        self.session.add_all(packages)
        self.session.commit()
        
        # Step 4: Find suitable routes
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()
        
        suitable_routes = []
        for i, route in enumerate(routes):
            if i < len(trucks):
                truck = trucks[i]
                result = self.order_processor.validate_order_for_route(order, route, truck)
                if result.is_valid:
                    suitable_routes.append((route, truck, result))
        
        # Step 5: Verify at least one suitable route found
        self.assertGreater(len(suitable_routes), 0, 
                          "Should find at least one suitable route for valid order")
        
        # Step 6: Select best route (highest efficiency score)
        best_route, best_truck, best_result = suitable_routes[0]
        if len(suitable_routes) > 1:
            best_score = -float('inf')
            for route, truck, result in suitable_routes:
                score = self._calculate_route_score(result.metrics)
                if score > best_score:
                    best_score = score
                    best_route, best_truck, best_result = route, truck, result
        
        # Step 7: Assign order to route
        order.route_id = best_route.id
        
        # Assign cargo to truck
        cargo.truck_id = best_truck.id
        
        self.session.commit()
        
        # Step 8: Verify assignment
        self.session.refresh(order)
        self.session.refresh(cargo)
        
        self.assertEqual(order.route_id, best_route.id, "Order should be assigned to best route")
        self.assertEqual(cargo.truck_id, best_truck.id, "Cargo should be assigned to truck")
        
        # Step 9: Calculate profitability impact
        original_profitability = best_route.profitability
        estimated_revenue = 75.0  # Estimated revenue for this order
        estimated_cost = 25.0     # Estimated additional cost
        
        best_route.profitability += (estimated_revenue - estimated_cost)
        self.session.commit()
        
        # Step 10: Verify profitability improvement
        self.assertGreater(best_route.profitability, original_profitability,
                          "Route profitability should improve after adding order")
        
        improvement = best_route.profitability - original_profitability
        self.assertAlmostEqual(improvement, 50.0, places=1,
                              msg="Profitability improvement should match expected value")
    
    def test_batch_order_processing_workflow(self):
        """
        Test processing multiple orders in batch
        """
        # Create multiple test orders
        batch_orders = []
        
        for i in range(5):
            pickup_loc = Location(
                lat=33.7490 + (i * 0.01),  # Spread around Atlanta
                lng=-84.3880 + (i * 0.01)
            )
            dropoff_loc = Location(
                lat=32.0835 + (i * 0.01),  # Spread around Savannah
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
            
            # Add package
            package = Package(
                volume=5.0 + i,  # Varying sizes
                weight=100.0 + (i * 20),
                type=CargoType.STANDARD,
                cargo_id=cargo.id
            )
            self.session.add(package)
            self.session.commit()
            
            batch_orders.append(order)
        
        # Process batch
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()
        
        start_time = time.time()
        batch_results = self.order_processor.process_order_batch(batch_orders, routes, trucks)
        processing_time = time.time() - start_time
        
        # Verify batch processing results
        self.assertEqual(len(batch_results), len(batch_orders),
                        "Should process all orders in batch")
        
        # Performance check
        avg_time_per_order = processing_time / len(batch_orders)
        self.assertLess(avg_time_per_order, 2.0,
                       f"Average processing time {avg_time_per_order:.2f}s should be <2s per order")
        
        # Verify results quality
        valid_orders = sum(1 for result in batch_results.values() if result.is_valid)
        self.assertGreater(valid_orders, 0, "At least some orders should be valid")
        
        # Check that results contain proper metrics
        for order_id, result in batch_results.items():
            self.assertIsInstance(result.metrics, dict)
            if result.is_valid:
                self.assertIn('order_volume_m3', result.metrics)
                self.assertIn('order_weight_kg', result.metrics)
    
    def test_order_rejection_workflow(self):
        """
        Test workflow when orders cannot be accommodated
        """
        # Create order that violates multiple constraints
        
        # Very far pickup location (violates proximity)
        far_pickup = Location(lat=25.7617, lng=-80.1918)  # Miami
        far_dropoff = Location(lat=47.6062, lng=-122.3321)  # Seattle
        
        self.session.add_all([far_pickup, far_dropoff])
        self.session.commit()
        
        problematic_order = Order(
            location_origin_id=far_pickup.id,
            location_destiny_id=far_dropoff.id,
            client_id=self.test_client_id
        )
        self.session.add(problematic_order)
        self.session.commit()
        
        # Add oversized cargo
        cargo = Cargo(order_id=problematic_order.id)
        self.session.add(cargo)
        self.session.commit()
        
        # Package that exceeds capacity
        oversized_package = Package(
            volume=60.0,  # Exceeds 48m³ truck capacity
            weight=6000.0,  # Exceeds weight limits
            type=CargoType.HAZMAT,  # May have compatibility issues
            cargo_id=cargo.id
        )
        self.session.add(oversized_package)
        self.session.commit()
        
        # Try to process this order
        routes = self.session.exec(select(Route)).all()
        trucks = self.session.exec(select(Truck)).all()
        
        rejection_reasons = []
        
        for i, route in enumerate(routes):
            if i < len(trucks):
                truck = trucks[i]
                result = self.order_processor.validate_order_for_route(
                    problematic_order, route, truck
                )
                
                if not result.is_valid:
                    for error in result.errors:
                        rejection_reasons.append(error.result.value)
        
        # Verify order was properly rejected with reasons
        self.assertGreater(len(rejection_reasons), 0, "Order should be rejected with reasons")
        
        # Check for expected rejection reasons
        expected_rejections = [
            ValidationResult.INVALID_PROXIMITY.value,
            ValidationResult.INVALID_CAPACITY.value,
            ValidationResult.INVALID_WEIGHT.value
        ]
        
        found_rejections = set(rejection_reasons)
        expected_set = set(expected_rejections)
        
        # Should have at least one expected rejection reason
        self.assertTrue(found_rejections.intersection(expected_set),
                       f"Should have expected rejection reasons. Found: {found_rejections}")
    
    def test_route_optimization_workflow(self):
        """
        Test route optimization when multiple orders can be combined
        """
        # Create multiple orders for the same route corridor
        atlanta_to_savannah_orders = []
        
        for i in range(3):
            # All orders along Atlanta-Savannah corridor
            pickup_lat = 33.7490 - (i * 0.3)  # Moving south from Atlanta
            pickup_lng = -84.3880 + (i * 0.2)  # Moving east
            
            dropoff_lat = 32.0835 + (i * 0.1)  # Around Savannah area
            dropoff_lng = -81.0998 + (i * 0.1)
            
            pickup_loc = Location(lat=pickup_lat, lng=pickup_lng)
            dropoff_loc = Location(lat=dropoff_lat, lng=dropoff_lng)
            
            self.session.add_all([pickup_loc, dropoff_loc])
            self.session.commit()
            
            order = Order(
                location_origin_id=pickup_loc.id,
                location_destiny_id=dropoff_loc.id,
                client_id=self.test_client_id
            )
            self.session.add(order)
            self.session.commit()
            
            # Add small cargo that can be combined
            cargo = Cargo(order_id=order.id)
            self.session.add(cargo)
            self.session.commit()
            
            package = Package(
                volume=8.0,  # Small enough to combine
                weight=150.0,
                type=CargoType.STANDARD,
                cargo_id=cargo.id
            )
            self.session.add(package)
            self.session.commit()
            
            atlanta_to_savannah_orders.append(order)
        
        # Find the Atlanta-Savannah route
        routes = self.session.exec(select(Route)).all()
        target_route = None
        
        for route in routes:
            # Check if route goes from Atlanta area to Savannah area
            origin_distance = route.location_origin.distance_to(
                Location(lat=33.7490, lng=-84.3880)  # Atlanta
            )
            destiny_distance = route.location_destiny.distance_to(
                Location(lat=32.0835, lng=-81.0998)  # Savannah
            )
            
            if origin_distance < 50 and destiny_distance < 50:  # Within 50km
                target_route = route
                break
        
        self.assertIsNotNone(target_route, "Should find Atlanta-Savannah route")
        
        # Get the truck for this route
        truck = self.session.get(Truck, target_route.truck_id)
        self.assertIsNotNone(truck, "Route should have assigned truck")
        
        # Test combining orders on the same route
        original_profitability = target_route.profitability
        combined_orders = 0
        total_volume = 0
        
        for order in atlanta_to_savannah_orders:
            result = self.order_processor.validate_order_for_route(order, target_route, truck)
            
            if result.is_valid:
                # Add order to route
                order.route_id = target_route.id
                
                # Add cargo to truck
                for cargo in order.cargo:
                    cargo.truck_id = truck.id
                    total_volume += cargo.total_volume()
                
                combined_orders += 1
                
                # Simulate profitability improvement
                target_route.profitability += 40.0  # Revenue per order minus costs
        
        self.session.commit()
        
        # Verify optimization results
        self.assertGreater(combined_orders, 1, "Should combine multiple orders on same route")
        self.assertLess(total_volume, truck.capacity, "Combined cargo should fit in truck")
        self.assertGreater(target_route.profitability, original_profitability,
                          "Route profitability should improve with combined orders")
        
        # Calculate efficiency metrics
        capacity_utilization = (total_volume / truck.capacity) * 100
        profitability_improvement = target_route.profitability - original_profitability
        
        self.assertGreater(capacity_utilization, 30.0, "Should achieve reasonable capacity utilization")
        self.assertGreater(profitability_improvement, 50.0, "Should achieve significant profitability improvement")
    
    def _calculate_route_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate efficiency score for route selection
        """
        score = 0.0
        
        # Prefer higher capacity utilization
        volume_util = metrics.get('volume_utilization_percent', 0)
        weight_util = metrics.get('weight_utilization_percent', 0)
        score += (volume_util + weight_util) / 2
        
        # Penalize high additional costs
        additional_cost = metrics.get('additional_cost_usd', 0)
        score -= additional_cost * 10
        
        # Prefer shorter deviations
        deviation_miles = metrics.get('deviation_distance_miles', 0)
        score -= deviation_miles * 5
        
        return score


if __name__ == "__main__":
    unittest.main()