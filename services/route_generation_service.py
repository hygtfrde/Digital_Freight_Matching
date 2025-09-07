"""
Route Generation Service for Digital Freight Matching System

Generates profitable new routes from cargo combinations and validates economic viability.
Integrates with existing route calculation and cost framework.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session

# Import existing models and services
from app.database import Order, Route, Truck, Location, engine, create_location
from services.cargo_aggregation_service import CargoCombination
from services.route_calculation import get_route_service, RouteResult
from order_processor import OrderProcessingConstants

logger = logging.getLogger(__name__)


@dataclass
class RouteGenerationResult:
    """Result of route generation attempt"""
    success: bool
    route: Optional[Route]
    estimated_profit: float
    estimated_cost: float
    estimated_revenue: float
    total_distance_km: float
    total_time_hours: float
    orders_included: int
    error_message: Optional[str] = None


@dataclass
class EconomicAnalysis:
    """Economic analysis of a generated route"""
    total_distance_km: float
    total_time_hours: float
    base_cost_usd: float
    fuel_cost_usd: float
    driver_cost_usd: float
    total_cost_usd: float
    estimated_revenue_usd: float
    profit_margin: float
    is_profitable: bool
    min_profit_threshold: float = 50.0  # Minimum daily profit required


class RouteGenerationService:
    """
    Service for generating profitable routes from cargo combinations
    """
    
    def __init__(self, session: Session):
        """Initialize with database session and dependencies"""
        self.session = session
        self.constants = OrderProcessingConstants()
        # Use fallback instead of OSMnx for demo purposes (OSMnx too slow for large areas)
        self.route_service = None  # get_route_service()
        
    def generate_profitable_route(self, combination: CargoCombination, 
                                 available_truck: Optional[Truck] = None) -> RouteGenerationResult:
        """
        Generate a profitable route from a cargo combination
        
        Args:
            combination: Compatible cargo combination
            available_truck: Specific truck to use, or None to use default specs
            
        Returns:
            RouteGenerationResult with route and profitability analysis
        """
        logger.info(f"Generating route for combination with {len(combination.orders)} orders")
        
        try:
            # Step 1: Determine optimal route path
            route_locations = self._determine_optimal_route_path(combination.orders)
            if not route_locations or len(route_locations) < 2:
                return RouteGenerationResult(
                    success=False,
                    route=None,
                    estimated_profit=0.0,
                    estimated_cost=0.0,
                    estimated_revenue=0.0,
                    total_distance_km=0.0,
                    total_time_hours=0.0,
                    orders_included=len(combination.orders),
                    error_message="Could not determine optimal route path"
                )
            
            # Step 2: Calculate route distance and time (using simple calculation for demo)
            route_result = self._calculate_simple_route_distance(route_locations)
            
            # Step 3: Perform economic analysis
            logger.debug(f"Starting economic analysis for route: {route_result.total_distance_km}km")
            economic_analysis = self._analyze_route_economics(
                route_result, 
                combination.orders,
                available_truck
            )
            
            # Step 4: Validate profitability
            if not economic_analysis.is_profitable:
                logger.info(f"Route not profitable: profit margin {economic_analysis.profit_margin}%")
                return RouteGenerationResult(
                    success=False,
                    route=None,
                    estimated_profit=economic_analysis.profit_margin,
                    estimated_cost=economic_analysis.total_cost_usd,
                    estimated_revenue=economic_analysis.estimated_revenue_usd,
                    total_distance_km=route_result.total_distance_km,
                    total_time_hours=route_result.total_time_hours,
                    orders_included=len(combination.orders),
                    error_message=f"Route not profitable: {economic_analysis.profit_margin:.1f}% margin < {economic_analysis.min_profit_threshold}%"
                )
            
            # Step 5: Create route entity
            route = self._create_route_entity(route_locations, economic_analysis, available_truck)
            
            logger.info(f"Successfully generated profitable route: "
                       f"{economic_analysis.profit_margin:.1f}% margin, "
                       f"${economic_analysis.estimated_revenue_usd - economic_analysis.total_cost_usd:.2f} profit")
            
            return RouteGenerationResult(
                success=True,
                route=route,
                estimated_profit=economic_analysis.estimated_revenue_usd - economic_analysis.total_cost_usd,
                estimated_cost=economic_analysis.total_cost_usd,
                estimated_revenue=economic_analysis.estimated_revenue_usd,
                total_distance_km=route_result.total_distance_km,
                total_time_hours=route_result.total_time_hours,
                orders_included=len(combination.orders)
            )
            
        except Exception as e:
            logger.error(f"Route generation failed: {e}")
            return RouteGenerationResult(
                success=False,
                route=None,
                estimated_profit=0.0,
                estimated_cost=0.0,
                estimated_revenue=0.0,
                total_distance_km=0.0,
                total_time_hours=0.0,
                orders_included=len(combination.orders),
                error_message=f"Generation failed: {str(e)}"
            )
    
    def _determine_optimal_route_path(self, orders: List[Order]) -> List[Location]:
        """
        Determine optimal route path visiting all order locations
        
        Args:
            orders: List of orders to visit
            
        Returns:
            List of locations in optimal order
        """
        if not orders:
            return []
        
        # Collect all unique locations
        locations = []
        location_ids = set()
        
        for order in orders:
            if order.location_origin and order.location_origin.id not in location_ids:
                locations.append(order.location_origin)
                location_ids.add(order.location_origin.id)
            
            if order.location_destiny and order.location_destiny.id not in location_ids:
                locations.append(order.location_destiny)
                location_ids.add(order.location_destiny.id)
        
        if len(locations) < 2:
            logger.warning(f"Insufficient locations for route: {len(locations)}")
            return locations
        
        # For now, use simple ordering - could be enhanced with TSP algorithms
        # Sort by latitude first, then longitude for a roughly optimal path
        locations.sort(key=lambda loc: (loc.lat, loc.lng))
        
        logger.debug(f"Determined route path with {len(locations)} locations")
        return locations
    
    def _analyze_route_economics(self, route_result: RouteResult, orders: List[Order], 
                                truck: Optional[Truck] = None) -> EconomicAnalysis:
        """
        Perform comprehensive economic analysis of the route
        
        Args:
            route_result: Route calculation result
            orders: Orders included in route
            truck: Truck specifications (optional)
            
        Returns:
            EconomicAnalysis with profitability metrics
        """
        distance_km = route_result.total_distance_km
        time_hours = route_result.total_time_hours
        
        # Convert to miles for cost calculations (using existing constants)
        distance_miles = distance_km * self.constants.KM_TO_MILES
        
        # Calculate costs using existing cost structure
        fuel_cost = distance_miles * self.constants.FUEL_COST_PER_MILE
        driver_cost = distance_miles * self.constants.TRUCKER_COST_PER_MILE
        maintenance_cost = distance_miles * self.constants.MAINTENANCE_COST_PER_MILE
        leasing_cost = distance_miles * self.constants.LEASING_COST_PER_MILE
        insurance_cost = distance_miles * self.constants.INSURANCE_COST_PER_MILE
        
        total_cost = fuel_cost + driver_cost + maintenance_cost + leasing_cost + insurance_cost
        
        # Estimate revenue based on cargo volume and weight
        estimated_revenue = self._estimate_route_revenue(orders, distance_miles)
        
        # Calculate profit metrics
        profit_usd = estimated_revenue - total_cost
        profit_margin = (profit_usd / estimated_revenue * 100) if estimated_revenue > 0 else -100
        
        is_profitable = profit_margin >= 20.0  # Require at least 20% margin
        
        logger.debug(f"Economic analysis: ${estimated_revenue:.2f} revenue, "
                    f"${total_cost:.2f} cost, {profit_margin:.1f}% margin")
        
        return EconomicAnalysis(
            total_distance_km=distance_km,
            total_time_hours=time_hours,
            base_cost_usd=total_cost,
            fuel_cost_usd=fuel_cost,
            driver_cost_usd=driver_cost,
            total_cost_usd=total_cost,
            estimated_revenue_usd=estimated_revenue,
            profit_margin=profit_margin,
            is_profitable=is_profitable
        )
    
    def _estimate_route_revenue(self, orders: List[Order], distance_miles: float) -> float:
        """
        Estimate revenue for route based on cargo and distance
        
        Args:
            orders: Orders to be served
            distance_miles: Total route distance in miles
            
        Returns:
            Estimated revenue in USD
        """
        total_revenue = 0.0
        
        for order in orders:
            # Base rate per order (could be made configurable)
            base_rate = 100.0  # $100 base rate per order
            
            # Distance component (rate per mile for the order's distance)
            order_distance_miles = order.total_distance() * self.constants.KM_TO_MILES
            distance_rate = order_distance_miles * 1.5  # $1.50 per mile
            
            # Volume component (rate per cubic meter)
            volume_rate = order.total_volume() * 15.0  # $15 per cubic meter
            
            # Weight component (rate per kg)
            weight_rate = order.total_weight() * 0.5  # $0.50 per kg
            
            order_revenue = base_rate + distance_rate + volume_rate + weight_rate
            total_revenue += order_revenue
            
            logger.debug(f"Order {order.id} revenue: ${order_revenue:.2f} "
                        f"(base: ${base_rate}, dist: ${distance_rate:.2f}, "
                        f"vol: ${volume_rate:.2f}, weight: ${weight_rate:.2f})")
        
        return total_revenue
    
    def _create_route_entity(self, locations: List[Location], analysis: EconomicAnalysis,
                            truck: Optional[Truck] = None) -> Route:
        """
        Create Route entity from analyzed route data
        
        Args:
            locations: Route locations in order
            analysis: Economic analysis results
            truck: Assigned truck (optional)
            
        Returns:
            Route entity (not yet persisted to database)
        """
        if len(locations) < 2:
            raise ValueError("Route must have at least 2 locations")
        
        origin = locations[0]
        destination = locations[-1]
        
        # Calculate profitability (revenue - cost)
        profitability = analysis.estimated_revenue_usd - analysis.total_cost_usd
        
        # Create route entity
        route = Route(
            location_origin_id=origin.id,
            location_destiny_id=destination.id,
            profitability=profitability,
            truck_id=truck.id if truck else None
        )
        
        # Set path for route calculations (not persisted to DB)
        route.set_path(locations)
        
        logger.info(f"Created route entity: origin={origin.id}, destination={destination.id}, "
                   f"profitability=${profitability:.2f}")
        
        return route
    
    def validate_economic_viability(self, combination: CargoCombination,
                                  min_profit_margin: float = 20.0) -> Tuple[bool, Dict[str, float]]:
        """
        Quick validation of economic viability before full route generation
        
        Args:
            combination: Cargo combination to validate
            min_profit_margin: Minimum profit margin percentage required
            
        Returns:
            Tuple of (is_viable, metrics_dict)
        """
        logger.debug(f"Validating economic viability for {len(combination.orders)} orders")
        
        # Rough distance estimate (sum of individual order distances)
        estimated_distance_km = combination.estimated_distance_km
        estimated_distance_miles = estimated_distance_km * self.constants.KM_TO_MILES
        
        # Quick cost estimate
        estimated_cost = estimated_distance_miles * self.constants.TOTAL_COST_PER_MILE
        
        # Quick revenue estimate
        estimated_revenue = self._estimate_route_revenue(combination.orders, estimated_distance_miles)
        
        # Calculate rough profit margin
        profit_margin = ((estimated_revenue - estimated_cost) / estimated_revenue * 100) if estimated_revenue > 0 else -100
        
        is_viable = profit_margin >= min_profit_margin
        
        metrics = {
            'estimated_distance_km': estimated_distance_km,
            'estimated_distance_miles': estimated_distance_miles,
            'estimated_cost_usd': estimated_cost,
            'estimated_revenue_usd': estimated_revenue,
            'estimated_profit_margin': profit_margin,
            'min_profit_margin': min_profit_margin
        }
        
        logger.debug(f"Economic viability: {is_viable} ({profit_margin:.1f}% margin)")
        return is_viable, metrics
    
    def generate_multiple_routes(self, combinations: List[CargoCombination], 
                               available_trucks: List[Truck],
                               max_routes: int = 10) -> List[RouteGenerationResult]:
        """
        Generate multiple profitable routes from multiple cargo combinations
        
        Args:
            combinations: List of cargo combinations to evaluate
            available_trucks: Available trucks for route assignment
            max_routes: Maximum number of routes to generate
            
        Returns:
            List of successful route generation results, sorted by profitability
        """
        logger.info(f"Generating up to {max_routes} routes from {len(combinations)} combinations")
        
        successful_routes = []
        
        for i, combination in enumerate(combinations):
            if len(successful_routes) >= max_routes:
                logger.info(f"Reached maximum route limit: {max_routes}")
                break
            
            # Quick viability check first
            is_viable, _ = self.validate_economic_viability(combination)
            if not is_viable:
                logger.debug(f"Combination {i} not economically viable, skipping")
                continue
            
            # Assign truck if available
            truck = available_trucks[len(successful_routes)] if len(successful_routes) < len(available_trucks) else None
            
            # Generate route
            result = self.generate_profitable_route(combination, truck)
            
            if result.success:
                successful_routes.append(result)
                logger.info(f"Generated route {len(successful_routes)}: ${result.estimated_profit:.2f} profit")
        
        # Sort by profitability (highest first)
        successful_routes.sort(key=lambda r: r.estimated_profit, reverse=True)
        
        logger.info(f"Successfully generated {len(successful_routes)} profitable routes")
        return successful_routes
    
    def _calculate_simple_route_distance(self, locations: List[Location]):
        """
        Simple fallback route calculation using Haversine distance
        
        Args:
            locations: Route locations
            
        Returns:
            Mock RouteResult with basic distance/time calculations
        """
        if len(locations) < 2:
            # Create a simple mock result for error cases
            from dataclasses import dataclass
            
            @dataclass
            class SimpleRouteResult:
                total_distance_km: float = 0.0
                total_time_hours: float = 0.0
                is_successful: bool = True
                error: str = None
            
            return SimpleRouteResult()
        
        total_distance = 0.0
        for i in range(len(locations) - 1):
            distance = locations[i].distance_to(locations[i + 1])
            total_distance += distance
        
        # Estimate time at 60 km/h average
        total_time = total_distance / 60.0
        
        from dataclasses import dataclass
        
        @dataclass  
        class SimpleRouteResult:
            total_distance_km: float
            total_time_hours: float
            is_successful: bool = True
            error: str = None
        
        return SimpleRouteResult(
            total_distance_km=total_distance,
            total_time_hours=total_time
        )