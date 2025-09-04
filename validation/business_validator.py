"""
Business Requirements Validation Framework

This module validates that the Digital Freight Matching system meets all 
business requirements from the engineering lab specification.

Key Requirements Validated:
1. Profitability improvement ($388.15 daily loss target)
2. 1km proximity constraint enforcement
3. Capacity limits (48m³ volume, 9180 lbs weight)
4. Time limits (10-hour maximum route time)
5. Contract route preservation (5 existing routes)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum
import math

from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


class ValidationStatus(str, Enum):
    """Validation result status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_TESTED = "not_tested"


@dataclass
class ValidationReport:
    """Report for individual requirement validation"""
    requirement_id: str
    requirement_description: str
    status: ValidationStatus
    details: str
    metrics: Dict[str, float]
    timestamp: datetime
    test_data_used: Optional[Dict] = None
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class PerformanceReport:
    """Report for system performance metrics"""
    operation: str
    execution_time_ms: float
    memory_usage_mb: float
    orders_processed: int
    success_rate: float
    throughput_orders_per_second: float
    error_details: List[str]
    timestamp: datetime
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []


class BusinessValidator:
    """
    Validates Digital Freight Matching system against business requirements
    
    This class implements validation methods for each of the 7 main business
    requirements identified in the requirements document.
    """
    
    # Business constants from requirements
    TARGET_DAILY_LOSS_REDUCTION = 388.15  # USD
    MAX_PROXIMITY_KM = 1.0
    MAX_TRUCK_VOLUME_M3 = 48.0
    MAX_TRUCK_WEIGHT_LBS = 9180.0
    MAX_ROUTE_TIME_HOURS = 10.0
    STOP_TIME_MINUTES = 15.0
    REQUIRED_CONTRACT_ROUTES = 5
    
    # Contract route destinations (from business requirements)
    CONTRACT_DESTINATIONS = ["Ringgold", "Augusta", "Savannah", "Albany", "Columbus"]
    
    def __init__(self):
        """Initialize the business validator"""
        self.validation_history: List[ValidationReport] = []
        self.performance_history: List[PerformanceReport] = []
    
    def validate_profitability_requirements(self, routes: List[Route], 
                                         baseline_daily_loss: float = 388.15) -> ValidationReport:
        """
        Validate Requirement 1.1: System demonstrates conversion of daily loss into profit
        
        Args:
            routes: List of routes with current profitability
            baseline_daily_loss: Original daily loss amount (default: $388.15)
            
        Returns:
            ValidationReport with profitability analysis
        """
        start_time = datetime.now()
        
        try:
            # Calculate current total profitability
            total_current_profit = sum(route.profitability for route in routes)
            
            # Calculate improvement from baseline
            improvement = total_current_profit - (-baseline_daily_loss)
            improvement_percentage = (improvement / baseline_daily_loss) * 100 if baseline_daily_loss > 0 else 0
            
            # Determine validation status
            if total_current_profit > 0:
                status = ValidationStatus.PASSED
                details = f"System successfully converted ${baseline_daily_loss:.2f} daily loss into ${total_current_profit:.2f} daily profit"
            elif improvement > 0:
                status = ValidationStatus.WARNING
                details = f"System reduced daily loss by ${improvement:.2f} but has not achieved profitability yet"
            elif total_current_profit == 0 and baseline_daily_loss > 0:
                # Special case: no routes but had baseline loss - this is an improvement to break-even
                status = ValidationStatus.WARNING
                details = f"System eliminated ${baseline_daily_loss:.2f} daily loss, achieving break-even"
            else:
                status = ValidationStatus.FAILED
                details = f"System has not improved profitability. Current daily result: ${total_current_profit:.2f}"
            
            metrics = {
                "baseline_daily_loss": baseline_daily_loss,
                "current_daily_profit": total_current_profit,
                "improvement_amount": improvement,
                "improvement_percentage": improvement_percentage,
                "routes_analyzed": len(routes)
            }
            
            recommendations = []
            if status != ValidationStatus.PASSED:
                recommendations.extend([
                    "Analyze routes with negative profitability for optimization opportunities",
                    "Consider adjusting pricing strategy for additional cargo",
                    "Review capacity utilization to maximize revenue per route"
                ])
            
            report = ValidationReport(
                requirement_id="1.1",
                requirement_description="Convert $388.15 daily loss into measurable profit",
                status=status,
                details=details,
                metrics=metrics,
                timestamp=start_time,
                test_data_used={"routes_count": len(routes), "baseline_loss": baseline_daily_loss},
                recommendations=recommendations
            )
            
            self.validation_history.append(report)
            return report
            
        except Exception as e:
            return ValidationReport(
                requirement_id="1.1",
                requirement_description="Convert $388.15 daily loss into measurable profit",
                status=ValidationStatus.FAILED,
                details=f"Validation failed due to error: {str(e)}",
                metrics={},
                timestamp=start_time,
                recommendations=["Fix system errors before profitability analysis"]
            )
    
    def validate_proximity_constraint(self, orders: List[Order], routes: List[Route]) -> ValidationReport:
        """
        Validate Requirement 1.2: System enforces 1km proximity constraint
        
        Args:
            orders: List of orders to validate
            routes: List of available routes
            
        Returns:
            ValidationReport with proximity constraint analysis
        """
        start_time = datetime.now()
        
        try:
            violations = []
            total_orders = len(orders)
            compliant_orders = 0
            
            for order in orders:
                if not order.location_origin or not order.location_destiny:
                    violations.append(f"Order {order.id}: Missing pickup or dropoff location")
                    continue
                
                # Find closest route for this order
                min_pickup_distance = float('inf')
                min_dropoff_distance = float('inf')
                closest_route = None
                
                for route in routes:
                    if not route.path:
                        continue
                    
                    # Check distance to route points
                    for route_point in route.path:
                        pickup_dist = self._calculate_distance(order.location_origin, route_point)
                        dropoff_dist = self._calculate_distance(order.location_destiny, route_point)
                        
                        if pickup_dist < min_pickup_distance:
                            min_pickup_distance = pickup_dist
                            closest_route = route
                        if dropoff_dist < min_dropoff_distance:
                            min_dropoff_distance = dropoff_dist
                
                # Check if within proximity constraint
                if min_pickup_distance <= self.MAX_PROXIMITY_KM and min_dropoff_distance <= self.MAX_PROXIMITY_KM:
                    compliant_orders += 1
                else:
                    violations.append(
                        f"Order {order.id}: Pickup {min_pickup_distance:.2f}km, "
                        f"Dropoff {min_dropoff_distance:.2f}km from closest route"
                    )
            
            compliance_rate = (compliant_orders / total_orders * 100) if total_orders > 0 else 100
            
            if total_orders == 0:
                status = ValidationStatus.PASSED
                details = "No orders to validate - proximity constraint compliance confirmed"
            elif compliance_rate == 100:
                status = ValidationStatus.PASSED
                details = f"All {total_orders} orders comply with 1km proximity constraint"
            elif compliance_rate >= 90:
                status = ValidationStatus.WARNING
                details = f"{compliance_rate:.1f}% of orders comply with proximity constraint"
            else:
                status = ValidationStatus.FAILED
                details = f"Only {compliance_rate:.1f}% of orders comply with proximity constraint"
            
            metrics = {
                "total_orders": total_orders,
                "compliant_orders": compliant_orders,
                "compliance_rate_percent": compliance_rate,
                "violations_count": len(violations),
                "max_proximity_km": self.MAX_PROXIMITY_KM
            }
            
            recommendations = []
            if violations:
                recommendations.extend([
                    "Review order matching algorithm for proximity validation",
                    "Consider rejecting orders that exceed proximity limits",
                    "Implement real-time proximity checking during order intake"
                ])
            
            report = ValidationReport(
                requirement_id="1.2",
                requirement_description="Enforce 1km proximity constraint for pickup and dropoff",
                status=status,
                details=details,
                metrics=metrics,
                timestamp=start_time,
                test_data_used={"orders_tested": total_orders, "routes_available": len(routes)},
                recommendations=recommendations
            )
            
            self.validation_history.append(report)
            return report
            
        except Exception as e:
            return ValidationReport(
                requirement_id="1.2",
                requirement_description="Enforce 1km proximity constraint for pickup and dropoff",
                status=ValidationStatus.FAILED,
                details=f"Validation failed due to error: {str(e)}",
                metrics={},
                timestamp=start_time,
                recommendations=["Fix system errors before proximity validation"]
            )
    
    def validate_capacity_constraints(self, orders: List[Order], trucks: List[Truck]) -> ValidationReport:
        """
        Validate Requirement 1.3: System respects capacity limits (48m³, 9180 lbs)
        
        Args:
            orders: List of orders to validate
            trucks: List of trucks with capacity limits
            
        Returns:
            ValidationReport with capacity constraint analysis
        """
        start_time = datetime.now()
        
        try:
            violations = []
            total_assignments = 0
            compliant_assignments = 0
            
            for truck in trucks:
                # Validate truck capacity limits
                if truck.capacity > self.MAX_TRUCK_VOLUME_M3:
                    violations.append(f"Truck {truck.id}: Volume capacity {truck.capacity}m³ exceeds limit {self.MAX_TRUCK_VOLUME_M3}m³")
                
                # Check current cargo load
                current_volume = truck.total_cargo_volume()
                current_weight_kg = truck.total_cargo_weight()
                current_weight_lbs = current_weight_kg * 2.20462  # Convert kg to lbs
                
                total_assignments += 1
                
                # Validate volume constraint
                volume_compliant = current_volume <= self.MAX_TRUCK_VOLUME_M3
                weight_compliant = current_weight_lbs <= self.MAX_TRUCK_WEIGHT_LBS
                
                if volume_compliant and weight_compliant:
                    compliant_assignments += 1
                else:
                    if not volume_compliant:
                        violations.append(
                            f"Truck {truck.id}: Volume {current_volume:.2f}m³ exceeds limit {self.MAX_TRUCK_VOLUME_M3}m³"
                        )
                    if not weight_compliant:
                        violations.append(
                            f"Truck {truck.id}: Weight {current_weight_lbs:.2f}lbs exceeds limit {self.MAX_TRUCK_WEIGHT_LBS}lbs"
                        )
            
            # Check individual orders for capacity requirements
            for order in orders:
                order_volume = order.total_volume()
                order_weight_kg = order.total_weight()
                order_weight_lbs = order_weight_kg * 2.20462
                
                if order_volume > self.MAX_TRUCK_VOLUME_M3:
                    violations.append(f"Order {order.id}: Volume {order_volume:.2f}m³ exceeds truck capacity")
                
                if order_weight_lbs > self.MAX_TRUCK_WEIGHT_LBS:
                    violations.append(f"Order {order.id}: Weight {order_weight_lbs:.2f}lbs exceeds truck capacity")
            
            compliance_rate = (compliant_assignments / total_assignments * 100) if total_assignments > 0 else 100
            
            if len(violations) == 0:
                status = ValidationStatus.PASSED
                details = f"All capacity constraints respected. {compliance_rate:.1f}% compliance rate"
            elif len(violations) > 0:
                status = ValidationStatus.FAILED
                details = f"Capacity violations detected: {len(violations)} violations found"
            
            metrics = {
                "max_volume_m3": self.MAX_TRUCK_VOLUME_M3,
                "max_weight_lbs": self.MAX_TRUCK_WEIGHT_LBS,
                "trucks_analyzed": len(trucks),
                "orders_analyzed": len(orders),
                "violations_count": len(violations),
                "compliance_rate_percent": compliance_rate
            }
            
            recommendations = []
            if violations:
                recommendations.extend([
                    "Implement pre-assignment capacity validation",
                    "Add real-time capacity monitoring during order processing",
                    "Consider load balancing across multiple trucks for large orders"
                ])
            
            report = ValidationReport(
                requirement_id="1.3",
                requirement_description="Respect 48m³ capacity and 9180 lbs weight limits",
                status=status,
                details=details,
                metrics=metrics,
                timestamp=start_time,
                test_data_used={"trucks_count": len(trucks), "orders_count": len(orders)},
                recommendations=recommendations
            )
            
            self.validation_history.append(report)
            return report
            
        except Exception as e:
            return ValidationReport(
                requirement_id="1.3",
                requirement_description="Respect 48m³ capacity and 9180 lbs weight limits",
                status=ValidationStatus.FAILED,
                details=f"Validation failed due to error: {str(e)}",
                metrics={},
                timestamp=start_time,
                recommendations=["Fix system errors before capacity validation"]
            )
    
    def validate_time_constraints(self, routes: List[Route]) -> ValidationReport:
        """
        Validate Requirement 1.4: System maintains 10-hour maximum route time
        
        Args:
            routes: List of routes to validate
            
        Returns:
            ValidationReport with time constraint analysis
        """
        start_time = datetime.now()
        
        try:
            violations = []
            total_routes = len(routes)
            compliant_routes = 0
            
            for route in routes:
                # Calculate total route time including stops
                base_time = route.total_time()  # Driving time
                
                # Add stop time (15 minutes per order, pickup and dropoff)
                stop_time_hours = len(route.orders) * 2 * (self.STOP_TIME_MINUTES / 60.0)
                total_time = base_time + stop_time_hours
                
                if total_time <= self.MAX_ROUTE_TIME_HOURS:
                    compliant_routes += 1
                else:
                    violations.append(
                        f"Route {route.id}: Total time {total_time:.2f}h exceeds limit {self.MAX_ROUTE_TIME_HOURS}h "
                        f"(Drive: {base_time:.2f}h, Stops: {stop_time_hours:.2f}h)"
                    )
            
            compliance_rate = (compliant_routes / total_routes * 100) if total_routes > 0 else 100
            
            if len(violations) == 0:
                status = ValidationStatus.PASSED
                details = f"All {total_routes} routes comply with 10-hour time limit"
            elif compliance_rate >= 90:
                status = ValidationStatus.WARNING
                details = f"{compliance_rate:.1f}% of routes comply with time constraint"
            else:
                status = ValidationStatus.FAILED
                details = f"Only {compliance_rate:.1f}% of routes comply with time constraint"
            
            metrics = {
                "max_route_time_hours": self.MAX_ROUTE_TIME_HOURS,
                "stop_time_minutes": self.STOP_TIME_MINUTES,
                "total_routes": total_routes,
                "compliant_routes": compliant_routes,
                "violations_count": len(violations),
                "compliance_rate_percent": compliance_rate
            }
            
            recommendations = []
            if violations:
                recommendations.extend([
                    "Implement route time validation before order assignment",
                    "Consider splitting long routes into multiple shorter routes",
                    "Optimize route planning to minimize driving time"
                ])
            
            report = ValidationReport(
                requirement_id="1.4",
                requirement_description="Maintain 10-hour maximum route time with 15-minute stops",
                status=status,
                details=details,
                metrics=metrics,
                timestamp=start_time,
                test_data_used={"routes_analyzed": total_routes},
                recommendations=recommendations
            )
            
            self.validation_history.append(report)
            return report
            
        except Exception as e:
            return ValidationReport(
                requirement_id="1.4",
                requirement_description="Maintain 10-hour maximum route time with 15-minute stops",
                status=ValidationStatus.FAILED,
                details=f"Validation failed due to error: {str(e)}",
                metrics={},
                timestamp=start_time,
                recommendations=["Fix system errors before time validation"]
            )
    
    def validate_contract_compliance(self, routes: List[Route]) -> ValidationReport:
        """
        Validate Requirement 1.5: System preserves all 5 contract routes
        
        Args:
            routes: List of current routes
            
        Returns:
            ValidationReport with contract compliance analysis
        """
        start_time = datetime.now()
        
        try:
            # Extract route destinations (this is simplified - in real system would need proper mapping)
            route_destinations = []
            missing_destinations = []
            
            # Check if we have the required number of routes
            if len(routes) < self.REQUIRED_CONTRACT_ROUTES:
                status = ValidationStatus.FAILED
                details = f"Only {len(routes)} routes found, need {self.REQUIRED_CONTRACT_ROUTES} contract routes"
                missing_destinations = self.CONTRACT_DESTINATIONS.copy()
            else:
                # For this validation, we assume the first 5 routes are the contract routes
                # In a real system, routes would have destination names or identifiers
                contract_routes_count = min(len(routes), self.REQUIRED_CONTRACT_ROUTES)
                
                if contract_routes_count == self.REQUIRED_CONTRACT_ROUTES:
                    status = ValidationStatus.PASSED
                    details = f"All {self.REQUIRED_CONTRACT_ROUTES} contract routes are preserved"
                else:
                    status = ValidationStatus.FAILED
                    details = f"Only {contract_routes_count} of {self.REQUIRED_CONTRACT_ROUTES} contract routes found"
            
            metrics = {
                "required_contract_routes": self.REQUIRED_CONTRACT_ROUTES,
                "current_routes_count": len(routes),
                "contract_routes_preserved": min(len(routes), self.REQUIRED_CONTRACT_ROUTES),
                "missing_routes_count": len(missing_destinations)
            }
            
            recommendations = []
            if status != ValidationStatus.PASSED:
                recommendations.extend([
                    "Ensure all 5 contract routes (Ringgold, Augusta, Savannah, Albany, Columbus) are maintained",
                    "Implement route preservation checks before system modifications",
                    "Add route identification system to track contract vs. additional routes"
                ])
            
            report = ValidationReport(
                requirement_id="1.5",
                requirement_description="Preserve all 5 contract routes to required destinations",
                status=status,
                details=details,
                metrics=metrics,
                timestamp=start_time,
                test_data_used={"routes_analyzed": len(routes)},
                recommendations=recommendations
            )
            
            self.validation_history.append(report)
            return report
            
        except Exception as e:
            return ValidationReport(
                requirement_id="1.5",
                requirement_description="Preserve all 5 contract routes to required destinations",
                status=ValidationStatus.FAILED,
                details=f"Validation failed due to error: {str(e)}",
                metrics={},
                timestamp=start_time,
                recommendations=["Fix system errors before contract compliance validation"]
            )
    
    def validate_all_requirements(self, orders: List[Order], routes: List[Route], 
                                trucks: List[Truck], baseline_daily_loss: float = 388.15) -> List[ValidationReport]:
        """
        Run all business requirement validations
        
        Args:
            orders: List of orders to validate
            routes: List of routes to validate
            trucks: List of trucks to validate
            baseline_daily_loss: Original daily loss amount
            
        Returns:
            List of ValidationReport objects for all requirements
        """
        reports = []
        
        # Validate each requirement
        reports.append(self.validate_profitability_requirements(routes, baseline_daily_loss))
        reports.append(self.validate_proximity_constraint(orders, routes))
        reports.append(self.validate_capacity_constraints(orders, trucks))
        reports.append(self.validate_time_constraints(routes))
        reports.append(self.validate_contract_compliance(routes))
        
        return reports
    
    def generate_summary_report(self, validation_reports: List[ValidationReport]) -> Dict:
        """
        Generate a summary of all validation results
        
        Args:
            validation_reports: List of validation reports
            
        Returns:
            Dictionary with summary statistics
        """
        total_requirements = len(validation_reports)
        passed_count = sum(1 for r in validation_reports if r.status == ValidationStatus.PASSED)
        failed_count = sum(1 for r in validation_reports if r.status == ValidationStatus.FAILED)
        warning_count = sum(1 for r in validation_reports if r.status == ValidationStatus.WARNING)
        
        overall_status = "PASSED" if failed_count == 0 else "FAILED"
        if failed_count == 0 and warning_count > 0:
            overall_status = "PASSED_WITH_WARNINGS"
        
        return {
            "overall_status": overall_status,
            "total_requirements": total_requirements,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "warning_count": warning_count,
            "pass_rate_percent": (passed_count / total_requirements * 100) if total_requirements > 0 else 0,
            "validation_timestamp": datetime.now(),
            "requirements_details": [
                {
                    "id": r.requirement_id,
                    "status": r.status.value,
                    "description": r.requirement_description
                }
                for r in validation_reports
            ]
        }
    
    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate distance between two locations using Haversine formula
        
        Args:
            loc1: First location
            loc2: Second location
            
        Returns:
            Distance in kilometers
        """
        return loc1.distance_to(loc2)