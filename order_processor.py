"""
Order Processing Engine for Digital Freight Matching System

Implements order validation and constraint checking with business rules:
- 1km proximity constraint validation using haversine distance calculation
- 15-minute stops plus deviation time calculation
- Capacity checking with volume (CBM) and weight (pounds) validation
- Uses exact constants from documentation
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional
from schemas.schemas import Order, Route, Truck, Location



class ValidationResult(Enum):
    """Order validation results"""
    VALID = "valid"
    INVALID_PROXIMITY = "invalid_proximity"
    INVALID_CAPACITY = "invalid_capacity"
    INVALID_TIME = "invalid_time"
    INVALID_WEIGHT = "invalid_weight"
    INCOMPATIBLE_CARGO = "incompatible_cargo"


@dataclass
class ValidationError:
    """Detailed validation error information"""
    result: ValidationResult
    message: str
    details: Dict[str, Any]


@dataclass
class ProcessingResult:
    """Result of order processing"""
    is_valid: bool
    errors: List[ValidationError]
    metrics: Dict[str, float]


class OrderProcessingConstants:
    """
    Business constants from documentation - DO NOT CHANGE
    """
    # Truck Information
    TOTAL_COST_PER_MILE = 1.693846154
    TRUCKER_COST_PER_MILE = 0.78
    FUEL_COST_PER_MILE = 0.373846153846154  # GAS_PRICE / MILES_PER_GALLON = 2.43 / 6.5
    LEASING_COST_PER_MILE = 0.27
    MAINTENANCE_COST_PER_MILE = 0.17
    INSURANCE_COST_PER_MILE = 0.1

    # Performance specs
    MILES_PER_GALLON = 6.5
    GAS_PRICE = 2.43
    AVG_SPEED_MPH = 50

    # Cargo specifications
    MAX_WEIGHT_LBS = 9180
    TOTAL_VOLUME_CUBIC_FEET = 1700
    PALLETS_PER_TRUCK = 26.6
    PALLET_COST_PER_MILE = 0.06376832579

    # Pallet specifications
    PALLET_WEIGHT_LBS = 440
    PALLET_VOLUME_CUBIC_FEET = 64

    # Business rules
    MAX_PROXIMITY_KM = 1.0  # 1km proximity constraint
    STOP_TIME_MINUTES = 15  # 15 minutes per stop
    MAX_ROUTE_HOURS = 10.0  # 10 hour maximum route time

    # Unit conversions
    CUBIC_FEET_TO_CUBIC_METERS = 0.0283168
    LBS_TO_KG = 0.453592
    MILES_TO_KM = 1.609344
    KM_TO_MILES = 0.621371


class OrderProcessor:
    """
    Main order processing engine with validation and constraint checking
    """

    def __init__(self):
        self.constants = OrderProcessingConstants()

    def validate_order_for_route(self, order: Order, route: Route, truck: Truck) -> ProcessingResult:
        """
        Comprehensive order validation for a specific route and truck

        Args:
            order: Order to validate
            route: Target route
            truck: Assigned truck

        Returns:
            ProcessingResult with validation status and details
        """
        errors = []
        metrics = {}

        # 1. Proximity constraint validation
        proximity_result = self._validate_proximity_constraint(order, route)
        if proximity_result:
            errors.append(proximity_result)

        # 2. Capacity validation (volume and weight)
        capacity_result = self._validate_capacity_constraint(order, truck)
        if capacity_result:
            errors.append(capacity_result)

        # 3. Time constraint validation
        time_result = self._validate_time_constraint(order, route)
        if time_result:
            errors.append(time_result)

        # 4. Cargo compatibility validation
        cargo_result = self._validate_cargo_compatibility(order, truck)
        if cargo_result:
            errors.append(cargo_result)

        # Calculate metrics
        metrics = self._calculate_order_metrics(order, route, truck)

        return ProcessingResult(
            is_valid=len(errors) == 0,
            errors=errors,
            metrics=metrics
        )

    def _validate_proximity_constraint(self, order: Order, route: Route) -> Optional[ValidationError]:
        """
        Validate 1km proximity constraint using haversine distance calculation
        """
        if not order.location_origin or not order.location_destiny:
            return ValidationError(
                result=ValidationResult.INVALID_PROXIMITY,
                message="Order missing pickup or dropoff location",
                details={"missing_locations": True}
            )

        # Get route path points
        route_points = []
        if hasattr(route, 'path') and route.path:
            route_points = route.path
        elif route.location_origin and route.location_destiny:
            route_points = [route.location_origin, route.location_destiny]

        if not route_points:
            return ValidationError(
                result=ValidationResult.INVALID_PROXIMITY,
                message="Route has no defined path",
                details={"empty_route": True}
            )

        # Check pickup location proximity
        pickup_distance = self._min_distance_to_route(order.location_origin, route_points)
        if pickup_distance > self.constants.MAX_PROXIMITY_KM:
            return ValidationError(
                result=ValidationResult.INVALID_PROXIMITY,
                message=f"Pickup location too far from route: {pickup_distance:.2f}km > {self.constants.MAX_PROXIMITY_KM}km",
                details={
                    "pickup_distance_km": pickup_distance,
                    "max_allowed_km": self.constants.MAX_PROXIMITY_KM,
                    "location_type": "pickup"
                }
            )

        # Check dropoff location proximity
        dropoff_distance = self._min_distance_to_route(order.location_destiny, route_points)
        if dropoff_distance > self.constants.MAX_PROXIMITY_KM:
            return ValidationError(
                result=ValidationResult.INVALID_PROXIMITY,
                message=f"Dropoff location too far from route: {dropoff_distance:.2f}km > {self.constants.MAX_PROXIMITY_KM}km",
                details={
                    "dropoff_distance_km": dropoff_distance,
                    "max_allowed_km": self.constants.MAX_PROXIMITY_KM,
                    "location_type": "dropoff"
                }
            )

        return None

    def _validate_capacity_constraint(self, order: Order, truck: Truck) -> Optional[ValidationError]:
        """
        Validate capacity constraints with volume (CBM) and weight (pounds)
        """
        # Calculate order requirements
        order_volume_m3 = order.total_volume()
        order_weight_kg = order.total_weight()

        # Convert to documentation units for validation
        order_volume_cf = order_volume_m3 / self.constants.CUBIC_FEET_TO_CUBIC_METERS
        order_weight_lbs = order_weight_kg / self.constants.LBS_TO_KG

        # Check volume capacity
        truck_volume_cf = truck.capacity / self.constants.CUBIC_FEET_TO_CUBIC_METERS
        available_volume_cf = truck_volume_cf - sum(
            cargo.total_volume() / self.constants.CUBIC_FEET_TO_CUBIC_METERS
            for cargo in truck.cargo_loads
        )

        if order_volume_cf > available_volume_cf:
            return ValidationError(
                result=ValidationResult.INVALID_CAPACITY,
                message=f"Insufficient volume capacity: need {order_volume_cf:.1f}cf, available {available_volume_cf:.1f}cf",
                details={
                    "required_volume_cf": order_volume_cf,
                    "available_volume_cf": available_volume_cf,
                    "truck_total_volume_cf": truck_volume_cf,
                    "constraint_type": "volume"
                }
            )

        # Check weight capacity (using documentation max weight)
        current_weight_lbs = sum(
            cargo.total_weight() / self.constants.LBS_TO_KG
            for cargo in truck.cargo_loads
        )
        available_weight_lbs = self.constants.MAX_WEIGHT_LBS - current_weight_lbs

        if order_weight_lbs > available_weight_lbs:
            return ValidationError(
                result=ValidationResult.INVALID_WEIGHT,
                message=f"Insufficient weight capacity: need {order_weight_lbs:.1f}lbs, available {available_weight_lbs:.1f}lbs",
                details={
                    "required_weight_lbs": order_weight_lbs,
                    "available_weight_lbs": available_weight_lbs,
                    "max_weight_lbs": self.constants.MAX_WEIGHT_LBS,
                    "constraint_type": "weight"
                }
            )

        return None

    def _validate_time_constraint(self, order: Order, route: Route) -> Optional[ValidationError]:
        """
        Validate time constraints with 15-minute stops plus deviation time
        """
        # Calculate current route time
        current_time_hours = route.total_time(base_speed_kmh=self.constants.AVG_SPEED_MPH * self.constants.MILES_TO_KM)

        # Add time for new stops (pickup + dropoff = 2 stops)
        additional_stop_time_hours = (2 * self.constants.STOP_TIME_MINUTES) / 60.0

        # Calculate deviation distance and time
        deviation_distance_km = self._calculate_route_deviation(order, route)
        deviation_time_hours = deviation_distance_km / (self.constants.AVG_SPEED_MPH * self.constants.MILES_TO_KM)

        # Total new route time
        new_total_time = current_time_hours + additional_stop_time_hours + deviation_time_hours

        if new_total_time > self.constants.MAX_ROUTE_HOURS:
            return ValidationError(
                result=ValidationResult.INVALID_TIME,
                message=f"Route would exceed maximum time: {new_total_time:.2f}h > {self.constants.MAX_ROUTE_HOURS}h",
                details={
                    "current_time_hours": current_time_hours,
                    "additional_stop_time_hours": additional_stop_time_hours,
                    "deviation_time_hours": deviation_time_hours,
                    "new_total_time_hours": new_total_time,
                    "max_allowed_hours": self.constants.MAX_ROUTE_HOURS
                }
            )

        return None

    def _validate_cargo_compatibility(self, order: Order, truck: Truck) -> Optional[ValidationError]:
        """
        Validate cargo type compatibility
        """
        if not order.cargo:
            return None

        # First, check internal compatibility within the order's cargo
        for cargo in order.cargo:
            if not self._is_internally_compatible(cargo):
                cargo_types = [pkg.type.value for pkg in cargo.packages]
                return ValidationError(
                    result=ValidationResult.INCOMPATIBLE_CARGO,
                    message=f"Incompatible cargo types within single shipment: {cargo_types}",
                    details={
                        "cargo_types": cargo_types,
                        "internal_conflict": True
                    }
                )

        # Then check compatibility with existing cargo on truck
        for new_cargo in order.cargo:
            for existing_cargo in truck.cargo_loads:
                if not new_cargo.is_compatible_with(existing_cargo):
                    new_types = [pkg.type.value for pkg in new_cargo.packages]
                    existing_types = [pkg.type.value for pkg in existing_cargo.packages]

                    return ValidationError(
                        result=ValidationResult.INCOMPATIBLE_CARGO,
                        message=f"Incompatible cargo types: {new_types} conflicts with existing {existing_types}",
                        details={
                            "new_cargo_types": new_types,
                            "existing_cargo_types": existing_types,
                            "conflict_detected": True
                        }
                    )

        return None
    
    def _is_internally_compatible(self, cargo) -> bool:
        """Check if packages within a single cargo are compatible with each other"""
        from schemas.schemas import CargoType
        
        cargo_types = cargo.get_types()
        
        # Check for incompatible combinations within this cargo
        incompatible_pairs = [
            (CargoType.HAZMAT, CargoType.FRAGILE),
            (CargoType.HAZMAT, CargoType.REFRIGERATED)
        ]
        
        for type1, type2 in incompatible_pairs:
            if type1 in cargo_types and type2 in cargo_types:
                return False
        
        return True

    def _min_distance_to_route(self, location: Location, route_points: List[Location]) -> float:
        """
        Calculate minimum distance from location to any point on route using haversine formula
        """
        min_distance = float('inf')

        for route_point in route_points:
            distance = location.distance_to(route_point)
            if distance < min_distance:
                min_distance = distance

        return min_distance

    def _calculate_distance_to_route(self, location: Location, route: Route) -> float:
        """
        Calculate minimum distance from location to route
        Wrapper for _min_distance_to_route that works with route objects
        """
        if not hasattr(route, 'path') or not route.path:
            # If route has no path, use route endpoints
            route_points = []
            if hasattr(route, 'location_origin') and route.location_origin:
                route_points.append(route.location_origin)
            if hasattr(route, 'location_destiny') and route.location_destiny:
                route_points.append(route.location_destiny)
            
            if not route_points:
                return 0.0
                
            return self._min_distance_to_route(location, route_points)
        
        return self._min_distance_to_route(location, route.path)

    def _calculate_route_deviation(self, order: Order, route: Route) -> float:
        """
        Calculate additional distance caused by adding order to route
        """
        if not hasattr(route, 'path') or not route.path or len(route.path) < 2:
            return 0.0

        # Simple approximation: distance from route endpoints to order locations
        origin_deviation = 0.0
        destiny_deviation = 0.0

        if order.location_origin:
            origin_deviation = self._min_distance_to_route(order.location_origin, route.path)

        if order.location_destiny:
            destiny_deviation = self._min_distance_to_route(order.location_destiny, route.path)

        # Return total additional distance (round trip for deviations)
        return 2 * (origin_deviation + destiny_deviation)

    def _calculate_order_metrics(self, order: Order, route: Route, truck: Truck) -> Dict[str, float]:
        """
        Calculate comprehensive metrics for the order
        """
        metrics = {}

        # Volume metrics
        order_volume_m3 = order.total_volume()
        order_volume_cf = order_volume_m3 / self.constants.CUBIC_FEET_TO_CUBIC_METERS
        metrics['order_volume_m3'] = order_volume_m3
        metrics['order_volume_cf'] = order_volume_cf

        # Weight metrics
        order_weight_kg = order.total_weight()
        order_weight_lbs = order_weight_kg / self.constants.LBS_TO_KG
        metrics['order_weight_kg'] = order_weight_kg
        metrics['order_weight_lbs'] = order_weight_lbs

        # Distance metrics
        order_distance_km = order.total_distance()
        order_distance_miles = order_distance_km * self.constants.KM_TO_MILES
        metrics['order_distance_km'] = order_distance_km
        metrics['order_distance_miles'] = order_distance_miles

        # Capacity utilization
        truck_volume_cf = truck.capacity / self.constants.CUBIC_FEET_TO_CUBIC_METERS
        volume_utilization = (order_volume_cf / truck_volume_cf) * 100 if truck_volume_cf > 0 else 0
        weight_utilization = (order_weight_lbs / self.constants.MAX_WEIGHT_LBS) * 100

        metrics['volume_utilization_percent'] = volume_utilization
        metrics['weight_utilization_percent'] = weight_utilization

        # Cost calculations using documentation constants
        deviation_distance_miles = self._calculate_route_deviation(order, route) * self.constants.KM_TO_MILES
        additional_cost = deviation_distance_miles * self.constants.TOTAL_COST_PER_MILE

        metrics['deviation_distance_miles'] = deviation_distance_miles
        metrics['additional_cost_usd'] = additional_cost

        return metrics

    def process_order_batch(self, orders: List[Order], routes: List[Route], trucks: List[Truck]) -> Dict[int, ProcessingResult]:
        """
        Process multiple orders against available routes and trucks

        Returns:
            Dictionary mapping order IDs to their processing results
        """
        results = {}

        for order in orders:
            order_id = order.id or id(order)
            best_result = None
            best_score = -1

            # Try each route-truck combination
            for i, route in enumerate(routes):
                if i < len(trucks):
                    truck = trucks[i]
                    result = self.validate_order_for_route(order, route, truck)

                    if result.is_valid:
                        # Score based on efficiency metrics
                        score = self._calculate_efficiency_score(result.metrics)
                        if score > best_score:
                            best_score = score
                            best_result = result

            # If no valid route found, return the validation result from the first route
            if best_result is None:
                if routes and trucks:
                    best_result = self.validate_order_for_route(order, routes[0], trucks[0])
                else:
                    best_result = ProcessingResult(
                        is_valid=False,
                        errors=[ValidationError(
                            result=ValidationResult.INVALID_PROXIMITY,
                            message="No routes or trucks available",
                            details={"no_resources": True}
                        )],
                        metrics={}
                    )

            results[order_id] = best_result

        return results

    def process_order_batch_v2(self, orders: List[Order], routes: List[Route], trucks: List[Truck]) -> Dict[int, ProcessingResult]:
        """
        NEW VERSION: Process multiple orders against available routes and trucks
        """
        results = {}

        for order in orders:
            order_id = order.id or id(order)

            # Simply validate against first route-truck pair
            if routes and trucks:
                result = self.validate_order_for_route(order, routes[0], trucks[0])
                results[order_id] = result
            else:
                results[order_id] = ProcessingResult(
                    is_valid=False,
                    errors=[ValidationError(
                        result=ValidationResult.INVALID_PROXIMITY,
                        message="No routes or trucks available",
                        details={"no_resources": True}
                    )],
                    metrics={}
                )

        return results

    def _calculate_efficiency_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate efficiency score for route selection
        Higher score = better match
        """
        score = 0.0

        # Prefer higher capacity utilization
        volume_util = metrics.get('volume_utilization_percent', 0)
        weight_util = metrics.get('weight_utilization_percent', 0)
        score += (volume_util + weight_util) / 2

        # Penalize high additional costs
        additional_cost = metrics.get('additional_cost_usd', 0)
        score -= additional_cost * 10  # Cost penalty factor

        # Prefer shorter deviations
        deviation_miles = metrics.get('deviation_distance_miles', 0)
        score -= deviation_miles * 5  # Distance penalty factor

        return score
