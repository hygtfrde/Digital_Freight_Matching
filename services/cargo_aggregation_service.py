"""
Cargo Aggregation Service for Digital Freight Matching System

Finds unmatched orders and creates compatible cargo combinations for new route generation.
Integrates with existing OrderProcessor validation framework.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from itertools import combinations
from sqlmodel import Session, select

# Import existing models and validation
from app.database import Order, Route, Truck, Cargo, Package, CargoType, Location
from order_processor import OrderProcessor, ProcessingResult, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class CargoCombination:
    """Represents a combination of compatible orders that could form a new route"""
    orders: List[Order]
    total_volume_m3: float
    total_weight_kg: float
    cargo_types: Set[CargoType]
    estimated_distance_km: float
    compatibility_score: float
    

@dataclass
class AggregationResult:
    """Result of cargo aggregation analysis"""
    unmatched_orders: List[Order]
    compatible_combinations: List[CargoCombination]
    total_unmatched_volume: float
    total_unmatched_weight: float
    aggregation_opportunities: int


class CargoAggregationService:
    """
    Service for finding unmatched orders and creating compatible cargo combinations
    """
    
    def __init__(self, session: Session):
        """Initialize with database session and order processor"""
        self.session = session
        self.order_processor = OrderProcessor()
        
    def find_unmatched_orders(self, routes: List[Route], trucks: List[Truck]) -> List[Order]:
        """
        Find orders that cannot be matched to any existing route
        
        Args:
            routes: Available routes for matching
            trucks: Available trucks for capacity validation
            
        Returns:
            List of orders that couldn't be matched to existing routes
        """
        logger.info(f"Analyzing {len(routes)} routes and {len(trucks)} trucks for unmatched orders")
        
        # Get all orders without assigned routes
        unassigned_orders = self.session.exec(
            select(Order).where(Order.route_id.is_(None))
        ).all()
        
        unmatched_orders = []
        
        for order in unassigned_orders:
            is_matched = False
            
            # Try to match order to each route-truck combination
            for i, route in enumerate(routes):
                if i < len(trucks):
                    truck = trucks[i]
                    result = self.order_processor.validate_order_for_route(order, route, truck)
                    
                    if result.is_valid:
                        is_matched = True
                        logger.debug(f"Order {order.id} can be matched to route {route.id}")
                        break
            
            if not is_matched:
                unmatched_orders.append(order)
                logger.debug(f"Order {order.id} remains unmatched")
        
        logger.info(f"Found {len(unmatched_orders)} unmatched orders out of {len(unassigned_orders)} unassigned")
        return unmatched_orders
    
    def find_compatible_combinations(self, orders: List[Order], max_combination_size: int = 5) -> List[CargoCombination]:
        """
        Find compatible combinations of orders that could be grouped into new routes
        
        Args:
            orders: List of unmatched orders to combine
            max_combination_size: Maximum number of orders per combination
            
        Returns:
            List of compatible cargo combinations sorted by compatibility score
        """
        logger.info(f"Finding compatible combinations from {len(orders)} orders")
        
        if len(orders) < 2:
            logger.warning("Need at least 2 orders to create combinations")
            return []
        
        compatible_combinations = []
        
        # Generate all possible combinations (2 to max_combination_size)
        for combo_size in range(2, min(len(orders) + 1, max_combination_size + 1)):
            logger.debug(f"Checking combinations of size {combo_size}")
            
            for order_combo in combinations(orders, combo_size):
                combination = self._evaluate_order_combination(list(order_combo))
                
                if combination:
                    compatible_combinations.append(combination)
                    logger.debug(f"Found compatible combination: {[o.id for o in combination.orders]}")
        
        # Sort by compatibility score (highest first)
        compatible_combinations.sort(key=lambda c: c.compatibility_score, reverse=True)
        
        logger.info(f"Found {len(compatible_combinations)} compatible combinations")
        return compatible_combinations
    
    def _evaluate_order_combination(self, orders: List[Order]) -> Optional[CargoCombination]:
        """
        Evaluate if a combination of orders is compatible and viable
        
        Args:
            orders: List of orders to evaluate as a combination
            
        Returns:
            CargoCombination if compatible, None otherwise
        """
        if not orders:
            return None
        
        # Calculate combined metrics
        total_volume = sum(order.total_volume() for order in orders)
        total_weight = sum(order.total_weight() for order in orders)
        
        # Check capacity constraints against max truck capacity (48m³, 9180 lbs)
        max_volume_m3 = 48.0
        max_weight_lbs = 9180.0
        max_weight_kg = max_weight_lbs * 0.453592
        
        if total_volume > max_volume_m3:
            logger.debug(f"Combination exceeds volume capacity: {total_volume}m³ > {max_volume_m3}m³")
            return None
        
        if total_weight > max_weight_kg:
            logger.debug(f"Combination exceeds weight capacity: {total_weight}kg > {max_weight_kg}kg")
            return None
        
        # Collect all cargo types
        all_cargo_types = set()
        for order in orders:
            for cargo in order.cargo:
                all_cargo_types.update(cargo.get_types())
        
        # Check cargo type compatibility
        if not self._check_cargo_type_compatibility(all_cargo_types):
            logger.debug(f"Incompatible cargo types in combination: {all_cargo_types}")
            return None
        
        # Estimate route distance (simplified: sum of individual order distances)
        estimated_distance = sum(order.total_distance() for order in orders)
        
        # Calculate compatibility score
        compatibility_score = self._calculate_compatibility_score(orders, total_volume, total_weight)
        
        return CargoCombination(
            orders=orders,
            total_volume_m3=total_volume,
            total_weight_kg=total_weight,
            cargo_types=all_cargo_types,
            estimated_distance_km=estimated_distance,
            compatibility_score=compatibility_score
        )
    
    def _check_cargo_type_compatibility(self, cargo_types: Set[CargoType]) -> bool:
        """
        Check if cargo types are compatible based on business rules
        
        Args:
            cargo_types: Set of cargo types to check
            
        Returns:
            True if compatible, False otherwise
        """
        # Define incompatible pairs (from existing cargo compatibility logic)
        incompatible_pairs = [
            (CargoType.HAZMAT, CargoType.FRAGILE),
            (CargoType.HAZMAT, CargoType.REFRIGERATED)
        ]
        
        for type1, type2 in incompatible_pairs:
            if type1 in cargo_types and type2 in cargo_types:
                return False
        
        return True
    
    def _calculate_compatibility_score(self, orders: List[Order], total_volume: float, total_weight: float) -> float:
        """
        Calculate compatibility score for order combination
        Higher score = better combination
        
        Args:
            orders: List of orders in combination
            total_volume: Combined volume
            total_weight: Combined weight
            
        Returns:
            Compatibility score (0-100)
        """
        score = 0.0
        
        # Volume utilization score (prefer higher utilization)
        max_volume = 48.0
        volume_utilization = (total_volume / max_volume) * 100
        score += min(volume_utilization, 100) * 0.3
        
        # Weight utilization score
        max_weight_kg = 9180.0 * 0.453592
        weight_utilization = (total_weight / max_weight_kg) * 100
        score += min(weight_utilization, 100) * 0.3
        
        # Geographic clustering score (prefer orders with nearby locations)
        geographic_score = self._calculate_geographic_clustering_score(orders)
        score += geographic_score * 0.25
        
        # Order count bonus (prefer combining more orders)
        order_count_bonus = min(len(orders) * 5, 20)  # Up to 20 points for order count
        score += order_count_bonus * 0.15
        
        return min(score, 100.0)
    
    def _calculate_geographic_clustering_score(self, orders: List[Order]) -> float:
        """
        Calculate how geographically clustered the orders are
        Higher score = more clustered (better for routing)
        
        Args:
            orders: List of orders to evaluate
            
        Returns:
            Geographic clustering score (0-100)
        """
        if len(orders) < 2:
            return 100.0
        
        # Collect all locations (origins and destinations)
        locations = []
        for order in orders:
            if order.location_origin:
                locations.append(order.location_origin)
            if order.location_destiny:
                locations.append(order.location_destiny)
        
        if len(locations) < 2:
            return 50.0  # Neutral score if insufficient location data
        
        # Calculate average distance between all location pairs
        total_distance = 0.0
        pair_count = 0
        
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                distance = locations[i].distance_to(locations[j])
                total_distance += distance
                pair_count += 1
        
        if pair_count == 0:
            return 50.0
        
        average_distance = total_distance / pair_count
        
        # Score inversely related to average distance
        # Distances under 100km get high scores, over 500km get low scores
        if average_distance <= 100:
            return 100.0
        elif average_distance >= 500:
            return 10.0
        else:
            # Linear interpolation between 100km (score 100) and 500km (score 10)
            return 100 - ((average_distance - 100) / 400) * 90
    
    def analyze_aggregation_opportunities(self, routes: List[Route], trucks: List[Truck]) -> AggregationResult:
        """
        Comprehensive analysis of cargo aggregation opportunities
        
        Args:
            routes: Available routes for matching
            trucks: Available trucks for capacity validation
            
        Returns:
            AggregationResult with complete analysis
        """
        logger.info("Starting comprehensive aggregation analysis")
        
        # Find unmatched orders
        unmatched_orders = self.find_unmatched_orders(routes, trucks)
        
        if not unmatched_orders:
            logger.info("No unmatched orders found - no aggregation opportunities")
            return AggregationResult(
                unmatched_orders=[],
                compatible_combinations=[],
                total_unmatched_volume=0.0,
                total_unmatched_weight=0.0,
                aggregation_opportunities=0
            )
        
        # Find compatible combinations
        compatible_combinations = self.find_compatible_combinations(unmatched_orders)
        
        # Calculate summary metrics
        total_volume = sum(order.total_volume() for order in unmatched_orders)
        total_weight = sum(order.total_weight() for order in unmatched_orders)
        
        logger.info(f"Aggregation analysis complete: {len(unmatched_orders)} unmatched orders, "
                   f"{len(compatible_combinations)} compatible combinations")
        
        return AggregationResult(
            unmatched_orders=unmatched_orders,
            compatible_combinations=compatible_combinations,
            total_unmatched_volume=total_volume,
            total_unmatched_weight=total_weight,
            aggregation_opportunities=len(compatible_combinations)
        )