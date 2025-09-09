"""
Demo Test Runner for Enhanced Demo Testing

This module implements comprehensive testing using parsed test data and existing
business validation logic to demonstrate both successful and failed scenarios.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from demos.enhanced_demo_testing.test_data_parser import TestDataParser, TestOrder
from validation.business_validator import BusinessValidator, ValidationReport, ValidationStatus
from schemas.schemas import Order, Route, Truck, Location, Cargo, CargoType


class OrderTestStatus(str, Enum):
    """Status of individual order test"""
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class ConstraintResult:
    """Result of a specific constraint validation"""
    constraint_type: str
    passed: bool
    required_value: float
    actual_value: float
    severity: str
    description: str


@dataclass
class ProfitabilityResult:
    """Result of profitability calculation"""
    is_profitable: bool
    profit_amount: float
    revenue: float
    cost: float
    profit_margin_percent: float
    explanation: str


@dataclass
class OrderTestResult:
    """Complete result of testing a single order"""
    order_id: int
    test_description: str
    status: OrderTestStatus
    profitability_result: ProfitabilityResult
    constraint_violations: List[ConstraintResult]
    processing_time_ms: float
    detailed_explanation: str
    route_used: Optional[Route] = None
    truck_used: Optional[Truck] = None
    error_message: Optional[str] = None


@dataclass
class DemoTestResults:
    """Complete results from comprehensive demo testing"""
    total_orders_tested: int
    successful_orders: int
    failed_orders: int
    error_orders: int
    total_processing_time_ms: float
    average_processing_time_ms: float
    detailed_results: List[OrderTestResult]
    validation_reports: List[ValidationReport]
    test_summary: Dict[str, Any]
    timestamp: datetime


class DemoTestRunner:
    """
    Comprehensive demo test runner that processes test orders through
    business validation and generates detailed success/failure scenarios.
    """
    
    # Business constants for calculations
    BASE_REVENUE_PER_ORDER = 150.0  # USD per order
    COST_PER_KM = 1.2  # USD per kilometer
    BASE_SPEED_KMH = 80.0  # Average speed for time calculations
    
    def __init__(self):
        """Initialize the demo test runner"""
        self.test_data_parser = TestDataParser()
        self.business_validator = BusinessValidator()
        self.test_orders: List[TestOrder] = []
        self.test_routes: List[Route] = []
        self.test_trucks: List[Truck] = []
    
    def run_comprehensive_demo(self, test_data_path: Optional[str] = None) -> DemoTestResults:
        """
        Run comprehensive demo testing on all test orders
        
        Args:
            test_data_path: Optional path to test data file
            
        Returns:
            DemoTestResults with complete analysis
        """
        start_time = time.time()
        
        try:
            # Load test data
            self.test_orders = self.test_data_parser.load_test_data(test_data_path)
            self.test_routes = self.test_data_parser.create_test_routes()
            self.test_trucks = self.test_data_parser.create_test_trucks()
            
            print(f"Loaded {len(self.test_orders)} test orders for comprehensive demo")
            
            # Process each order
            detailed_results = []
            successful_count = 0
            failed_count = 0
            error_count = 0
            
            for i, test_order in enumerate(self.test_orders):
                print(f"Processing order {i + 1}/{len(self.test_orders)}: {test_order.test_description}")
                
                result = self.process_single_order(test_order)
                detailed_results.append(result)
                
                if result.status == OrderTestStatus.SUCCESS:
                    successful_count += 1
                elif result.status == OrderTestStatus.FAILED:
                    failed_count += 1
                else:
                    error_count += 1
            
            # Run business validation on all orders
            orders = [test_order.order for test_order in self.test_orders]
            validation_reports = self.business_validator.validate_all_requirements(
                orders, self.test_routes, self.test_trucks
            )
            
            # Calculate total processing time
            total_time_ms = (time.time() - start_time) * 1000
            avg_time_ms = total_time_ms / len(self.test_orders) if self.test_orders else 0
            
            # Generate test summary
            test_summary = self._generate_test_summary(detailed_results)
            
            return DemoTestResults(
                total_orders_tested=len(self.test_orders),
                successful_orders=successful_count,
                failed_orders=failed_count,
                error_orders=error_count,
                total_processing_time_ms=total_time_ms,
                average_processing_time_ms=avg_time_ms,
                detailed_results=detailed_results,
                validation_reports=validation_reports,
                test_summary=test_summary,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            # Return error result if demo fails
            return DemoTestResults(
                total_orders_tested=0,
                successful_orders=0,
                failed_orders=0,
                error_orders=1,
                total_processing_time_ms=(time.time() - start_time) * 1000,
                average_processing_time_ms=0,
                detailed_results=[],
                validation_reports=[],
                test_summary={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def process_single_order(self, test_order: TestOrder) -> OrderTestResult:
        """
        Process a single test order through validation and profitability analysis
        
        Args:
            test_order: TestOrder to process
            
        Returns:
            OrderTestResult with detailed analysis
        """
        start_time = time.time()
        
        try:
            order = test_order.order
            
            # Find best matching route and truck
            best_route, best_truck = self._find_best_match(order)
            
            if not best_route or not best_truck:
                # No suitable route/truck found
                processing_time = (time.time() - start_time) * 1000
                return OrderTestResult(
                    order_id=order.id or test_order.order_index,
                    test_description=test_order.test_description,
                    status=OrderTestStatus.FAILED,
                    profitability_result=ProfitabilityResult(
                        is_profitable=False,
                        profit_amount=-50.0,  # Opportunity cost
                        revenue=0.0,
                        cost=50.0,
                        profit_margin_percent=-100.0,
                        explanation="No suitable route or truck available"
                    ),
                    constraint_violations=[],
                    processing_time_ms=processing_time,
                    detailed_explanation="Order rejected: No matching route or compatible truck found",
                    route_used=None,
                    truck_used=None
                )
            
            # Validate business constraints
            constraint_violations = self.validate_business_constraints(order, best_route, best_truck)
            
            # Calculate profitability impact
            profitability_result = self.calculate_profitability_impact(order, best_route, best_truck)
            
            # Determine overall status
            has_critical_violations = any(
                violation.severity == "critical" for violation in constraint_violations
            )
            
            if has_critical_violations or not profitability_result.is_profitable:
                status = OrderTestStatus.FAILED
                explanation = self._generate_failure_explanation(
                    constraint_violations, profitability_result
                )
            else:
                status = OrderTestStatus.SUCCESS
                explanation = self._generate_success_explanation(
                    profitability_result, constraint_violations
                )
            
            processing_time = (time.time() - start_time) * 1000
            
            return OrderTestResult(
                order_id=order.id or test_order.order_index,
                test_description=test_order.test_description,
                status=status,
                profitability_result=profitability_result,
                constraint_violations=constraint_violations,
                processing_time_ms=processing_time,
                detailed_explanation=explanation,
                route_used=best_route,
                truck_used=best_truck
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return OrderTestResult(
                order_id=test_order.order_index,
                test_description=test_order.test_description,
                status=OrderTestStatus.ERROR,
                profitability_result=ProfitabilityResult(
                    is_profitable=False,
                    profit_amount=0.0,
                    revenue=0.0,
                    cost=0.0,
                    profit_margin_percent=0.0,
                    explanation="Processing error occurred"
                ),
                constraint_violations=[],
                processing_time_ms=processing_time,
                detailed_explanation=f"Error processing order: {str(e)}",
                error_message=str(e)
            )
    
    def validate_business_constraints(self, order: Order, route: Route, truck: Truck) -> List[ConstraintResult]:
        """
        Validate business constraints for an order-route-truck combination
        
        Args:
            order: Order to validate
            route: Route to use
            truck: Truck to use
            
        Returns:
            List of ConstraintResult objects
        """
        violations = []
        
        # 1. Proximity constraint (1km)
        if order.location_origin and order.location_destiny and route.location_origin and route.location_destiny:
            pickup_distance = order.location_origin.distance_to(route.location_origin)
            dropoff_distance = order.location_destiny.distance_to(route.location_destiny)
            
            max_proximity = self.business_validator.MAX_PROXIMITY_KM
            
            if pickup_distance > max_proximity:
                violations.append(ConstraintResult(
                    constraint_type="proximity_pickup",
                    passed=False,
                    required_value=max_proximity,
                    actual_value=pickup_distance,
                    severity="critical",
                    description=f"Pickup location {pickup_distance:.2f}km from route (max {max_proximity}km)"
                ))
            
            if dropoff_distance > max_proximity:
                violations.append(ConstraintResult(
                    constraint_type="proximity_dropoff",
                    passed=False,
                    required_value=max_proximity,
                    actual_value=dropoff_distance,
                    severity="critical",
                    description=f"Dropoff location {dropoff_distance:.2f}km from route (max {max_proximity}km)"
                ))
        
        # 2. Capacity constraints
        order_volume = order.total_volume()
        order_weight_kg = order.total_weight()
        order_weight_lbs = order_weight_kg * 2.20462
        
        max_volume = self.business_validator.MAX_TRUCK_VOLUME_M3
        max_weight = self.business_validator.MAX_TRUCK_WEIGHT_LBS
        
        if order_volume > max_volume:
            violations.append(ConstraintResult(
                constraint_type="volume_capacity",
                passed=False,
                required_value=max_volume,
                actual_value=order_volume,
                severity="critical",
                description=f"Order volume {order_volume:.1f}m³ exceeds truck capacity {max_volume}m³"
            ))
        
        if order_weight_lbs > max_weight:
            violations.append(ConstraintResult(
                constraint_type="weight_capacity",
                passed=False,
                required_value=max_weight,
                actual_value=order_weight_lbs,
                severity="critical",
                description=f"Order weight {order_weight_lbs:.1f}lbs exceeds truck capacity {max_weight}lbs"
            ))
        
        # Check available capacity on truck
        available_capacity = truck.available_capacity()
        if order_volume > available_capacity:
            violations.append(ConstraintResult(
                constraint_type="available_capacity",
                passed=False,
                required_value=available_capacity,
                actual_value=order_volume,
                severity="critical",
                description=f"Order volume {order_volume:.1f}m³ exceeds available capacity {available_capacity:.1f}m³"
            ))
        
        # 3. Time constraints
        route_distance = route.total_distance() + order.total_distance()
        estimated_time = route_distance / self.BASE_SPEED_KMH
        stop_time = 2 * 0.25  # 15 minutes each for pickup and dropoff
        total_time = estimated_time + stop_time
        
        max_time = self.business_validator.MAX_ROUTE_TIME_HOURS
        
        if total_time > max_time:
            violations.append(ConstraintResult(
                constraint_type="time_limit",
                passed=False,
                required_value=max_time,
                actual_value=total_time,
                severity="warning",
                description=f"Route time {total_time:.1f}h exceeds limit {max_time}h"
            ))
        
        # 4. Cargo compatibility
        if order.cargo:
            cargo_types = set()
            for cargo in order.cargo:
                cargo_types.update(cargo.get_types())
            
            # Check truck compatibility
            if CargoType.HAZMAT in cargo_types and truck.type != "hazmat":
                violations.append(ConstraintResult(
                    constraint_type="cargo_compatibility",
                    passed=False,
                    required_value=1.0,  # Boolean as float
                    actual_value=0.0,
                    severity="critical",
                    description=f"Hazmat cargo requires hazmat-certified truck, got {truck.type}"
                ))
            
            if CargoType.REFRIGERATED in cargo_types and truck.type != "refrigerated":
                violations.append(ConstraintResult(
                    constraint_type="cargo_compatibility",
                    passed=False,
                    required_value=1.0,
                    actual_value=0.0,
                    severity="critical",
                    description=f"Refrigerated cargo requires refrigerated truck, got {truck.type}"
                ))
        
        # 5. Range/autonomy constraint
        total_route_distance = route.total_distance() + order.total_distance()
        if total_route_distance > truck.autonomy:
            violations.append(ConstraintResult(
                constraint_type="range_limit",
                passed=False,
                required_value=truck.autonomy,
                actual_value=total_route_distance,
                severity="critical",
                description=f"Route distance {total_route_distance:.1f}km exceeds truck range {truck.autonomy}km"
            ))
        
        return violations
    
    def calculate_profitability_impact(self, order: Order, route: Route, truck: Truck) -> ProfitabilityResult:
        """
        Calculate the profitability impact of adding this order to the route
        
        Args:
            order: Order to analyze
            route: Route to use
            truck: Truck to use
            
        Returns:
            ProfitabilityResult with financial analysis
        """
        try:
            # Calculate revenue
            base_revenue = self.BASE_REVENUE_PER_ORDER
            
            # Adjust revenue based on cargo type and volume
            volume_bonus = order.total_volume() * 2.0  # $2 per m³
            
            # Hazmat and refrigerated cargo get premium pricing
            cargo_premium = 0.0
            if order.cargo:
                for cargo in order.cargo:
                    cargo_types = cargo.get_types()
                    if CargoType.HAZMAT in cargo_types:
                        cargo_premium += 50.0  # $50 hazmat premium
                    if CargoType.REFRIGERATED in cargo_types:
                        cargo_premium += 30.0  # $30 refrigerated premium
            
            total_revenue = base_revenue + volume_bonus + cargo_premium
            
            # Calculate costs
            additional_distance = order.total_distance()
            distance_cost = additional_distance * self.COST_PER_KM
            
            # Add handling costs
            handling_cost = 20.0  # Base handling cost per order
            
            # Add fuel cost based on truck type and cargo weight
            weight_factor = order.total_weight() / 1000.0  # Convert kg to tons
            fuel_cost = weight_factor * 5.0  # $5 per ton
            
            total_cost = distance_cost + handling_cost + fuel_cost
            
            # Calculate profit
            profit = total_revenue - total_cost
            profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else -100
            
            # Determine if profitable (minimum 10% margin required)
            is_profitable = profit > 0 and profit_margin >= 10.0
            
            # Generate explanation
            if is_profitable:
                explanation = (f"Profitable order: ${profit:.2f} profit ({profit_margin:.1f}% margin). "
                             f"Revenue: ${total_revenue:.2f}, Cost: ${total_cost:.2f}")
            else:
                explanation = (f"Unprofitable order: ${profit:.2f} loss ({profit_margin:.1f}% margin). "
                             f"Revenue: ${total_revenue:.2f}, Cost: ${total_cost:.2f}")
            
            return ProfitabilityResult(
                is_profitable=is_profitable,
                profit_amount=profit,
                revenue=total_revenue,
                cost=total_cost,
                profit_margin_percent=profit_margin,
                explanation=explanation
            )
            
        except Exception as e:
            return ProfitabilityResult(
                is_profitable=False,
                profit_amount=0.0,
                revenue=0.0,
                cost=0.0,
                profit_margin_percent=0.0,
                explanation=f"Error calculating profitability: {str(e)}"
            )
    
    def _find_best_match(self, order: Order) -> Tuple[Optional[Route], Optional[Truck]]:
        """
        Find the best matching route and truck for an order
        
        Args:
            order: Order to match
            
        Returns:
            Tuple of (best_route, best_truck) or (None, None) if no match
        """
        best_route = None
        best_truck = None
        best_score = -1
        
        for route in self.test_routes:
            for truck in self.test_trucks:
                score = self._calculate_match_score(order, route, truck)
                if score > best_score:
                    best_score = score
                    best_route = route
                    best_truck = truck
        
        return best_route, best_truck
    
    def _calculate_match_score(self, order: Order, route: Route, truck: Truck) -> float:
        """
        Calculate a matching score for order-route-truck combination
        
        Args:
            order: Order to score
            route: Route to score
            truck: Truck to score
            
        Returns:
            Score (higher is better, -1 for incompatible)
        """
        try:
            score = 0.0
            
            # Check basic compatibility first
            if not order.location_origin or not order.location_destiny:
                return -1
            if not route.location_origin or not route.location_destiny:
                return -1
            
            # Distance score (closer is better)
            pickup_distance = order.location_origin.distance_to(route.location_origin)
            dropoff_distance = order.location_destiny.distance_to(route.location_destiny)
            
            # Reject if too far (beyond proximity constraint)
            if pickup_distance > self.business_validator.MAX_PROXIMITY_KM:
                return -1
            if dropoff_distance > self.business_validator.MAX_PROXIMITY_KM:
                return -1
            
            # Score based on proximity (closer = higher score)
            proximity_score = max(0, 10 - (pickup_distance + dropoff_distance))
            score += proximity_score
            
            # Capacity score
            order_volume = order.total_volume()
            if order_volume > truck.capacity:
                return -1  # Cannot fit
            
            available_capacity = truck.available_capacity()
            if order_volume > available_capacity:
                return -1  # No space available
            
            # Score based on capacity utilization (better utilization = higher score)
            utilization = order_volume / truck.capacity
            capacity_score = utilization * 5  # Max 5 points for full utilization
            score += capacity_score
            
            # Cargo compatibility score
            if order.cargo:
                for cargo in order.cargo:
                    cargo_types = cargo.get_types()
                    
                    # Check truck type compatibility
                    if CargoType.HAZMAT in cargo_types:
                        if truck.type == "hazmat":
                            score += 3  # Bonus for correct truck type
                        else:
                            return -1  # Incompatible
                    
                    if CargoType.REFRIGERATED in cargo_types:
                        if truck.type == "refrigerated":
                            score += 3  # Bonus for correct truck type
                        else:
                            return -1  # Incompatible
                    
                    # Standard cargo works with any truck
                    if CargoType.STANDARD in cargo_types:
                        score += 1
            
            # Range compatibility
            total_distance = route.total_distance() + order.total_distance()
            if total_distance > truck.autonomy:
                return -1  # Cannot reach
            
            # Bonus for good range utilization
            range_utilization = total_distance / truck.autonomy
            if 0.3 <= range_utilization <= 0.8:  # Sweet spot
                score += 2
            
            return score
            
        except Exception:
            return -1  # Error in calculation
    
    def _generate_success_explanation(self, profitability: ProfitabilityResult, 
                                    violations: List[ConstraintResult]) -> str:
        """Generate explanation for successful order processing"""
        explanation = f"✅ ORDER ACCEPTED: {profitability.explanation}"
        
        if violations:
            warnings = [v for v in violations if v.severity == "warning"]
            if warnings:
                explanation += f"\n⚠️  Warnings: {len(warnings)} constraint warnings detected"
                for warning in warnings[:2]:  # Show first 2 warnings
                    explanation += f"\n   - {warning.description}"
        else:
            explanation += "\n✅ All business constraints satisfied"
        
        return explanation
    
    def _generate_failure_explanation(self, violations: List[ConstraintResult], 
                                    profitability: ProfitabilityResult) -> str:
        """Generate explanation for failed order processing"""
        critical_violations = [v for v in violations if v.severity == "critical"]
        
        if critical_violations:
            explanation = f"❌ ORDER REJECTED: {len(critical_violations)} critical constraint violations"
            for violation in critical_violations[:3]:  # Show first 3 violations
                explanation += f"\n   - {violation.description}"
        elif not profitability.is_profitable:
            explanation = f"❌ ORDER REJECTED: {profitability.explanation}"
        else:
            explanation = "❌ ORDER REJECTED: Unknown reason"
        
        return explanation
    
    def _generate_test_summary(self, results: List[OrderTestResult]) -> Dict[str, Any]:
        """Generate summary statistics from test results"""
        if not results:
            return {"error": "No results to summarize"}
        
        total_orders = len(results)
        successful = sum(1 for r in results if r.status == OrderTestStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == OrderTestStatus.FAILED)
        errors = sum(1 for r in results if r.status == OrderTestStatus.ERROR)
        
        # Calculate profitability metrics
        profitable_orders = sum(1 for r in results if r.profitability_result.is_profitable)
        total_profit = sum(r.profitability_result.profit_amount for r in results)
        total_revenue = sum(r.profitability_result.revenue for r in results)
        total_cost = sum(r.profitability_result.cost for r in results)
        
        # Performance metrics
        avg_processing_time = sum(r.processing_time_ms for r in results) / total_orders
        max_processing_time = max(r.processing_time_ms for r in results)
        min_processing_time = min(r.processing_time_ms for r in results)
        
        # Constraint violation analysis
        constraint_types = {}
        for result in results:
            for violation in result.constraint_violations:
                constraint_types[violation.constraint_type] = constraint_types.get(violation.constraint_type, 0) + 1
        
        return {
            "total_orders": total_orders,
            "success_rate_percent": (successful / total_orders * 100),
            "failure_rate_percent": (failed / total_orders * 100),
            "error_rate_percent": (errors / total_orders * 100),
            "profitable_orders": profitable_orders,
            "profitability_rate_percent": (profitable_orders / total_orders * 100),
            "total_profit": round(total_profit, 2),
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "average_processing_time_ms": round(avg_processing_time, 2),
            "max_processing_time_ms": round(max_processing_time, 2),
            "min_processing_time_ms": round(min_processing_time, 2),
            "common_constraint_violations": constraint_types,
            "orders_by_status": {
                "successful": successful,
                "failed": failed,
                "errors": errors
            }
        }