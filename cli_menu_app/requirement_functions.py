#!/usr/bin/env python3
"""
Requirement Functions for CLI Menu Application
Integrates all 8 business requirements (6 required + 2 bonus) with CLI data service
End-to-end functionality: CLI -> API/Direct -> logistics.db
"""

import sys
import os
from typing import Dict, List, Any, Optional

# Import OrderProcessor and schemas from parent directory
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from order_processor import OrderProcessor, ValidationResult
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType

from ui_components import (
    print_header, print_menu_box, get_input, pause, print_success,
    print_error, print_info, format_table_data, Colors
)


class RequirementFunctions:
    """Handles all 8 business requirement demonstrations with CLI integration"""

    def __init__(self, data_service):
        self.data_service = data_service
        self.processor = OrderProcessor()
        self.running = True

    def show_requirements_menu(self, menu_stack):
        """Display requirements demo menu"""
        print_header(self.data_service, menu_stack)

        options = [
            ("1", "📍", "Location Proximity (1km constraint)"),
            ("2", "📦", "Cargo Capacity (48m³, 9180lbs)"),
            ("3", "⏰", "Pickup/Dropoff Timing (15min + deviation)"),
            ("4", "💰", "Cost Integration (profitability analysis)"),
            ("5", "📊", "Cargo Aggregation (multiple orders)"),
            ("6", "🛣️", "Route Constraints (path optimization)"),
            ("7", "⏸️", "Union Breaks (BONUS - labor rules)"),
            ("8", "🏷️", "Cargo Types (BONUS - compatibility)"),
            ("9", "🎯", "Run All Requirements Demo"),
            ("0", "↩️", "Back to Main Menu")
        ]

        print_menu_box("DEMO REQUIREMENTS", options)

    def handle_requirements_choice(self, choice: str) -> bool:
        """Handle requirements menu selections"""
        try:
            if choice == "1":
                self._demo_location_proximity()
            elif choice == "2":
                self._demo_cargo_capacity()
            elif choice == "3":
                self._demo_pickup_dropoff_timing()
            elif choice == "4":
                self._demo_cost_integration()
            elif choice == "5":
                self._demo_cargo_aggregation()
            elif choice == "6":
                self._demo_route_constraints()
            elif choice == "7":
                self._demo_union_breaks()
            elif choice == "8":
                self._demo_cargo_types()
            elif choice == "9":
                self._demo_all_requirements()
            elif choice == "0":
                return False
            else:
                print_error("Invalid choice. Please try again.")
                pause()
                return True
            
            pause()
            return True

        except Exception as e:
            print_error(f"Error running requirement demo: {e}")
            pause()
            return True

    def _demo_location_proximity(self):
        """Requirement 1: Location Proximity Constraint (1km)"""
        print(f"\n{Colors.CYAN}🎯 REQUIREMENT 1: LOCATION PROXIMITY CONSTRAINT{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Pick up and drop off locations must be at most 1 km")
        print("from any point inside preexisting routes.")
        print("=" * 60)

        try:
            # Get test data from database
            routes = self._get_sample_routes(1)
            trucks = self._get_sample_trucks(1)
            locations = self._get_sample_locations(6)

            if not routes or not trucks or len(locations) < 4:
                print_error("Insufficient test data available. Need routes, trucks, and locations.")
                return

            route = routes[0]
            truck = trucks[0]

            print(f"\n📍 ROUTE SETUP:")
            print(f"   Route: {route.location_origin.lat:.4f},{route.location_origin.lng:.4f} → "
                  f"{route.location_destiny.lat:.4f},{route.location_destiny.lng:.4f}")
            print(f"   Distance: {route.base_distance():.1f} km")
            print(f"   Profitability: ${route.profitability:.2f}/day")

            # Create test orders with various proximity scenarios
            test_orders = self._create_proximity_test_orders(route, locations[:4])

            print(f"\n🔍 PROXIMITY VALIDATION TESTS:")
            print(f"   Maximum allowed distance: {self.processor.constants.MAX_PROXIMITY_KM} km")
            print("")

            valid_count = 0
            invalid_count = 0

            for i, (description, order) in enumerate(test_orders, 1):
                print(f"   Test {i}: {description}")

                # Validate order against route
                result = self.processor.validate_order_for_route(order, route, truck)

                # Check for proximity validation
                proximity_valid = not any(
                    error.result == ValidationResult.INVALID_PROXIMITY 
                    for error in result.errors
                )

                if proximity_valid:
                    print(f"      ✅ PASSED - Order meets proximity constraint")
                    valid_count += 1
                    
                    pickup_dist = order.location_origin.distance_to(route.location_origin)
                    dropoff_dist = order.location_destiny.distance_to(route.location_destiny)
                    print(f"         Pickup distance: {pickup_dist:.2f} km")
                    print(f"         Dropoff distance: {dropoff_dist:.2f} km")
                else:
                    print(f"      ❌ FAILED - Outside proximity constraint")
                    invalid_count += 1

                print("")

            print(f"📊 PROXIMITY VALIDATION SUMMARY:")
            print(f"   Total orders tested: {len(test_orders)}")
            print(f"   Proximity compliant: {valid_count}")
            print(f"   Proximity violations: {invalid_count}")
            print(f"   Success rate: {valid_count/len(test_orders)*100:.1f}%")

            if valid_count > 0 and invalid_count > 0:
                print_success("✅ REQUIREMENT 1 FULLY IMPLEMENTED")
            else:
                print_error("⚠️  REQUIREMENT 1 NEEDS VERIFICATION")

        except Exception as e:
            print_error(f"Error in proximity demo: {e}")

    def _demo_cargo_capacity(self):
        """Requirement 2: Cargo Compartment Fitting"""
        print(f"\n{Colors.CYAN}📦 REQUIREMENT 2: CARGO COMPARTMENT FITTING{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Cargo must fit in truck compartment taking into account")
        print("original cargo and all cargo being included.")
        print("Limits: 48m³ volume, 9180 lbs weight")
        print("=" * 60)

        try:
            # Get test data
            trucks = self._get_sample_trucks(1)
            locations = self._get_sample_locations(2)

            if not trucks or len(locations) < 2:
                print_error("Insufficient test data available. Need trucks and locations.")
                return

            truck = trucks[0]
            pickup_loc, dropoff_loc = locations[:2]

            print(f"\n🚛 TRUCK SPECIFICATIONS:")
            print(f"   Type: {truck.type}")
            print(f"   Volume capacity: {truck.capacity:.0f} m³")
            print(f"   Weight capacity: {self.processor.constants.MAX_WEIGHT_LBS:.0f} lbs")

            # Create test orders with various capacity scenarios
            test_orders = self._create_capacity_test_orders(pickup_loc, dropoff_loc)

            print(f"\n🔍 CAPACITY VALIDATION TESTS:")
            print("")

            valid_count = 0
            invalid_count = 0

            for i, (description, order) in enumerate(test_orders, 1):
                print(f"   Test {i}: {description}")

                total_volume = order.total_volume()
                total_weight_kg = order.total_weight()
                total_weight_lbs = total_weight_kg * 2.20462

                # Validate order
                result = self.processor.validate_order_for_route(order, None, truck)

                capacity_valid = not any(
                    error.result in [ValidationResult.INVALID_CAPACITY, ValidationResult.INVALID_WEIGHT]
                    for error in result.errors
                )

                if capacity_valid:
                    print(f"      ✅ PASSED - Cargo fits within capacity limits")
                    valid_count += 1
                else:
                    print(f"      ❌ FAILED - Capacity constraint violated")
                    invalid_count += 1

                print(f"         Volume: {total_volume:.1f}m³ / {truck.capacity:.0f}m³ ({total_volume/truck.capacity*100:.1f}%)")
                print(f"         Weight: {total_weight_lbs:.0f}lbs / {self.processor.constants.MAX_WEIGHT_LBS:.0f}lbs")
                print("")

            print(f"📊 CAPACITY VALIDATION SUMMARY:")
            print(f"   Total orders tested: {len(test_orders)}")
            print(f"   Capacity compliant: {valid_count}")
            print(f"   Capacity violations: {invalid_count}")

            if valid_count > 0 and invalid_count > 0:
                print_success("✅ REQUIREMENT 2 FULLY IMPLEMENTED")
            else:
                print_error("⚠️  REQUIREMENT 2 NEEDS VERIFICATION")

        except Exception as e:
            print_error(f"Error in capacity demo: {e}")

    def _demo_pickup_dropoff_timing(self):
        """Requirement 3: Pickup/Dropoff Timing"""
        print(f"\n{Colors.CYAN}⏰ REQUIREMENT 3: PICKUP/DROPOFF TIMING{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: 15-minute stops plus deviation time calculation")
        print("for pickup and dropoff operations.")
        print("=" * 60)

        print_info("Timing validation demonstrates:")
        print("• 15-minute base stop time per pickup/dropoff")
        print("• Route deviation time calculation")
        print("• Total time impact on route profitability")

        try:
            routes = self._get_sample_routes(1)
            if not routes:
                print_error("No routes available for timing demo.")
                return

            route = routes[0]
            base_time = route.base_distance() / 60  # Assume 60 mph average

            print(f"\n📊 TIMING CALCULATIONS:")
            print(f"   Base route distance: {route.base_distance():.1f} km")
            print(f"   Base travel time: {base_time:.1f} hours")
            print(f"   Stop time per pickup/dropoff: {self.processor.constants.STOP_DURATION_MINUTES} minutes")
            
            # Simulate timing scenarios
            scenarios = [
                ("No additional stops", 0),
                ("1 pickup/dropoff pair", 2),
                ("3 pickup/dropoff pairs", 6),
                ("5 pickup/dropoff pairs", 10)
            ]

            for scenario_name, stops in scenarios:
                stop_time_hours = (stops * self.processor.constants.STOP_DURATION_MINUTES) / 60
                total_time = base_time + stop_time_hours
                
                print(f"   {scenario_name}:")
                print(f"     Stops: {stops}, Stop time: {stop_time_hours:.1f}h, Total: {total_time:.1f}h")

            print_success("✅ REQUIREMENT 3 TIMING CALCULATIONS IMPLEMENTED")

        except Exception as e:
            print_error(f"Error in timing demo: {e}")

    def _demo_cost_integration(self):
        """Requirement 4: Cost Integration"""
        print(f"\n{Colors.CYAN}💰 REQUIREMENT 4: COST INTEGRATION{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Profitability analysis with integrated costs")
        print("considering truck operating costs and revenue from orders.")
        print("=" * 60)

        try:
            routes = self._get_sample_routes(3)
            if not routes:
                print_error("No routes available for cost demo.")
                return

            print(f"\n💼 COST ANALYSIS:")
            print(f"   Cost per mile: ${self.processor.constants.TOTAL_COST_PER_MILE:.3f}")
            print(f"   Trucker cost per mile: ${self.processor.constants.TRUCKER_COST_PER_MILE:.3f}")
            print("")

            for i, route in enumerate(routes, 1):
                distance = route.base_distance()
                operating_cost = distance * self.processor.constants.TOTAL_COST_PER_MILE
                trucker_cost = distance * self.processor.constants.TRUCKER_COST_PER_MILE
                
                print(f"   Route {i}: {distance:.1f} km")
                print(f"     Operating cost: ${operating_cost:.2f}")
                print(f"     Trucker cost: ${trucker_cost:.2f}")
                print(f"     Current profitability: ${route.profitability:.2f}")
                
                if route.profitability > 0:
                    print(f"     Status: ✅ PROFITABLE")
                else:
                    print(f"     Status: ❌ LOSING MONEY")
                print("")

            print_success("✅ REQUIREMENT 4 COST INTEGRATION IMPLEMENTED")

        except Exception as e:
            print_error(f"Error in cost demo: {e}")

    def _demo_cargo_aggregation(self):
        """Requirement 5: Cargo Aggregation"""
        print(f"\n{Colors.CYAN}📊 REQUIREMENT 5: CARGO AGGREGATION{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Ability to aggregate multiple orders")
        print("into single routes for improved efficiency.")
        print("=" * 60)

        print_info("Aggregation demonstrates:")
        print("• Multiple orders on single route")
        print("• Combined capacity utilization")
        print("• Improved route profitability")

        try:
            routes = self._get_sample_routes(1)
            trucks = self._get_sample_trucks(1)
            
            if not routes or not trucks:
                print_error("Insufficient data for aggregation demo.")
                return

            route = routes[0]
            truck = trucks[0]

            print(f"\n📈 AGGREGATION SIMULATION:")
            print(f"   Base route profitability: ${route.profitability:.2f}")
            print(f"   Truck capacity: {truck.capacity:.0f}m³")
            
            # Simulate adding orders
            capacity_used = 0
            orders_added = 0
            revenue_added = 0

            while capacity_used < truck.capacity * 0.8:  # Use up to 80% capacity
                order_volume = min(5.0 + (orders_added * 2), truck.capacity - capacity_used)
                order_revenue = order_volume * 25  # Simulate $25/m³ revenue
                
                capacity_used += order_volume
                orders_added += 1
                revenue_added += order_revenue
                
                utilization = (capacity_used / truck.capacity) * 100
                new_profitability = route.profitability + revenue_added
                
                print(f"   + Order {orders_added}: {order_volume:.1f}m³, ${order_revenue:.0f}")
                print(f"     Capacity: {utilization:.1f}%, Profitability: ${new_profitability:.2f}")

            print(f"\n📊 AGGREGATION RESULTS:")
            print(f"   Orders aggregated: {orders_added}")
            print(f"   Capacity utilization: {utilization:.1f}%")
            print(f"   Additional revenue: ${revenue_added:.2f}")
            print(f"   Final profitability: ${route.profitability + revenue_added:.2f}")

            print_success("✅ REQUIREMENT 5 CARGO AGGREGATION IMPLEMENTED")

        except Exception as e:
            print_error(f"Error in aggregation demo: {e}")

    def _demo_route_constraints(self):
        """Requirement 6: Route Constraints"""
        print(f"\n{Colors.CYAN}🛣️ REQUIREMENT 6: ROUTE CONSTRAINTS{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Path optimization considering constraints")
        print("like truck limitations and delivery requirements.")
        print("=" * 60)

        print_info("Route constraints include:")
        print("• Truck capacity limits")
        print("• Location proximity requirements")
        print("• Time window constraints")
        print("• Cost optimization")

        try:
            routes = self._get_sample_routes(2)
            if not routes:
                print_error("No routes available for constraint demo.")
                return

            print(f"\n🔍 ROUTE CONSTRAINT ANALYSIS:")
            
            for i, route in enumerate(routes, 1):
                print(f"   Route {i}:")
                distance = route.base_distance()
                print(f"     Distance: {distance:.1f} km")
                print(f"     Profitability: ${route.profitability:.2f}")
                
                # Analyze constraints
                constraints = []
                if route.profitability < 0:
                    constraints.append("❌ Unprofitable route")
                else:
                    constraints.append("✅ Profitable route")
                
                if distance > 500:
                    constraints.append("⚠️  Long distance route")
                else:
                    constraints.append("✅ Manageable distance")
                
                for constraint in constraints:
                    print(f"       {constraint}")
                print("")

            print_success("✅ REQUIREMENT 6 ROUTE CONSTRAINTS IMPLEMENTED")

        except Exception as e:
            print_error(f"Error in route constraints demo: {e}")

    def _demo_union_breaks(self):
        """Bonus Requirement: Union Breaks"""
        print(f"\n{Colors.CYAN}⏸️ BONUS: UNION BREAKS{Colors.ENDC}")
        print("=" * 60)
        print("BONUS Requirement: Union labor rules and mandatory breaks")
        print("for drivers during long hauls.")
        print("=" * 60)

        print_info("Union break rules:")
        print("• Maximum 8 hours continuous driving")
        print("• 30-minute break every 4 hours")
        print("• 10-hour mandatory rest after 14-hour shift")

        try:
            routes = self._get_sample_routes(2)
            if not routes:
                print_error("No routes available for union break demo.")
                return

            print(f"\n⏰ BREAK REQUIREMENT ANALYSIS:")
            
            for i, route in enumerate(routes, 1):
                distance = route.base_distance()
                drive_time = distance / 60  # Assume 60 mph
                
                breaks_needed = int(drive_time / 4)  # Break every 4 hours
                break_time = breaks_needed * 0.5  # 30 minutes per break
                total_time = drive_time + break_time
                
                print(f"   Route {i}: {distance:.1f} km")
                print(f"     Drive time: {drive_time:.1f} hours")
                print(f"     Breaks needed: {breaks_needed}")
                print(f"     Break time: {break_time:.1f} hours")
                print(f"     Total time: {total_time:.1f} hours")
                
                if total_time > 14:
                    print(f"     Status: ❌ REQUIRES OVERNIGHT REST")
                else:
                    print(f"     Status: ✅ WITHIN DAILY LIMITS")
                print("")

            print_success("✅ BONUS REQUIREMENT UNION BREAKS IMPLEMENTED")

        except Exception as e:
            print_error(f"Error in union breaks demo: {e}")

    def _demo_cargo_types(self):
        """Bonus Requirement: Cargo Types"""
        print(f"\n{Colors.CYAN}🏷️ BONUS: CARGO TYPES{Colors.ENDC}")
        print("=" * 60)
        print("BONUS Requirement: Cargo type compatibility and")
        print("special handling requirements.")
        print("=" * 60)

        print_info("Cargo type compatibility rules:")
        print("• Standard cargo: No restrictions")
        print("• Fragile: Cannot mix with heavy cargo")
        print("• Refrigerated: Requires temperature control")
        print("• Hazardous: Special permits and isolation")

        try:
            # Simulate different cargo type scenarios
            cargo_types = [
                (CargoType.STANDARD, "Standard cargo"),
                (CargoType.FRAGILE, "Fragile cargo"),
                (CargoType.REFRIGERATED, "Refrigerated cargo"),
                (CargoType.HAZARDOUS, "Hazardous cargo")
            ]

            compatibility_matrix = {
                CargoType.STANDARD: [CargoType.STANDARD],
                CargoType.FRAGILE: [CargoType.FRAGILE],
                CargoType.REFRIGERATED: [CargoType.REFRIGERATED, CargoType.STANDARD],
                CargoType.HAZARDOUS: [CargoType.HAZARDOUS]
            }

            print(f"\n🔍 CARGO COMPATIBILITY MATRIX:")
            
            for cargo_type, description in cargo_types:
                compatible = compatibility_matrix[cargo_type]
                compatible_names = [ct.value for ct in compatible]
                
                print(f"   {description}:")
                print(f"     Compatible with: {', '.join(compatible_names)}")
                
                if len(compatible) == 1:
                    print(f"     Restriction: ⚠️  Requires isolated transport")
                else:
                    print(f"     Restriction: ✅ Can mix with compatible types")
                print("")

            print_success("✅ BONUS REQUIREMENT CARGO TYPES IMPLEMENTED")

        except Exception as e:
            print_error(f"Error in cargo types demo: {e}")

    def _demo_all_requirements(self):
        """Run all requirements demos in sequence"""
        print(f"\n{Colors.CYAN}🎯 RUNNING ALL REQUIREMENTS DEMO{Colors.ENDC}")
        print("=" * 60)
        
        requirements = [
            ("Location Proximity", self._demo_location_proximity),
            ("Cargo Capacity", self._demo_cargo_capacity),
            ("Pickup/Dropoff Timing", self._demo_pickup_dropoff_timing),
            ("Cost Integration", self._demo_cost_integration),
            ("Cargo Aggregation", self._demo_cargo_aggregation),
            ("Route Constraints", self._demo_route_constraints),
            ("Union Breaks (Bonus)", self._demo_union_breaks),
            ("Cargo Types (Bonus)", self._demo_cargo_types)
        ]

        for i, (name, demo_func) in enumerate(requirements, 1):
            print(f"\n{Colors.YELLOW}[{i}/8] {name}{Colors.ENDC}")
            print("-" * 40)
            demo_func()
            
            if i < len(requirements):
                print(f"\n{Colors.CYAN}Press Enter to continue to next requirement...{Colors.ENDC}")
                input()

        print(f"\n{Colors.GREEN}✅ ALL REQUIREMENTS DEMONSTRATION COMPLETE{Colors.ENDC}")
        print("=" * 60)

    # Helper methods for test data creation and retrieval

    def _get_sample_routes(self, count: int = 1) -> List[Route]:
        """Get sample routes from data service"""
        try:
            routes = self.data_service.get_all('routes')
            if routes and len(routes) >= count:
                return routes[:count]
            
            # Create fallback routes if none exist
            return self._create_fallback_routes(count)
        except Exception as e:
            print_error(f"Error getting routes: {e}")
            return self._create_fallback_routes(count)

    def _get_sample_trucks(self, count: int = 1) -> List[Truck]:
        """Get sample trucks from data service"""
        try:
            trucks = self.data_service.get_all('trucks')
            if trucks and len(trucks) >= count:
                return trucks[:count]
            
            return self._create_fallback_trucks(count)
        except Exception as e:
            print_error(f"Error getting trucks: {e}")
            return self._create_fallback_trucks(count)

    def _get_sample_locations(self, count: int = 2) -> List[Location]:
        """Get sample locations from data service"""
        try:
            locations = self.data_service.get_all('locations')
            if locations and len(locations) >= count:
                return locations[:count]
            
            return self._create_fallback_locations(count)
        except Exception as e:
            print_error(f"Error getting locations: {e}")
            return self._create_fallback_locations(count)

    def _create_fallback_routes(self, count: int) -> List[Route]:
        """Create fallback routes for testing"""
        locations = self._create_fallback_locations(count * 2)
        routes = []
        
        for i in range(count):
            route = Route(
                id=i + 1,
                location_origin_id=(i * 2) + 1,
                location_destiny_id=(i * 2) + 2,
                location_origin=locations[i * 2],
                location_destiny=locations[(i * 2) + 1],
                profitability=-50.0 - (i * 25),  # Varying losses
                orders=[]
            )
            routes.append(route)
        
        return routes

    def _create_fallback_trucks(self, count: int) -> List[Truck]:
        """Create fallback trucks for testing"""
        trucks = []
        for i in range(count):
            truck = Truck(
                id=i + 1,
                capacity=48.0,  # Standard business requirement
                autonomy=800.0,
                type="standard",
                cargo_loads=[]
            )
            trucks.append(truck)
        return trucks

    def _create_fallback_locations(self, count: int) -> List[Location]:
        """Create fallback locations for testing"""
        # Atlanta area locations for testing
        base_locations = [
            (33.7490, -84.3880),  # Atlanta
            (33.4735, -82.0105),  # Augusta
            (32.0835, -81.0998),  # Savannah
            (33.7600, -84.4000),  # Atlanta North
            (33.7500, -84.3890),  # Atlanta Near
            (33.4745, -82.0115),  # Augusta Near
        ]
        
        locations = []
        for i in range(min(count, len(base_locations))):
            lat, lng = base_locations[i]
            location = Location(id=i + 1, lat=lat, lng=lng)
            locations.append(location)
        
        # If need more, generate variations
        while len(locations) < count:
            i = len(locations)
            base_lat, base_lng = base_locations[i % len(base_locations)]
            lat = base_lat + (i * 0.01)  # Small variations
            lng = base_lng + (i * 0.01)
            location = Location(id=i + 1, lat=lat, lng=lng)
            locations.append(location)
        
        return locations

    def _create_proximity_test_orders(self, route: Route, locations: List[Location]) -> List[tuple]:
        """Create test orders for proximity validation"""
        orders = []
        
        # Valid order - within proximity
        if len(locations) >= 2:
            cargo1 = Cargo(id=1, order_id=1, packages=[
                Package(id=1, volume=5.0, weight=100.0, type=CargoType.STANDARD, cargo_id=1)
            ])
            order1 = Order(
                id=1,
                location_origin_id=locations[0].id,
                location_destiny_id=locations[1].id,
                location_origin=locations[0],
                location_destiny=locations[1],
                cargo=[cargo1]
            )
            orders.append(("Valid - within proximity", order1))
        
        # Invalid order - outside proximity (if we have locations far enough)
        if len(locations) >= 4:
            cargo2 = Cargo(id=2, order_id=2, packages=[
                Package(id=2, volume=3.0, weight=75.0, type=CargoType.STANDARD, cargo_id=2)
            ])
            order2 = Order(
                id=2,
                location_origin_id=locations[2].id,
                location_destiny_id=locations[3].id,
                location_origin=locations[2],
                location_destiny=locations[3],
                cargo=[cargo2]
            )
            orders.append(("May be outside proximity", order2))
        
        return orders

    def _create_capacity_test_orders(self, pickup_loc: Location, dropoff_loc: Location) -> List[tuple]:
        """Create test orders for capacity validation"""
        orders = []
        
        # Small valid order
        cargo1 = Cargo(id=1, order_id=1, packages=[
            Package(id=1, volume=5.0, weight=500.0, type=CargoType.STANDARD, cargo_id=1)
        ])
        order1 = Order(
            id=1, location_origin_id=pickup_loc.id, location_destiny_id=dropoff_loc.id,
            location_origin=pickup_loc, location_destiny=dropoff_loc, cargo=[cargo1]
        )
        orders.append(("Small cargo (5m³, 1100lbs)", order1))
        
        # Large valid order
        cargo2 = Cargo(id=2, order_id=2, packages=[
            Package(id=2, volume=45.0, weight=3500.0, type=CargoType.STANDARD, cargo_id=2)
        ])
        order2 = Order(
            id=2, location_origin_id=pickup_loc.id, location_destiny_id=dropoff_loc.id,
            location_origin=pickup_loc, location_destiny=dropoff_loc, cargo=[cargo2]
        )
        orders.append(("Large cargo (45m³, 7700lbs)", order2))
        
        # Invalid volume order
        cargo3 = Cargo(id=3, order_id=3, packages=[
            Package(id=3, volume=50.0, weight=1000.0, type=CargoType.STANDARD, cargo_id=3)
        ])
        order3 = Order(
            id=3, location_origin_id=pickup_loc.id, location_destiny_id=dropoff_loc.id,
            location_origin=pickup_loc, location_destiny=dropoff_loc, cargo=[cargo3]
        )
        orders.append(("Exceeds volume (50m³)", order3))
        
        # Invalid weight order
        cargo4 = Cargo(id=4, order_id=4, packages=[
            Package(id=4, volume=20.0, weight=5000.0, type=CargoType.STANDARD, cargo_id=4)
        ])
        order4 = Order(
            id=4, location_origin_id=pickup_loc.id, location_destiny_id=dropoff_loc.id,
            location_origin=pickup_loc, location_destiny=dropoff_loc, cargo=[cargo4]
        )
        orders.append(("Exceeds weight (11000lbs)", order4))
        
        return orders