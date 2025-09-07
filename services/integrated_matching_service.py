"""
Integrated Matching Service for Digital Freight Matching System

Combines cargo aggregation and route generation to provide complete
order-to-route matching with automatic new route creation.

This service extends the existing OrderProcessor batch processing
with cargo aggregation and route generation capabilities.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select

# Import existing services and models
from app.database import Order, Route, Truck, Location
from services.cargo_aggregation_service import CargoAggregationService, AggregationResult
from services.route_generation_service import RouteGenerationService, RouteGenerationResult
from order_processor import OrderProcessor, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class IntegratedMatchingResult:
    """Result of integrated matching process"""
    total_orders_processed: int
    matched_to_existing_routes: int
    unmatched_orders: int
    new_routes_generated: int
    total_orders_assigned: int
    estimated_additional_profit: float
    successful_combinations: List
    failed_combinations: List
    processing_errors: List[str]


class IntegratedMatchingService:
    """
    Service that integrates cargo aggregation and route generation
    with existing order processing capabilities
    """
    
    def __init__(self, session: Session):
        """Initialize with database session and component services"""
        self.session = session
        self.order_processor = OrderProcessor()
        self.cargo_aggregation = CargoAggregationService(session)
        self.route_generation = RouteGenerationService(session)
        
    def process_orders_with_aggregation(self, orders: List[Order], routes: List[Route], 
                                      trucks: List[Truck]) -> IntegratedMatchingResult:
        """
        Complete order processing with cargo aggregation and route generation
        
        Process flow:
        1. Try to match orders to existing routes (existing logic)
        2. Find unmatched orders 
        3. Create cargo combinations from unmatched orders
        4. Generate new profitable routes
        5. Assign orders to new routes
        
        Args:
            orders: Orders to process
            routes: Available existing routes
            trucks: Available trucks
            
        Returns:
            IntegratedMatchingResult with complete processing results
        """
        logger.info(f"Starting integrated matching for {len(orders)} orders, "
                   f"{len(routes)} routes, {len(trucks)} trucks")
        
        processing_errors = []
        matched_to_existing = 0
        new_routes_generated = 0
        estimated_additional_profit = 0.0
        successful_combinations = []
        failed_combinations = []
        
        try:
            # Step 1: Try matching to existing routes using existing logic
            logger.info("Step 1: Matching to existing routes...")
            existing_matches = self.order_processor.process_order_batch(orders, routes, trucks)
            
            matched_to_existing = sum(1 for result in existing_matches.values() if result.is_valid)
            logger.info(f"Matched {matched_to_existing} orders to existing routes")
            
            # Step 2: Find truly unmatched orders (those that failed validation)
            logger.info("Step 2: Finding unmatched orders...")
            unmatched_orders = []
            for order_id, result in existing_matches.items():
                if not result.is_valid:
                    # Find the order object
                    order = next((o for o in orders if (o.id or id(o)) == order_id), None)
                    if order:
                        unmatched_orders.append(order)
            
            logger.info(f"Found {len(unmatched_orders)} unmatched orders")
            
            if not unmatched_orders:
                logger.info("No unmatched orders - returning existing matches only")
                return IntegratedMatchingResult(
                    total_orders_processed=len(orders),
                    matched_to_existing_routes=matched_to_existing,
                    unmatched_orders=0,
                    new_routes_generated=0,
                    total_orders_assigned=matched_to_existing,
                    estimated_additional_profit=0.0,
                    successful_combinations=[],
                    failed_combinations=[],
                    processing_errors=processing_errors
                )
            
            # Step 3: Analyze aggregation opportunities
            logger.info("Step 3: Analyzing aggregation opportunities...")
            aggregation_result = self.cargo_aggregation.analyze_aggregation_opportunities(routes, trucks)
            
            logger.info(f"Found {len(aggregation_result.compatible_combinations)} cargo combinations")
            
            if not aggregation_result.compatible_combinations:
                logger.warning("No viable cargo combinations found")
                return IntegratedMatchingResult(
                    total_orders_processed=len(orders),
                    matched_to_existing_routes=matched_to_existing,
                    unmatched_orders=len(unmatched_orders),
                    new_routes_generated=0,
                    total_orders_assigned=matched_to_existing,
                    estimated_additional_profit=0.0,
                    successful_combinations=[],
                    failed_combinations=aggregation_result.compatible_combinations,
                    processing_errors=["No viable cargo combinations could be created"]
                )
            
            # Step 4: Generate new routes from combinations
            logger.info("Step 4: Generating new routes...")
            
            # Get available trucks (those not assigned to existing routes)
            assigned_truck_ids = {r.truck_id for r in routes if r.truck_id}
            available_trucks = [t for t in trucks if t.id not in assigned_truck_ids]
            
            if not available_trucks:
                logger.warning("No available trucks for new routes")
                processing_errors.append("No available trucks for new route generation")
            else:
                # Generate routes for the best combinations
                generation_results = self.route_generation.generate_multiple_routes(
                    aggregation_result.compatible_combinations[:len(available_trucks)],
                    available_trucks,
                    max_routes=len(available_trucks)
                )
                
                for result in generation_results:
                    if result.success:
                        successful_combinations.append({
                            'orders_count': result.orders_included,
                            'estimated_profit': result.estimated_profit,
                            'distance_km': result.total_distance_km,
                            'time_hours': result.total_time_hours
                        })
                        estimated_additional_profit += result.estimated_profit
                        new_routes_generated += 1
                        
                        logger.info(f"Generated profitable route: ${result.estimated_profit:.2f} profit")
                    else:
                        failed_combinations.append({
                            'orders_count': result.orders_included,
                            'error': result.error_message
                        })
                        
                        logger.warning(f"Route generation failed: {result.error_message}")
            
            total_assigned = matched_to_existing + sum(
                combo['orders_count'] for combo in successful_combinations
            )
            
            logger.info(f"Integrated matching complete: {total_assigned}/{len(orders)} orders assigned, "
                       f"{new_routes_generated} new routes, ${estimated_additional_profit:.2f} additional profit")
            
            return IntegratedMatchingResult(
                total_orders_processed=len(orders),
                matched_to_existing_routes=matched_to_existing,
                unmatched_orders=len(unmatched_orders) - sum(combo['orders_count'] for combo in successful_combinations),
                new_routes_generated=new_routes_generated,
                total_orders_assigned=total_assigned,
                estimated_additional_profit=estimated_additional_profit,
                successful_combinations=successful_combinations,
                failed_combinations=failed_combinations,
                processing_errors=processing_errors
            )
            
        except Exception as e:
            logger.error(f"Integrated matching failed: {e}")
            processing_errors.append(f"Integration error: {str(e)}")
            
            return IntegratedMatchingResult(
                total_orders_processed=len(orders),
                matched_to_existing_routes=matched_to_existing,
                unmatched_orders=len(orders) - matched_to_existing,
                new_routes_generated=0,
                total_orders_assigned=matched_to_existing,
                estimated_additional_profit=0.0,
                successful_combinations=[],
                failed_combinations=[],
                processing_errors=processing_errors
            )
    
    def create_and_persist_routes(self, generation_results: List[RouteGenerationResult]) -> List[Route]:
        """
        Create and persist new routes to database
        
        Args:
            generation_results: Successful route generation results
            
        Returns:
            List of persisted Route entities
        """
        persisted_routes = []
        
        for result in generation_results:
            if result.success and result.route:
                try:
                    # Add route to database
                    self.session.add(result.route)
                    self.session.flush()  # Get route ID
                    
                    # Update route profitability with calculated profit
                    result.route.profitability = result.estimated_profit
                    
                    persisted_routes.append(result.route)
                    
                    logger.info(f"Persisted route {result.route.id} with ${result.estimated_profit:.2f} profit")
                    
                except Exception as e:
                    logger.error(f"Failed to persist route: {e}")
                    self.session.rollback()
        
        try:
            self.session.commit()
            logger.info(f"Successfully persisted {len(persisted_routes)} new routes")
        except Exception as e:
            logger.error(f"Failed to commit routes: {e}")
            self.session.rollback()
            persisted_routes = []
        
        return persisted_routes
    
    def assign_orders_to_routes(self, orders: List[Order], routes: List[Route]) -> int:
        """
        Assign orders to their matched routes in database
        
        Args:
            orders: Orders to assign
            routes: Routes to assign to
            
        Returns:
            Number of orders successfully assigned
        """
        assigned_count = 0
        
        try:
            for order in orders:
                # This would need business logic to determine which route
                # For now, we'll assign based on location proximity
                best_route = self._find_best_route_for_order(order, routes)
                
                if best_route:
                    order.route_id = best_route.id
                    self.session.add(order)
                    assigned_count += 1
                    
                    logger.debug(f"Assigned order {order.id} to route {best_route.id}")
            
            self.session.commit()
            logger.info(f"Successfully assigned {assigned_count} orders to routes")
            
        except Exception as e:
            logger.error(f"Failed to assign orders: {e}")
            self.session.rollback()
            assigned_count = 0
        
        return assigned_count
    
    def _find_best_route_for_order(self, order: Order, routes: List[Route]) -> Optional[Route]:
        """
        Find the best route for an order based on location proximity
        
        Args:
            order: Order to find route for
            routes: Available routes
            
        Returns:
            Best matching route or None
        """
        if not order.location_origin or not order.location_destiny:
            return None
        
        best_route = None
        min_distance = float('inf')
        
        for route in routes:
            if not route.location_origin or not route.location_destiny:
                continue
            
            # Calculate total distance from order locations to route endpoints
            pickup_to_origin = order.location_origin.distance_to(route.location_origin)
            pickup_to_dest = order.location_origin.distance_to(route.location_destiny)
            dropoff_to_origin = order.location_destiny.distance_to(route.location_origin)
            dropoff_to_dest = order.location_destiny.distance_to(route.location_destiny)
            
            # Find minimum total deviation
            total_distance = min(
                pickup_to_origin + dropoff_to_dest,  # Normal direction
                pickup_to_dest + dropoff_to_origin   # Reverse direction
            )
            
            if total_distance < min_distance:
                min_distance = total_distance
                best_route = route
        
        # Only return route if within reasonable proximity (e.g., 50km total deviation)
        if min_distance <= 50.0:
            return best_route
        
        return None
    
    def generate_performance_report(self, result: IntegratedMatchingResult) -> Dict:
        """
        Generate performance report from integrated matching results
        
        Args:
            result: Integrated matching result
            
        Returns:
            Performance report dictionary
        """
        total_processed = result.total_orders_processed
        assignment_rate = (result.total_orders_assigned / total_processed * 100) if total_processed > 0 else 0
        
        report = {
            'processing_summary': {
                'total_orders_processed': total_processed,
                'orders_matched_to_existing': result.matched_to_existing_routes,
                'orders_in_new_routes': sum(c['orders_count'] for c in result.successful_combinations),
                'orders_still_unmatched': result.unmatched_orders,
                'assignment_rate_percent': round(assignment_rate, 1)
            },
            'route_generation': {
                'new_routes_created': result.new_routes_generated,
                'successful_combinations': len(result.successful_combinations),
                'failed_combinations': len(result.failed_combinations),
                'estimated_additional_profit': result.estimated_additional_profit
            },
            'profitability_impact': {
                'additional_daily_profit': result.estimated_additional_profit,
                'profit_per_new_route': (
                    result.estimated_additional_profit / result.new_routes_generated 
                    if result.new_routes_generated > 0 else 0
                ),
                'average_orders_per_new_route': (
                    sum(c['orders_count'] for c in result.successful_combinations) / result.new_routes_generated
                    if result.new_routes_generated > 0 else 0
                )
            },
            'errors_and_issues': result.processing_errors,
            'success_metrics': {
                'integration_successful': len(result.processing_errors) == 0,
                'some_routes_generated': result.new_routes_generated > 0,
                'profit_improvement': result.estimated_additional_profit > 0
            }
        }
        
        return report