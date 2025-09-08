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
    print_error, print_warning, print_info, format_table_data, Colors
)
from crud_operations import CRUDOperations


class RequirementFunctions:
    """Handles all 8 business requirement demonstrations with CLI integration"""

    def __init__(self, data_service):
        self.data_service = data_service
        self.processor = OrderProcessor()
        self.crud_ops = CRUDOperations(data_service)
        self.running = True
        self._data_sources = {}  # Track whether data came from DB or fallback

    def _print_data_info_box(self, title: str, items: List[tuple]):
        """Print a formatted data information box"""
        print(f"\n{Colors.WARNING}┌─ {title} " + "─" * (58 - len(title)) + f"┐{Colors.ENDC}")
        for key, value in items:
            if len(str(value)) > 45:
                print(f"{Colors.WARNING}│{Colors.ENDC} {key:<15}: {str(value)[:45]}...")
            else:
                print(f"{Colors.WARNING}│{Colors.ENDC} {key:<15}: {value}")
        print(f"{Colors.WARNING}└" + "─" * 60 + f"┘{Colors.ENDC}")

    def _format_table_data_limited(self, data: List[dict], headers: List[str], limit: int = 25) -> None:
        """Format and print tabular data with row limit and total count"""
        from ui_components import format_table_data, print_info, Colors
        
        if not data:
            print_info("No data found.")
            return
        
        total_count = len(data)
        display_data = data[:limit]
        
        # Use the existing format_table_data function
        format_table_data(display_data, headers)
        
        # Show total count info
        if total_count > limit:
            print(f"\n{Colors.CYAN}📊 Showing {len(display_data)} of {total_count} total rows{Colors.ENDC}")
        else:
            print(f"\n{Colors.CYAN}📊 Total: {total_count} rows{Colors.ENDC}")

    def _display_route_info(self, route: Route, data_source: str = "Database"):
        """Display detailed route information"""
        items = [
            ("Source", data_source),
            ("Route ID", route.id),
            ("Origin ID", route.location_origin_id),
            ("Origin Coords", f"{route.location_origin.lat:.6f}, {route.location_origin.lng:.6f}"),
            ("Destiny ID", route.location_destiny_id),  
            ("Destiny Coords", f"{route.location_destiny.lat:.6f}, {route.location_destiny.lng:.6f}"),
            ("Distance", f"{route.base_distance():.2f} km"),
            ("Profitability", f"${route.profitability:.2f}/day"),
            ("Status", "✅ Profitable" if route.profitability >= 0 else "❌ Losing Money")
        ]
        self._print_data_info_box("📍 ROUTE DATA", items)

    def _display_truck_info(self, truck: Truck, data_source: str = "Database"):
        """Display detailed truck information"""
        items = [
            ("Source", data_source),
            ("Truck ID", truck.id),
            ("Type", truck.type.title()),
            ("Capacity", f"{truck.capacity:.1f} m³"),
            ("Weight Limit", f"{self.processor.constants.MAX_WEIGHT_LBS:.0f} lbs"),
            ("Autonomy", f"{truck.autonomy:.0f} km"),
            ("Current Load", f"{len(truck.cargo_loads)} items"),
            ("Available Space", f"{truck.capacity:.1f} m³ (empty)")
        ]
        self._print_data_info_box("🚛 TRUCK DATA", items)

    def _display_location_info(self, locations: List[Location], data_source: str = "Database"):
        """Display detailed location information"""
        items = [("Source", data_source)]
        for i, loc in enumerate(locations[:4], 1):  # Show up to 4 locations
            items.append((f"Location {i} ID", loc.id))
            items.append((f"Location {i} Coords", f"{loc.lat:.6f}, {loc.lng:.6f}"))
        if len(locations) > 4:
            items.append(("Additional Locs", f"+{len(locations) - 4} more"))
        self._print_data_info_box("📍 LOCATION DATA", items)

    def _display_order_info(self, order: Order):
        """Display detailed order information"""
        total_volume = order.total_volume()
        total_weight = order.total_weight()
        total_packages = sum(len(cargo.packages) for cargo in order.cargo)
        
        items = [
            ("Order ID", order.id),
            ("Pickup Loc ID", order.location_origin_id),
            ("Pickup Coords", f"{order.location_origin.lat:.6f}, {order.location_origin.lng:.6f}"),
            ("Dropoff Loc ID", order.location_destiny_id),
            ("Dropoff Coords", f"{order.location_destiny.lat:.6f}, {order.location_destiny.lng:.6f}"),
            ("Total Volume", f"{total_volume:.2f} m³"),
            ("Total Weight", f"{total_weight:.1f} kg ({total_weight * 2.20462:.0f} lbs)"),
            ("Cargo Loads", len(order.cargo)),
            ("Total Packages", total_packages)
        ]
        self._print_data_info_box("📦 ORDER DATA", items)

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

        # Ask user for data mode
        print(f"\n{Colors.WARNING}📋 DATA SELECTION MODE:{Colors.ENDC}")
        print("  1. 🤖 Auto-select data (current behavior)")
        print("  2. 🎯 Select specific Route, Truck & Locations")
        print("  0. ↩️  Return to Requirements Menu")
        
        mode_choice = get_input("Select mode")
        
        if mode_choice == "0":
            return
        elif mode_choice == "2":
            # User selection mode
            selected_data = self._proximity_user_selection()
            if not selected_data:
                return
            route, truck, locations = selected_data
            data_mode = "User Selected"
        else:
            # Auto-select mode (original behavior)
            try:
                routes = self._get_sample_routes(1)
                trucks = self._get_sample_trucks(1)
                locations = self._get_sample_locations(6)

                if not routes or not trucks or len(locations) < 4:
                    print_error("Insufficient test data available. Need routes, trucks, and locations.")
                    return

                route = routes[0]
                truck = trucks[0]
                data_mode = "Auto Selected"
            except Exception as e:
                print_error(f"Error getting auto-selected data: {e}")
                return

        try:
            # Display data information boxes
            route_source = self._data_sources.get('routes', 'Fallback Data') if data_mode == "Auto Selected" else data_mode
            truck_source = self._data_sources.get('trucks', 'Fallback Data') if data_mode == "Auto Selected" else data_mode  
            location_source = self._data_sources.get('locations', 'Fallback Data') if data_mode == "Auto Selected" else data_mode
            
            self._display_route_info(route, route_source)
            self._display_truck_info(truck, truck_source)
            self._display_location_info(locations, location_source)

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

            # Determine overall result based on success rate
            if invalid_count == 0 and valid_count > 0:
                # Perfect score - all tests passed
                print_success("✅ REQUIREMENT 1: ALL TESTS PASSED")
            elif valid_count > 0 and invalid_count > 0:
                # Mixed results - demonstration successful but not all tests passed
                print_warning("⚠️ REQUIREMENT 1: PARTIAL SUCCESS - Demonstrates both pass/fail cases")
            elif valid_count == 0 and invalid_count > 0:
                # All tests failed
                print_error("❌ REQUIREMENT 1: ALL TESTS FAILED")
            else:
                # No tests or unclear result
                print_error("⚠️ REQUIREMENT 1: NEEDS VERIFICATION")

        except Exception as e:
            print_error(f"Error in proximity demo: {e}")

    def _proximity_user_selection(self):
        """Allow user to select specific Route, Truck, and Locations for proximity testing"""
        try:
            print(f"\n{Colors.CYAN}🎯 PROXIMITY TEST DATA SELECTION{Colors.ENDC}")
            print("=" * 50)
            
            # Step 1: Select Route
            print(f"\n📍 STEP 1: SELECT ROUTE")
            print("-" * 25)
            
            # List available routes using CRUD
            routes_data = self.data_service.get_all('routes')
            if not routes_data:
                print_error("No routes available in database.")
                return None
            
            print(f"Available Routes:")
            self._format_table_data_limited(routes_data, ['id', 'location_origin_id', 'location_destiny_id', 'profitability'])
            print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
            
            while True:
                route_id_input = get_input("Select Route ID (or 'back'/'cancel')")
                if route_id_input.lower() in ['cancel', 'back']:
                    return None
                try:
                    route_id = int(route_id_input)
                    # Try alternative approach - get all routes and find the one we want
                    routes_data = self.data_service.get_all('routes')
                    route_dict = next((r for r in routes_data if r.get('id') == route_id), None)
                    if route_dict:
                        route = self._dict_to_route(route_dict)
                        if route:
                            break
                        else:
                            print_error("Failed to process route data. Let me try a simpler approach.")
                            # Create a simple route object with available data
                            route = self._create_simple_route_from_dict(route_dict)
                            if route:
                                break
                    else:
                        print_error(f"Route ID {route_id} not found.")
                except ValueError:
                    print_error("Please enter a valid Route ID number.")
            
            print_success(f"✅ Selected Route ID: {route.id}")
            
            # Step 2: Select Truck  
            print(f"\n🚛 STEP 2: SELECT TRUCK")
            print("-" * 25)
            
            trucks_data = self.data_service.get_all('trucks')
            if not trucks_data:
                print_error("No trucks available in database.")
                return None
            
            print(f"Available Trucks:")
            self._format_table_data_limited(trucks_data, ['id', 'type', 'capacity', 'autonomy'])
            print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
            
            while True:
                truck_id_input = get_input("Select Truck ID (or 'back'/'cancel')")
                if truck_id_input.lower() in ['cancel', 'back']:
                    return None
                try:
                    truck_id = int(truck_id_input)
                    # Use alternative approach - get all trucks and find the one we want
                    trucks_data = self.data_service.get_all('trucks')
                    truck_dict = next((t for t in trucks_data if t.get('id') == truck_id), None)
                    if truck_dict:
                        truck = self._dict_to_truck(truck_dict)
                        if truck:
                            break
                        else:
                            print_error("Failed to process truck data.")
                    else:
                        print_error(f"Truck ID {truck_id} not found.")
                except ValueError:
                    print_error("Please enter a valid Truck ID number.")
            
            print_success(f"✅ Selected Truck ID: {truck.id}")
            
            # Step 3: Select Locations for test orders
            print(f"\n📍 STEP 3: SELECT LOCATIONS FOR TEST ORDERS")
            print("-" * 45)
            
            locations_data = self.data_service.get_all('locations')
            if not locations_data or len(locations_data) < 4:
                print_error("Need at least 4 locations available in database.")
                return None
            
            locations = []
            location_prompts = [
                "Test Order 1 - Pickup Location ID",
                "Test Order 1 - Dropoff Location ID", 
                "Test Order 2 - Pickup Location ID",
                "Test Order 2 - Dropoff Location ID"
            ]
            
            for prompt in location_prompts:
                # Show available locations for each selection
                print(f"\n📍 {prompt}")
                print("-" * 50)
                print(f"Available Locations:")
                self._format_table_data_limited(locations_data, ['id', 'lat', 'lng', 'marked'])
                print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
                
                while True:
                    loc_id_input = get_input(f"{prompt} (or 'back'/'cancel')")
                    if loc_id_input.lower() in ['cancel', 'back']:
                        return None
                    try:
                        loc_id = int(loc_id_input)
                        # Use alternative approach - get all locations and find the one we want
                        locations_data = self.data_service.get_all('locations')
                        loc_dict = next((l for l in locations_data if l.get('id') == loc_id), None)
                        if loc_dict:
                            location = self._dict_to_location(loc_dict)
                            if location:
                                locations.append(location)
                                print_success(f"✅ Selected Location ID: {location.id} ({location.lat:.4f}, {location.lng:.4f})")
                                break
                            else:
                                print_error("Failed to process location data.")
                        else:
                            print_error(f"Location ID {loc_id} not found.")
                    except ValueError:
                        print_error("Please enter a valid Location ID number.")
            
            print(f"\n{Colors.GREEN}✅ SELECTION COMPLETE!{Colors.ENDC}")
            print(f"Route: {route.id}, Truck: {truck.id}, Locations: {[loc.id for loc in locations]}")
            
            return (route, truck, locations)
            
        except Exception as e:
            print_error(f"Error in user selection: {e}")
            # Add debug info for CRUD issues
            if "has no attribute" in str(e):
                print_error("CRUD Methods Debug:")
                print(f"DataService type: {type(self.data_service)}")
                print(f"Available methods: {[m for m in dir(self.data_service) if not m.startswith('_')]}")
                print(f"Mode: {getattr(self.data_service, 'mode', 'Unknown')}")
            return None

    def _cargo_capacity_user_selection(self):
        """Allow user to select truck and packages for cargo capacity testing"""
        try:
            print(f"\n{Colors.CYAN}🎯 CARGO CAPACITY TEST DATA SELECTION{Colors.ENDC}")
            print("=" * 50)
            
            # Step 1: Select Truck
            print(f"\n🚛 STEP 1: SELECT TRUCK")
            print("-" * 25)
            
            trucks_data = self.data_service.get_all('trucks')
            if not trucks_data:
                print_error("No trucks available in database.")
                return None
            
            print(f"Available Trucks:")
            self._format_table_data_limited(trucks_data, ['id', 'type', 'capacity', 'autonomy'])
            print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
            
            while True:
                truck_id_input = get_input("Select Truck ID (or 'back'/'cancel')")
                if truck_id_input.lower() in ['cancel', 'back']:
                    return None
                try:
                    truck_id = int(truck_id_input)
                    truck_dict = next((t for t in trucks_data if t.get('id') == truck_id), None)
                    if truck_dict:
                        truck = self._dict_to_truck(truck_dict)
                        if truck:
                            break
                        else:
                            print_error("Failed to process truck data.")
                    else:
                        print_error(f"Truck ID {truck_id} not found.")
                except ValueError:
                    print_error("Please enter a valid Truck ID number.")
            
            print_success(f"✅ Selected Truck ID: {truck.id} (Capacity: {truck.capacity}m³)")
            
            # Step 2: Select Multiple Packages
            print(f"\n📦 STEP 2: SELECT PACKAGES TO TEST")
            print("-" * 35)
            
            packages_data = self.data_service.get_all('packages')
            if not packages_data:
                print_error("No packages available in database.")
                return None
                
            print(f"Available Packages:")
            self._format_table_data_limited(packages_data, ['id', 'volume', 'weight', 'type'])
            print(f"\n💡 Select multiple packages by entering IDs separated by commas (e.g., 1,2,3)")
            print(f"💡 Type 'back' or 'cancel' to return to previous menu")
            
            packages = []
            while True:
                package_ids_input = get_input("Enter Package IDs (comma-separated) (or 'back'/'cancel')")
                if package_ids_input.lower() in ['cancel', 'back']:
                    return None
                    
                try:
                    # Parse comma-separated IDs
                    package_ids = [int(x.strip()) for x in package_ids_input.split(',') if x.strip()]
                    if not package_ids:
                        print_error("Please enter at least one package ID.")
                        continue
                        
                    # Validate all IDs exist
                    found_packages = []
                    missing_ids = []
                    
                    for pkg_id in package_ids:
                        pkg_dict = next((p for p in packages_data if p.get('id') == pkg_id), None)
                        if pkg_dict:
                            package = self._dict_to_package(pkg_dict)
                            if package:
                                found_packages.append(package)
                            else:
                                missing_ids.append(pkg_id)
                        else:
                            missing_ids.append(pkg_id)
                    
                    if missing_ids:
                        print_error(f"Package IDs not found: {missing_ids}")
                        continue
                        
                    if found_packages:
                        packages = found_packages
                        break
                        
                except ValueError:
                    print_error("Please enter valid numeric package IDs separated by commas.")
            
            print_success(f"✅ Selected {len(packages)} packages")
            for pkg in packages:
                print(f"   • Package {pkg.id}: {pkg.volume}m³, {pkg.weight}kg, {pkg.type}")
                
            print(f"\n{Colors.GREEN}✅ SELECTION COMPLETE!{Colors.ENDC}")
            print(f"Truck: {truck.id}, Packages: {[pkg.id for pkg in packages]}")
            
            return {
                'truck': truck,
                'packages': packages
            }
            
        except Exception as e:
            print_error(f"Error in cargo capacity user selection: {e}")
            return None

    def _demo_cargo_capacity(self):
        """Requirement 2: Cargo Compartment Fitting"""
        print(f"\n{Colors.CYAN}📦 REQUIREMENT 2: CARGO COMPARTMENT FITTING{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Cargo must fit in truck compartment taking into account")
        print("original cargo and all cargo being included.")
        print("Limits: 48m³ volume, 9180 lbs weight")
        print("=" * 60)

        try:
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Use fallback test data (quick demo)")
            print("2. Select your own truck and packages (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                selected_data = self._cargo_capacity_user_selection()
                if not selected_data:
                    print_info("Cargo capacity test cancelled.")
                    return
                
                truck = selected_data['truck']
                selected_packages = selected_data['packages']
                data_source = "Database"
                
            else:
                # Fallback mode
                trucks = self._get_sample_trucks(1)
                if not trucks:
                    print_error("Insufficient test data available. Need trucks.")
                    return
                truck = trucks[0]
                
                # Get some packages from database as test data
                packages_data = self.data_service.get_all('packages')
                if not packages_data:
                    print_error("No packages available for testing.")
                    return
                    
                # Convert first few packages for testing
                selected_packages = []
                for pkg_dict in packages_data[:3]:  # Use first 3 packages
                    pkg = self._dict_to_package(pkg_dict)
                    if pkg:
                        selected_packages.append(pkg)
                        
                if not selected_packages:
                    print_error("Failed to load test packages.")
                    return
                    
                data_source = "Fallback Data"

            # Display selected data information boxes
            self._display_truck_info(truck, data_source)
            
            # Display packages information
            package_items = [
                ("Source", data_source),
                ("Package Count", len(selected_packages)),
                ("Package IDs", [pkg.id for pkg in selected_packages])
            ]
            
            for i, pkg in enumerate(selected_packages, 1):
                package_items.extend([
                    (f"Pkg {i} Volume", f"{pkg.volume}m³"),
                    (f"Pkg {i} Weight", f"{pkg.weight}kg"),
                    (f"Pkg {i} Type", str(pkg.type).split('.')[-1])
                ])
            
            self._print_data_info_box("📦 PACKAGE DATA", package_items)

            # Calculate totals
            total_volume = sum(pkg.volume for pkg in selected_packages)
            total_weight_kg = sum(pkg.weight for pkg in selected_packages)
            total_weight_lbs = total_weight_kg * 2.20462

            print(f"\n🔍 CAPACITY VALIDATION TEST:")
            print("")
            
            # Capacity limits
            max_volume = truck.capacity  # m³
            max_weight_lbs = self.processor.constants.MAX_WEIGHT_LBS  # 9180 lbs
            
            # Check volume constraint
            volume_valid = total_volume <= max_volume
            volume_percent = (total_volume / max_volume) * 100
            
            # Check weight constraint  
            weight_valid = total_weight_lbs <= max_weight_lbs
            weight_percent = (total_weight_lbs / max_weight_lbs) * 100
            
            # Overall result
            capacity_valid = volume_valid and weight_valid

            print(f"   📏 Volume Check:")
            print(f"      Total: {total_volume:.1f}m³ / {max_volume:.0f}m³ ({volume_percent:.1f}%)")
            if volume_valid:
                print(f"      ✅ PASSED - Volume within limits")
            else:
                print(f"      ❌ FAILED - Volume exceeds capacity")
            print("")
            
            print(f"   ⚖️  Weight Check:")
            print(f"      Total: {total_weight_lbs:.0f}lbs / {max_weight_lbs:.0f}lbs ({weight_percent:.1f}%)")
            if weight_valid:
                print(f"      ✅ PASSED - Weight within limits")
            else:
                print(f"      ❌ FAILED - Weight exceeds capacity")
            print("")

            print(f"📊 CAPACITY VALIDATION RESULT:")
            if capacity_valid:
                print_success(f"   ✅ OVERALL: PASSED - All packages fit in truck")
                print_success("✅ REQUIREMENT 2: ALL CONSTRAINTS SATISFIED")
            else:
                print_error(f"   ❌ OVERALL: FAILED - Capacity constraints violated")
                violations = []
                if not volume_valid:
                    violations.append("volume")
                if not weight_valid:
                    violations.append("weight")
                print_error(f"   Constraint violations: {', '.join(violations)}")
                print_warning("⚠️ REQUIREMENT 2: CONSTRAINTS VIOLATED - Try selecting fewer/lighter packages")

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
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Use fallback test data (quick demo)")
            print("2. Select your own route (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                route = self._timing_user_selection()
                if not route:
                    print_info("Timing test cancelled.")
                    return
                data_source = "Database"
            else:
                # Fallback mode
                routes = self._get_sample_routes(1)
                if not routes:
                    print_error("No routes available for timing demo.")
                    return
                route = routes[0]
                data_source = "Fallback Data"
            
            # Display route data information
            self._display_route_info(route, data_source)
            
            base_time = route.base_distance() / 60  # Assume 60 mph average

            print(f"\n📊 TIMING CALCULATIONS:")
            print(f"   Base route distance: {route.base_distance():.1f} km")
            print(f"   Base travel time: {base_time:.1f} hours")
            print(f"   Stop time per pickup/dropoff: {self.processor.constants.STOP_TIME_MINUTES} minutes")
            
            # Simulate timing scenarios
            scenarios = [
                ("No additional stops", 0),
                ("1 pickup/dropoff pair", 2),
                ("3 pickup/dropoff pairs", 6),
                ("5 pickup/dropoff pairs", 10)
            ]

            for scenario_name, stops in scenarios:
                stop_time_hours = (stops * self.processor.constants.STOP_TIME_MINUTES) / 60
                total_time = base_time + stop_time_hours
                
                print(f"   {scenario_name}:")
                print(f"     Stops: {stops}, Stop time: {stop_time_hours:.1f}h, Total: {total_time:.1f}h")

            print_success("✅ REQUIREMENT 3: TIMING CALCULATIONS DEMONSTRATED")

        except Exception as e:
            print_error(f"Error in timing demo: {e}")

    def _timing_user_selection(self):
        """Allow user to select route for timing testing"""
        try:
            print(f"\n{Colors.CYAN}🎯 TIMING TEST DATA SELECTION{Colors.ENDC}")
            print("=" * 50)
            
            # Step 1: Select Route
            print(f"\n🛣️ STEP 1: SELECT ROUTE")
            print("-" * 25)
            
            routes_data = self.data_service.get_all('routes')
            if not routes_data:
                print_error("No routes available in database.")
                return None
            
            print(f"Available Routes:")
            self._format_table_data_limited(routes_data, ['id', 'location_origin_id', 'location_destiny_id', 'profitability'])
            print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
            
            while True:
                route_id_input = get_input("Select Route ID (or 'back'/'cancel')")
                if route_id_input.lower() in ['cancel', 'back']:
                    return None
                try:
                    route_id = int(route_id_input)
                    route_dict = next((r for r in routes_data if r.get('id') == route_id), None)
                    if route_dict:
                        route = self._dict_to_route(route_dict)
                        if route:
                            break
                        else:
                            print_error("Failed to process route data.")
                            route = self._create_simple_route_from_dict(route_dict)
                            if route:
                                break
                    else:
                        print_error(f"Route ID {route_id} not found.")
                except ValueError:
                    print_error("Please enter a valid Route ID number.")
            
            print_success(f"✅ Selected Route ID: {route.id}")
            print(f"✅ Route distance: {route.base_distance():.1f} km")
            
            print(f"\n{Colors.GREEN}✅ SELECTION COMPLETE!{Colors.ENDC}")
            print(f"Route: {route.id}")
            
            return route
            
        except Exception as e:
            print_error(f"Error in timing user selection: {e}")
            return None

    def _cost_integration_user_selection(self):
        """Allow user to select multiple routes for cost analysis"""
        try:
            print(f"\n{Colors.CYAN}🎯 COST INTEGRATION TEST DATA SELECTION{Colors.ENDC}")
            print("=" * 50)
            
            # Step 1: Select Multiple Routes
            print(f"\n💰 STEP 1: SELECT ROUTES FOR COST ANALYSIS")
            print("-" * 45)
            
            routes_data = self.data_service.get_all('routes')
            if not routes_data:
                print_error("No routes available in database.")
                return None
            
            print(f"Available Routes:")
            self._format_table_data_limited(routes_data, ['id', 'location_origin_id', 'location_destiny_id', 'profitability'])
            print(f"\n💡 Select multiple routes by entering IDs separated by commas (e.g., 1,2,3)")
            print(f"💡 Type 'back' or 'cancel' to return to previous menu")
            
            routes = []
            while True:
                route_ids_input = get_input("Enter Route IDs (comma-separated) (or 'back'/'cancel')")
                if route_ids_input.lower() in ['cancel', 'back']:
                    return None
                    
                try:
                    # Parse comma-separated IDs
                    route_ids = [int(x.strip()) for x in route_ids_input.split(',') if x.strip()]
                    if not route_ids:
                        print_error("Please enter at least one route ID.")
                        continue
                        
                    if len(route_ids) < 2:
                        print_warning("Cost analysis works better with multiple routes. Consider selecting 2-5 routes.")
                        confirm = get_input("Continue with single route? (y/N): ")
                        if confirm.lower() != 'y':
                            continue
                        
                    # Validate all IDs exist and convert
                    found_routes = []
                    missing_ids = []
                    
                    for route_id in route_ids:
                        route_dict = next((r for r in routes_data if r.get('id') == route_id), None)
                        if route_dict:
                            route = self._dict_to_route(route_dict)
                            if not route:
                                route = self._create_simple_route_from_dict(route_dict)
                            if route:
                                found_routes.append(route)
                            else:
                                missing_ids.append(route_id)
                        else:
                            missing_ids.append(route_id)
                    
                    if missing_ids:
                        print_error(f"Route IDs not found: {missing_ids}")
                        continue
                        
                    if found_routes:
                        routes = found_routes
                        break
                        
                except ValueError:
                    print_error("Please enter valid numeric route IDs separated by commas.")
            
            print_success(f"✅ Selected {len(routes)} routes for cost analysis")
            for route in routes:
                print(f"   • Route {route.id}: {route.base_distance():.1f} km, ${route.profitability:.2f}")
                
            print(f"\n{Colors.GREEN}✅ SELECTION COMPLETE!{Colors.ENDC}")
            print(f"Routes: {[route.id for route in routes]}")
            
            return routes
            
        except Exception as e:
            print_error(f"Error in cost integration user selection: {e}")
            return None

    def _demo_cost_integration(self):
        """Requirement 4: Cost Integration"""
        print(f"\n{Colors.CYAN}💰 REQUIREMENT 4: COST INTEGRATION{Colors.ENDC}")
        print("=" * 60)
        print("Requirement: Profitability analysis with integrated costs")
        print("considering truck operating costs and revenue from orders.")
        print("=" * 60)

        try:
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Use fallback test data (quick demo)")
            print("2. Select your own routes (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                routes = self._cost_integration_user_selection()
                if not routes:
                    print_info("Cost integration test cancelled.")
                    return
                data_source = "Database"
            else:
                # Fallback mode - get first few routes from database
                routes_data = self.data_service.get_all('routes')
                if not routes_data:
                    print_error("No routes available for cost demo.")
                    return
                    
                # Convert first 3 routes for testing
                routes = []
                for route_dict in routes_data[:3]:
                    route = self._dict_to_route(route_dict)
                    if not route:
                        route = self._create_simple_route_from_dict(route_dict)
                    if route:
                        routes.append(route)
                        
                if not routes:
                    print_error("Failed to load test routes.")
                    return
                    
                data_source = "Fallback Data"

            # Display selected routes data information
            items = [("Source", data_source), ("Routes Selected", len(routes))]
            for i, route in enumerate(routes, 1):
                items.append((f"Route {i} ID", route.id))
                items.append((f"Route {i} Distance", f"{route.base_distance():.1f} km"))
                items.append((f"Route {i} Current Profit", f"${route.profitability:.2f}"))
            self._print_data_info_box("🛣️ SELECTED ROUTES DATA", items)

            # Display cost constants
            print(f"\n💼 COST ANALYSIS PARAMETERS:")
            print(f"   Total cost per mile: ${self.processor.constants.TOTAL_COST_PER_MILE:.3f}")
            print(f"   Trucker cost per mile: ${self.processor.constants.TRUCKER_COST_PER_MILE:.3f}")
            print("")

            # Analyze each route
            profitable_count = 0
            losing_count = 0
            total_distance = 0
            total_operating_cost = 0
            total_profit = 0

            print(f"🔍 INDIVIDUAL ROUTE ANALYSIS:")
            print("")

            for i, route in enumerate(routes, 1):
                distance_km = route.base_distance()
                distance_miles = distance_km * 0.621371  # Convert km to miles for cost calculation
                
                operating_cost = distance_miles * self.processor.constants.TOTAL_COST_PER_MILE
                trucker_cost = distance_miles * self.processor.constants.TRUCKER_COST_PER_MILE
                current_profit = route.profitability
                net_profit = current_profit - operating_cost
                
                # Accumulate totals
                total_distance += distance_km
                total_operating_cost += operating_cost
                total_profit += current_profit
                
                print(f"   Route {i} (ID: {route.id}):")
                print(f"     Distance: {distance_km:.1f} km ({distance_miles:.1f} miles)")
                print(f"     Operating cost: ${operating_cost:.2f}")
                print(f"     Trucker cost: ${trucker_cost:.2f}")  
                print(f"     Revenue: ${current_profit:.2f}")
                print(f"     Net profit: ${net_profit:.2f}")
                
                if net_profit > 0:
                    print(f"     Status: ✅ PROFITABLE (${net_profit:.2f})")
                    profitable_count += 1
                else:
                    print(f"     Status: ❌ LOSING MONEY (-${abs(net_profit):.2f})")
                    losing_count += 1
                print("")

            # Summary analysis
            total_net_profit = total_profit - total_operating_cost
            avg_profit_per_route = total_net_profit / len(routes)
            
            print(f"📊 COST INTEGRATION SUMMARY:")
            print(f"   Total routes analyzed: {len(routes)}")
            print(f"   Profitable routes: {profitable_count}")
            print(f"   Unprofitable routes: {losing_count}")
            print(f"   Total distance: {total_distance:.1f} km")
            print(f"   Total operating cost: ${total_operating_cost:.2f}")
            print(f"   Total revenue: ${total_profit:.2f}")
            print(f"   Total net profit: ${total_net_profit:.2f}")
            print(f"   Average profit per route: ${avg_profit_per_route:.2f}")

            # Determine overall result
            if losing_count == 0 and profitable_count > 0:
                print_success("✅ REQUIREMENT 4: ALL ROUTES PROFITABLE")
            elif profitable_count > 0 and losing_count > 0:
                print_warning("⚠️ REQUIREMENT 4: MIXED PROFITABILITY - Some routes losing money")
            elif profitable_count == 0 and losing_count > 0:
                print_error("❌ REQUIREMENT 4: ALL ROUTES UNPROFITABLE")
            else:
                print_error("⚠️ REQUIREMENT 4: NEEDS VERIFICATION")

        except Exception as e:
            print_error(f"Error in cost demo: {e}")

    def _cargo_aggregation_user_selection(self):
        """Allow user to select route, truck, and orders for cargo aggregation testing"""
        try:
            print(f"\n{Colors.CYAN}🎯 CARGO AGGREGATION TEST DATA SELECTION{Colors.ENDC}")
            print("=" * 55)
            
            # Step 1: Select Route
            print(f"\n🛣️ STEP 1: SELECT ROUTE FOR AGGREGATION")
            print("-" * 40)
            
            routes_data = self.data_service.get_all('routes')
            if not routes_data:
                print_error("No routes available in database.")
                return None
            
            print(f"Available Routes:")
            self._format_table_data_limited(routes_data, ['id', 'location_origin_id', 'location_destiny_id', 'profitability'])
            print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
            
            while True:
                route_id_input = get_input("Select Route ID (or 'back'/'cancel')")
                if route_id_input.lower() in ['cancel', 'back']:
                    return None
                try:
                    route_id = int(route_id_input)
                    route_dict = next((r for r in routes_data if r.get('id') == route_id), None)
                    if route_dict:
                        route = self._dict_to_route(route_dict)
                        if not route:
                            route = self._create_simple_route_from_dict(route_dict)
                        if route:
                            break
                    else:
                        print_error(f"Route ID {route_id} not found.")
                except ValueError:
                    print_error("Please enter a valid Route ID number.")
            
            print_success(f"✅ Selected Route ID: {route.id}")
            
            # Step 2: Select Truck
            print(f"\n🚛 STEP 2: SELECT TRUCK FOR CAPACITY VALIDATION")
            print("-" * 45)
            
            trucks_data = self.data_service.get_all('trucks')
            if not trucks_data:
                print_error("No trucks available in database.")
                return None
            
            print(f"Available Trucks:")
            self._format_table_data_limited(trucks_data, ['id', 'type', 'capacity', 'autonomy'])
            print(f"\n💡 Tip: Type 'back' or 'cancel' to return to previous menu")
            
            while True:
                truck_id_input = get_input("Select Truck ID (or 'back'/'cancel')")
                if truck_id_input.lower() in ['cancel', 'back']:
                    return None
                try:
                    truck_id = int(truck_id_input)
                    truck_dict = next((t for t in trucks_data if t.get('id') == truck_id), None)
                    if truck_dict:
                        truck = self._dict_to_truck(truck_dict)
                        if truck:
                            break
                    else:
                        print_error(f"Truck ID {truck_id} not found.")
                except ValueError:
                    print_error("Please enter a valid Truck ID number.")
            
            print_success(f"✅ Selected Truck ID: {truck.id} (Capacity: {truck.capacity}m³)")
            
            # Step 3: Select Multiple Orders for Aggregation
            print(f"\n📦 STEP 3: SELECT ORDERS TO AGGREGATE")
            print("-" * 35)
            
            orders_data = self.data_service.get_all('orders')
            if not orders_data:
                print_error("No orders available in database.")
                return None
            
            print(f"Available Orders:")
            self._format_table_data_limited(orders_data, ['id', 'location_origin_id', 'location_destiny_id', 'client_id'])
            print(f"\n💡 Select multiple orders by entering IDs separated by commas (e.g., 1,2,3)")
            print(f"💡 Type 'back' or 'cancel' to return to previous menu")
            
            orders = []
            while True:
                order_ids_input = get_input("Enter Order IDs (comma-separated) (or 'back'/'cancel')")
                if order_ids_input.lower() in ['cancel', 'back']:
                    return None
                    
                try:
                    # Parse comma-separated IDs
                    order_ids = [int(x.strip()) for x in order_ids_input.split(',') if x.strip()]
                    if not order_ids:
                        print_error("Please enter at least one order ID.")
                        continue
                        
                    if len(order_ids) < 2:
                        print_warning("Aggregation works better with multiple orders. Consider selecting 2-5 orders.")
                        confirm = get_input("Continue with single order? (y/N): ")
                        if confirm.lower() != 'y':
                            continue
                    
                    # Validate all IDs exist
                    found_orders = []
                    missing_ids = []
                    
                    for order_id in order_ids:
                        order_dict = next((o for o in orders_data if o.get('id') == order_id), None)
                        if order_dict:
                            # For simplicity, create basic order info
                            found_orders.append({
                                'id': order_dict.get('id'),
                                'origin_id': order_dict.get('location_origin_id'),
                                'destiny_id': order_dict.get('location_destiny_id'),
                                'client_id': order_dict.get('client_id')
                            })
                        else:
                            missing_ids.append(order_id)
                    
                    if missing_ids:
                        print_error(f"Order IDs not found: {missing_ids}")
                        continue
                        
                    if found_orders:
                        orders = found_orders
                        break
                        
                except ValueError:
                    print_error("Please enter valid numeric order IDs separated by commas.")
            
            print_success(f"✅ Selected {len(orders)} orders for aggregation")
            for order in orders:
                print(f"   • Order {order['id']}: Origin {order['origin_id']} → Destiny {order['destiny_id']}")
            
            print(f"\n{Colors.GREEN}✅ SELECTION COMPLETE!{Colors.ENDC}")
            print(f"Route: {route.id}, Truck: {truck.id}, Orders: {[o['id'] for o in orders]}")
            
            return {
                'route': route,
                'truck': truck,
                'orders': orders
            }
            
        except Exception as e:
            print_error(f"Error in cargo aggregation user selection: {e}")
            return None

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
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Use fallback test data (quick demo)")
            print("2. Select your own route, truck, and orders (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                selected_data = self._cargo_aggregation_user_selection()
                if not selected_data:
                    print_info("Cargo aggregation test cancelled.")
                    return
                
                route = selected_data['route']
                truck = selected_data['truck']
                orders = selected_data['orders']
                data_source = "Database"
                
            else:
                # Fallback mode - get sample data from database
                routes_data = self.data_service.get_all('routes')
                trucks_data = self.data_service.get_all('trucks')
                orders_data = self.data_service.get_all('orders')
                
                if not routes_data or not trucks_data or not orders_data:
                    print_error("Insufficient data for aggregation demo.")
                    return
                
                # Use first available route and truck
                route_dict = routes_data[0]
                truck_dict = trucks_data[0]
                
                route = self._dict_to_route(route_dict)
                if not route:
                    route = self._create_simple_route_from_dict(route_dict)
                truck = self._dict_to_truck(truck_dict)
                
                # Use first few orders
                orders = []
                for order_dict in orders_data[:3]:
                    orders.append({
                        'id': order_dict.get('id'),
                        'origin_id': order_dict.get('location_origin_id'),
                        'destiny_id': order_dict.get('location_destiny_id'),
                        'client_id': order_dict.get('client_id')
                    })
                    
                data_source = "Fallback Data"

            # Display selected data information boxes
            self._display_route_info(route, data_source)
            self._display_truck_info(truck, data_source)
            
            # Display orders information
            order_items = [
                ("Source", data_source),
                ("Orders Selected", len(orders)),
                ("Order IDs", [o['id'] for o in orders])
            ]
            
            for i, order in enumerate(orders, 1):
                order_items.extend([
                    (f"Order {i} ID", order['id']),
                    (f"Order {i} Route", f"{order['origin_id']} → {order['destiny_id']}")
                ])
            
            self._print_data_info_box("📦 ORDERS DATA", order_items)

            # Perform aggregation analysis
            print(f"\n🔍 CARGO AGGREGATION ANALYSIS:")
            print(f"   Base route profitability: ${route.profitability:.2f}")
            print(f"   Truck capacity: {truck.capacity:.0f}m³")
            print("")
            
            # Calculate aggregation potential
            base_profitability = route.profitability
            total_capacity_used = 0
            total_revenue_added = 0
            aggregated_count = 0
            
            # Simulate capacity usage for each order (simplified)
            for i, order in enumerate(orders, 1):
                # Simulate order volume (5-15 m³ per order)
                order_volume = 5.0 + (i * 2.5)  # Increasing volume per order
                order_revenue = order_volume * 20  # $20 per m³
                
                if total_capacity_used + order_volume <= truck.capacity * 0.9:  # 90% capacity limit
                    total_capacity_used += order_volume
                    total_revenue_added += order_revenue
                    aggregated_count += 1
                    
                    utilization = (total_capacity_used / truck.capacity) * 100
                    running_profit = base_profitability + total_revenue_added
                    
                    print(f"   + Order {order['id']}: {order_volume:.1f}m³, ${order_revenue:.0f} revenue")
                    print(f"     Capacity used: {utilization:.1f}%, Running profit: ${running_profit:.2f}")
                else:
                    print(f"   - Order {order['id']}: {order_volume:.1f}m³ - EXCEEDS CAPACITY")
                    break

            # Summary
            final_profitability = base_profitability + total_revenue_added
            capacity_utilization = (total_capacity_used / truck.capacity) * 100
            
            print(f"\n📊 AGGREGATION SUMMARY:")
            print(f"   Orders successfully aggregated: {aggregated_count} of {len(orders)}")
            print(f"   Total capacity utilization: {capacity_utilization:.1f}%")
            print(f"   Additional revenue generated: ${total_revenue_added:.2f}")
            print(f"   Original profitability: ${base_profitability:.2f}")
            print(f"   Final profitability: ${final_profitability:.2f}")
            print(f"   Profitability improvement: ${total_revenue_added:.2f}")

            # Determine result
            if aggregated_count == len(orders) and capacity_utilization > 50:
                print_success("✅ REQUIREMENT 5: ALL ORDERS AGGREGATED SUCCESSFULLY")
            elif aggregated_count > 0 and aggregated_count < len(orders):
                print_warning("⚠️ REQUIREMENT 5: PARTIAL AGGREGATION - Some orders exceed capacity")
            elif aggregated_count == 0:
                print_error("❌ REQUIREMENT 5: NO ORDERS COULD BE AGGREGATED")
            else:
                print_success("✅ REQUIREMENT 5: AGGREGATION DEMONSTRATED")

        except Exception as e:
            print_error(f"Error in aggregation demo: {e}")

    def _route_constraints_user_selection(self):
        """Allow user to select routes for constraint analysis"""
        try:
            print(f"\n{Colors.CYAN}🎯 ROUTE CONSTRAINTS TEST DATA SELECTION{Colors.ENDC}")
            print("=" * 55)
            
            # Step 1: Select Multiple Routes for Constraint Analysis
            print(f"\n🛣️ STEP 1: SELECT ROUTES FOR CONSTRAINT ANALYSIS")
            print("-" * 45)
            
            routes_data = self.data_service.get_all('routes')
            if not routes_data:
                print_error("No routes available in database.")
                return None
            
            print(f"Available Routes:")
            self._format_table_data_limited(routes_data, ['id', 'location_origin_id', 'location_destiny_id', 'profitability'])
            print(f"\n💡 Select multiple routes by entering IDs separated by commas (e.g., 1,2,3)")
            print(f"💡 Type 'back' or 'cancel' to return to previous menu")
            
            routes = []
            while True:
                route_ids_input = get_input("Enter Route IDs (comma-separated) (or 'back'/'cancel')")
                if route_ids_input.lower() in ['cancel', 'back']:
                    return None
                    
                try:
                    # Parse comma-separated IDs
                    route_ids = [int(x.strip()) for x in route_ids_input.split(',') if x.strip()]
                    if not route_ids:
                        print_error("Please enter at least one route ID.")
                        continue
                        
                    if len(route_ids) < 2:
                        print_warning("Constraint analysis works better with multiple routes. Consider selecting 2-5 routes.")
                        confirm = get_input("Continue with single route? (y/N): ")
                        if confirm.lower() != 'y':
                            continue
                    
                    # Validate all IDs exist and convert
                    found_routes = []
                    missing_ids = []
                    
                    for route_id in route_ids:
                        route_dict = next((r for r in routes_data if r.get('id') == route_id), None)
                        if route_dict:
                            route = self._dict_to_route(route_dict)
                            if not route:
                                route = self._create_simple_route_from_dict(route_dict)
                            if route:
                                found_routes.append(route)
                            else:
                                missing_ids.append(route_id)
                        else:
                            missing_ids.append(route_id)
                    
                    if missing_ids:
                        print_error(f"Route IDs not found: {missing_ids}")
                        continue
                        
                    if found_routes:
                        routes = found_routes
                        break
                        
                except ValueError:
                    print_error("Please enter valid numeric route IDs separated by commas.")
            
            print_success(f"✅ Selected {len(routes)} routes for constraint analysis")
            for route in routes:
                print(f"   • Route {route.id}: {route.base_distance():.1f} km, ${route.profitability:.2f}")
                
            print(f"\n{Colors.GREEN}✅ SELECTION COMPLETE!{Colors.ENDC}")
            print(f"Routes: {[route.id for route in routes]}")
            
            return routes
            
        except Exception as e:
            print_error(f"Error in route constraints user selection: {e}")
            return None

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
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Use fallback test data (quick demo)")
            print("2. Select your own routes (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                routes = self._route_constraints_user_selection()
                if not routes:
                    print_info("Route constraints test cancelled.")
                    return
                data_source = "Database"
            else:
                # Fallback mode - get first few routes from database
                routes_data = self.data_service.get_all('routes')
                if not routes_data:
                    print_error("No routes available for constraint demo.")
                    return
                    
                # Convert first 3 routes for testing
                routes = []
                for route_dict in routes_data[:3]:
                    route = self._dict_to_route(route_dict)
                    if not route:
                        route = self._create_simple_route_from_dict(route_dict)
                    if route:
                        routes.append(route)
                        
                if not routes:
                    print_error("Failed to load test routes.")
                    return
                    
                data_source = "Fallback Data"

            # Display selected routes data information
            items = [("Source", data_source), ("Routes Selected", len(routes))]
            for i, route in enumerate(routes, 1):
                items.append((f"Route {i} ID", route.id))
                items.append((f"Route {i} Distance", f"{route.base_distance():.1f} km"))
                items.append((f"Route {i} Profitability", f"${route.profitability:.2f}"))
            self._print_data_info_box("🔍 CONSTRAINT ANALYSIS DATA", items)

            # Perform constraint analysis
            print(f"\n🔍 ROUTE CONSTRAINT ANALYSIS:")
            
            passed_constraints = 0
            failed_constraints = 0
            total_routes = len(routes)
            
            # Constraint thresholds (business rules)
            MAX_DISTANCE_KM = 500.0
            MIN_PROFITABILITY = 0.0
            MAX_ROUTE_TIME_HOURS = self.processor.constants.MAX_ROUTE_HOURS  # 10 hours
            COST_PER_MILE = self.processor.constants.TOTAL_COST_PER_MILE
            
            print(f"   Constraint Thresholds:")
            print(f"     Maximum distance: {MAX_DISTANCE_KM} km")
            print(f"     Minimum profitability: ${MIN_PROFITABILITY}")
            print(f"     Maximum route time: {MAX_ROUTE_TIME_HOURS} hours")
            print("")
            
            for i, route in enumerate(routes, 1):
                distance_km = route.base_distance()
                distance_miles = distance_km * 0.621371
                profitability = route.profitability
                
                # Calculate estimated time (simplified)
                travel_time_hours = distance_km / 60  # Assume 60 km/h average
                operating_cost = distance_miles * COST_PER_MILE
                
                print(f"   Route {i} (ID: {route.id}):")
                print(f"     Distance: {distance_km:.1f} km ({distance_miles:.1f} miles)")
                print(f"     Estimated travel time: {travel_time_hours:.1f} hours")
                print(f"     Operating cost: ${operating_cost:.2f}")
                print(f"     Profitability: ${profitability:.2f}")
                
                # Analyze constraints
                route_passed = True
                constraints_status = []
                
                # Distance constraint
                if distance_km <= MAX_DISTANCE_KM:
                    constraints_status.append("✅ Distance within limit")
                else:
                    constraints_status.append("❌ Distance exceeds limit")
                    route_passed = False
                
                # Profitability constraint
                if profitability >= MIN_PROFITABILITY:
                    constraints_status.append("✅ Meets profitability requirement")
                else:
                    constraints_status.append("❌ Below profitability threshold")
                    route_passed = False
                
                # Time constraint
                if travel_time_hours <= MAX_ROUTE_TIME_HOURS:
                    constraints_status.append("✅ Within time limit")
                else:
                    constraints_status.append("⚠️ Exceeds recommended time")
                    # Note: Not failing the route for time, just warning
                
                # Cost efficiency (profitability vs cost)
                net_profit = profitability - operating_cost
                if net_profit > 0:
                    constraints_status.append("✅ Cost efficient")
                else:
                    constraints_status.append("❌ Not cost efficient")
                    route_passed = False
                
                for status in constraints_status:
                    print(f"       {status}")
                
                if route_passed:
                    print(f"     Overall: ✅ PASSES ALL CONSTRAINTS")
                    passed_constraints += 1
                else:
                    print(f"     Overall: ❌ FAILS CONSTRAINTS")
                    failed_constraints += 1
                    
                print("")

            # Summary analysis
            constraint_compliance_rate = (passed_constraints / total_routes) * 100
            
            print(f"📊 CONSTRAINT ANALYSIS SUMMARY:")
            print(f"   Total routes analyzed: {total_routes}")
            print(f"   Routes passing constraints: {passed_constraints}")
            print(f"   Routes failing constraints: {failed_constraints}")
            print(f"   Constraint compliance rate: {constraint_compliance_rate:.1f}%")

            # Determine overall result
            if failed_constraints == 0 and passed_constraints > 0:
                print_success("✅ REQUIREMENT 6: ALL ROUTES MEET CONSTRAINTS")
            elif passed_constraints > 0 and failed_constraints > 0:
                print_warning("⚠️ REQUIREMENT 6: MIXED CONSTRAINT COMPLIANCE")
            elif passed_constraints == 0 and failed_constraints > 0:
                print_error("❌ REQUIREMENT 6: NO ROUTES MEET CONSTRAINTS")
            else:
                print_error("⚠️ REQUIREMENT 6: NEEDS VERIFICATION")

        except Exception as e:
            print_error(f"Error in route constraints demo: {e}")

    def _union_breaks_user_selection(self) -> List[Route]:
        """Allow user to select routes for union break analysis"""
        try:
            routes_data = self.data_service.get_all('routes')
            if not routes_data:
                print_error("No routes found in database.")
                return None
            
            print(f"\n📋 Available Routes (showing first 25 of {len(routes_data)} total):")
            print("=" * 80)
            
            # Convert to Route objects and show limited list
            available_routes = []
            for route_dict in routes_data[:25]:
                route = self._dict_to_route(route_dict)
                if not route:
                    route = self._create_simple_route_from_dict(route_dict)
                if route:
                    available_routes.append(route)
                    distance = route.base_distance()
                    drive_time = distance / 60  # Assume 60 km/h average speed
                    print(f"  {route.id:3d}. Distance: {distance:6.1f}km | Drive Time: {drive_time:5.1f}h | Profit: ${route.profitability:8.2f}")
            
            if len(routes_data) > 25:
                print(f"  ... and {len(routes_data) - 25} more routes")
            
            print(f"\nTotal routes available: {len(routes_data)}")
            
            while True:
                route_ids_input = get_input("\nEnter route IDs for union break analysis (comma-separated, e.g., 1,2,3): ")
                if not route_ids_input.strip():
                    print_error("Route selection is required.")
                    continue
                
                try:
                    route_ids = [int(id_str.strip()) for id_str in route_ids_input.split(',')]
                    
                    # Find selected routes
                    selected_routes = []
                    for route_id in route_ids:
                        route_dict = next((r for r in routes_data if r['id'] == route_id), None)
                        if not route_dict:
                            print_error(f"Route ID {route_id} not found.")
                            break
                        
                        route = self._dict_to_route(route_dict)
                        if not route:
                            route = self._create_simple_route_from_dict(route_dict)
                        
                        if route:
                            selected_routes.append(route)
                    else:
                        # All routes found successfully
                        if selected_routes:
                            return selected_routes
                        else:
                            print_error("No valid routes could be created from selection.")
                            continue
                    
                except ValueError:
                    print_error("Please enter valid route IDs (numbers only, comma-separated).")
                    continue
                
        except Exception as e:
            print_error(f"Error in route selection: {e}")
            return None

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
        print("• Analysis based on 60 km/h average driving speed")

        try:
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Use fallback test data (quick demo)")
            print("2. Select your own routes (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                routes = self._union_breaks_user_selection()
                if not routes:
                    print_info("Union breaks analysis cancelled.")
                    return
                data_source = "Database"
            else:
                # Fallback mode
                routes = self._get_sample_routes(2)
                if not routes:
                    print_error("No routes available for union break demo.")
                    return
                data_source = "Fallback Data"

            # Display route data information
            items = [("Source", data_source), ("Routes for Analysis", len(routes))]
            for i, route in enumerate(routes, 1):
                items.append((f"Route {i} ID", route.id))
                items.append((f"Route {i} Distance", f"{route.base_distance():.1f} km"))
                drive_time = route.base_distance() / 60
                items.append((f"Route {i} Drive Time", f"{drive_time:.1f} hours"))
            self._print_data_info_box("⏸️ UNION BREAK ANALYSIS DATA", items)

            print(f"\n⏰ BREAK REQUIREMENT ANALYSIS:")
            
            all_compliant = True
            total_routes_analyzed = len(routes)
            compliant_routes = 0
            
            for i, route in enumerate(routes, 1):
                distance = route.base_distance()
                drive_time = distance / 60  # Assume 60 km/h average speed
                
                # Union break calculation
                breaks_needed = max(0, int(drive_time / 4))  # Break every 4 hours
                break_time = breaks_needed * 0.5  # 30 minutes per break
                total_time = drive_time + break_time
                
                print(f"   Route {i} (ID: {route.id}): {distance:.1f} km")
                print(f"     Base drive time: {drive_time:.1f} hours")
                print(f"     Breaks required: {breaks_needed} × 30min = {break_time:.1f}h")
                print(f"     Total time: {total_time:.1f} hours")
                
                # Union compliance check
                if total_time > 14:
                    print(f"     ❌ UNION VIOLATION - Exceeds 14-hour limit")
                    print(f"     📅 Requires overnight rest period")
                    all_compliant = False
                elif drive_time > 8:
                    print(f"     ❌ UNION VIOLATION - Exceeds 8-hour continuous driving")
                    all_compliant = False
                else:
                    print(f"     ✅ UNION COMPLIANT - Within daily limits")
                    compliant_routes += 1
                print("")

            # Overall summary
            print(f"📊 UNION BREAKS COMPLIANCE SUMMARY:")
            print(f"   • Total routes analyzed: {total_routes_analyzed}")
            print(f"   • Compliant routes: {compliant_routes}")
            print(f"   • Non-compliant routes: {total_routes_analyzed - compliant_routes}")
            print(f"   • Compliance rate: {(compliant_routes/total_routes_analyzed*100):.1f}%")
            print("")

            if all_compliant:
                print_success("✅ REQUIREMENT 7: ALL ROUTES UNION COMPLIANT")
            else:
                print_warning(f"⚠️ REQUIREMENT 7: {total_routes_analyzed - compliant_routes} ROUTES REQUIRE SCHEDULE ADJUSTMENT")

        except Exception as e:
            print_error(f"Error in union breaks demo: {e}")

    def _cargo_types_user_selection(self) -> List[any]:
        """Allow user to select cargo loads for compatibility analysis"""
        try:
            cargo_data = self.data_service.get_all('cargo')
            if not cargo_data:
                print_error("No cargo found in database.")
                return None
            
            print(f"\n📋 Available Cargo (showing first 25 of {len(cargo_data)} total):")
            print("=" * 80)
            
            # Show limited list with package details
            available_cargo = []
            for cargo_dict in cargo_data[:25]:
                available_cargo.append(cargo_dict)
                packages_data = self.data_service.get_packages_by_cargo_id(cargo_dict['id']) if hasattr(self.data_service, 'get_packages_by_cargo_id') else []
                
                if packages_data:
                    types = [pkg.get('type', 'unknown') for pkg in packages_data]
                    volume = sum(pkg.get('volume', 0) for pkg in packages_data)
                    weight = sum(pkg.get('weight', 0) for pkg in packages_data)
                    print(f"  {cargo_dict['id']:3d}. Packages: {len(packages_data)} | Types: {set(types)} | Vol: {volume:.1f}m³ | Weight: {weight:.1f}kg")
                else:
                    print(f"  {cargo_dict['id']:3d}. Order: {cargo_dict.get('order_id', 'N/A')} | Truck: {cargo_dict.get('truck_id', 'N/A')} | (No package details)")
            
            if len(cargo_data) > 25:
                print(f"  ... and {len(cargo_data) - 25} more cargo loads")
            
            print(f"\nTotal cargo available: {len(cargo_data)}")
            
            while True:
                cargo_ids_input = get_input("\nEnter cargo IDs for compatibility analysis (comma-separated, e.g., 1,2,3): ")
                if not cargo_ids_input.strip():
                    print_error("Cargo selection is required.")
                    continue
                
                try:
                    cargo_ids = [int(id_str.strip()) for id_str in cargo_ids_input.split(',')]
                    
                    # Find selected cargo
                    selected_cargo = []
                    for cargo_id in cargo_ids:
                        cargo_dict = next((c for c in cargo_data if c['id'] == cargo_id), None)
                        if not cargo_dict:
                            print_error(f"Cargo ID {cargo_id} not found.")
                            break
                        selected_cargo.append(cargo_dict)
                    else:
                        # All cargo found successfully
                        if selected_cargo:
                            return selected_cargo
                        else:
                            print_error("No valid cargo could be found from selection.")
                            continue
                    
                except ValueError:
                    print_error("Please enter valid cargo IDs (numbers only, comma-separated).")
                    continue
                
        except Exception as e:
            print_error(f"Error in cargo selection: {e}")
            return None

    def _demo_cargo_types(self):
        """Bonus Requirement: Cargo Types"""
        print(f"\n{Colors.CYAN}🏷️ BONUS: CARGO TYPES{Colors.ENDC}")
        print("=" * 60)
        print("BONUS Requirement: Cargo type compatibility and")
        print("special handling requirements.")
        print("=" * 60)

        print_info("Cargo type compatibility rules:")
        print("• Standard: Compatible with standard and refrigerated")
        print("• Fragile: Must be isolated (no mixing)")
        print("• Refrigerated: Compatible with standard only") 
        print("• Hazmat: Must be completely isolated")

        try:
            # Check if user wants to select custom data
            print(f"\n💡 Choose data selection mode:")
            print("1. Show system compatibility matrix (quick demo)")
            print("2. Analyze real cargo compatibility (interactive)")
            
            while True:
                mode_choice = get_input("Enter choice (1 or 2): ")
                if mode_choice in ['1', '2']:
                    break
                print_error("Please enter 1 or 2.")
            
            if mode_choice == '2':
                # User selection mode
                selected_cargo = self._cargo_types_user_selection()
                if not selected_cargo:
                    print_info("Cargo compatibility analysis cancelled.")
                    return
                data_source = "Database"
                
                # Analyze real cargo compatibility
                self._analyze_cargo_compatibility(selected_cargo, data_source)
                
            else:
                # System demonstration mode
                self._show_cargo_type_matrix()

        except Exception as e:
            print_error(f"Error in cargo types demo: {e}")

    def _show_cargo_type_matrix(self):
        """Show the cargo type compatibility system"""
        cargo_types = [
            (CargoType.STANDARD, "Standard cargo"),
            (CargoType.FRAGILE, "Fragile cargo"), 
            (CargoType.REFRIGERATED, "Refrigerated cargo"),
            (CargoType.HAZMAT, "Hazmat cargo")
        ]
        
        items = [
            ("Source", "System Schema"),
            ("Total Cargo Types", len(cargo_types)),
            ("Standard", "Compatible with refrigerated"),
            ("Fragile", "Requires isolation"), 
            ("Refrigerated", "Compatible with standard"),
            ("Hazmat", "Requires complete isolation"),
            ("Validation", "Matrix-based compatibility check")
        ]
        self._print_data_info_box("🏷️ CARGO TYPE SYSTEM", items)

        # Business rule compatibility matrix
        compatibility_rules = {
            CargoType.STANDARD: [CargoType.STANDARD, CargoType.REFRIGERATED],
            CargoType.FRAGILE: [CargoType.FRAGILE],  # Isolated
            CargoType.REFRIGERATED: [CargoType.REFRIGERATED, CargoType.STANDARD],
            CargoType.HAZMAT: [CargoType.HAZMAT]  # Completely isolated
        }

        print(f"\n🔍 CARGO COMPATIBILITY MATRIX:")
        
        for cargo_type, description in cargo_types:
            compatible = compatibility_rules[cargo_type]
            compatible_names = [ct.value for ct in compatible]
            
            print(f"   {description}:")
            print(f"     Compatible with: {', '.join(compatible_names)}")
            
            if len(compatible) == 1:
                print(f"     Restriction: ⚠️  Requires isolated transport")
            else:
                print(f"     Restriction: ✅ Can mix with compatible types")
            print("")

        print_success("✅ REQUIREMENT 8: CARGO TYPE SYSTEM DEMONSTRATED")

    def _analyze_cargo_compatibility(self, selected_cargo, data_source):
        """Analyze compatibility of selected real cargo loads"""
        
        # Display selected cargo information
        items = [("Source", data_source), ("Cargo Loads Selected", len(selected_cargo))]
        
        cargo_details = []
        for i, cargo_dict in enumerate(selected_cargo, 1):
            items.append((f"Cargo {i} ID", cargo_dict['id']))
            items.append((f"Cargo {i} Order", cargo_dict.get('order_id', 'N/A')))
            
            # Get packages for this cargo to determine types
            packages_data = self.data_service.get_packages_by_cargo_id(cargo_dict['id']) if hasattr(self.data_service, 'get_packages_by_cargo_id') else []
            
            if packages_data:
                types = [pkg.get('type', 'standard') for pkg in packages_data]
                volume = sum(pkg.get('volume', 0) for pkg in packages_data)
                weight = sum(pkg.get('weight', 0) for pkg in packages_data)
                cargo_details.append({
                    'id': cargo_dict['id'],
                    'types': set(types),
                    'volume': volume,
                    'weight': weight
                })
                items.append((f"Cargo {i} Types", str(set(types))))
                items.append((f"Cargo {i} Volume", f"{volume:.1f}m³"))
            else:
                # Fallback - assume standard type
                cargo_details.append({
                    'id': cargo_dict['id'],
                    'types': {'standard'},
                    'volume': 0,
                    'weight': 0
                })
                items.append((f"Cargo {i} Types", "{'standard'} (assumed)"))
        
        self._print_data_info_box("🏷️ CARGO COMPATIBILITY ANALYSIS DATA", items)
        
        print(f"\n🔍 COMPATIBILITY ANALYSIS:")
        
        # Business rule compatibility matrix
        incompatible_pairs = [
            ('hazmat', 'fragile'),
            ('hazmat', 'standard'),
            ('hazmat', 'refrigerated'),
            ('fragile', 'standard'),
            ('fragile', 'refrigerated')
        ]
        
        all_compatible = True
        violations = []
        
        # Check each pair of cargo loads for compatibility
        for i, cargo1 in enumerate(cargo_details):
            for j, cargo2 in enumerate(cargo_details):
                if i >= j:  # Skip duplicate pairs and self-comparison
                    continue
                    
                print(f"   Cargo {cargo1['id']} vs Cargo {cargo2['id']}:")
                print(f"     Types: {cargo1['types']} vs {cargo2['types']}")
                
                # Check for incompatible combinations
                compatibility_violations = []
                for type1 in cargo1['types']:
                    for type2 in cargo2['types']:
                        for incompatible_type1, incompatible_type2 in incompatible_pairs:
                            if ((type1 == incompatible_type1 and type2 == incompatible_type2) or
                                (type1 == incompatible_type2 and type2 == incompatible_type1)):
                                compatibility_violations.append(f"{type1} + {type2}")
                
                if compatibility_violations:
                    print(f"     ❌ INCOMPATIBLE - {', '.join(compatibility_violations)}")
                    violations.extend(compatibility_violations)
                    all_compatible = False
                else:
                    print(f"     ✅ COMPATIBLE")
                print("")
        
        # Overall summary
        print(f"📊 CARGO COMPATIBILITY SUMMARY:")
        print(f"   • Total cargo combinations analyzed: {len(selected_cargo) * (len(selected_cargo) - 1) // 2}")
        print(f"   • Compatible combinations: {(len(selected_cargo) * (len(selected_cargo) - 1) // 2) - len(set(violations))}")
        print(f"   • Incompatible combinations: {len(set(violations))}")
        print("")

        if all_compatible:
            print_success("✅ REQUIREMENT 8: ALL CARGO LOADS COMPATIBLE FOR MIXED TRANSPORT")
        else:
            print_warning(f"⚠️ REQUIREMENT 8: INCOMPATIBLE CARGO DETECTED - REQUIRES SEPARATE TRANSPORT")
            print_warning(f"   Violations: {', '.join(set(violations))}")

    # Helper methods for test data creation and retrieval

    def _get_sample_routes(self, count: int = 1) -> List[Route]:
        """Get sample routes from data service"""
        try:
            routes_data = self.data_service.get_all('routes')
            if routes_data and len(routes_data) >= count:
                routes = []
                for route_dict in routes_data[:count]:
                    route = self._dict_to_route(route_dict)
                    if route:
                        routes.append(route)
                if routes:
                    self._data_sources['routes'] = f"{self.data_service.mode.title()} DB"
                    return routes
            
            # Create fallback routes if none exist or conversion failed
            self._data_sources['routes'] = "Fallback Data"
            return self._create_fallback_routes(count)
        except Exception as e:
            print_error(f"Error getting routes: {e}")
            self._data_sources['routes'] = "Fallback Data"
            return self._create_fallback_routes(count)

    def _get_sample_trucks(self, count: int = 1) -> List[Truck]:
        """Get sample trucks from data service"""
        try:
            trucks_data = self.data_service.get_all('trucks')
            if trucks_data and len(trucks_data) >= count:
                trucks = []
                for truck_dict in trucks_data[:count]:
                    truck = self._dict_to_truck(truck_dict)
                    if truck:
                        trucks.append(truck)
                if trucks:
                    self._data_sources['trucks'] = f"{self.data_service.mode.title()} DB"
                    return trucks
            
            self._data_sources['trucks'] = "Fallback Data"
            return self._create_fallback_trucks(count)
        except Exception as e:
            print_error(f"Error getting trucks: {e}")
            self._data_sources['trucks'] = "Fallback Data"
            return self._create_fallback_trucks(count)

    def _get_sample_locations(self, count: int = 2) -> List[Location]:
        """Get sample locations from data service"""
        try:
            locations_data = self.data_service.get_all('locations')
            if locations_data and len(locations_data) >= count:
                locations = []
                for location_dict in locations_data[:count]:
                    location = self._dict_to_location(location_dict)
                    if location:
                        locations.append(location)
                if locations:
                    self._data_sources['locations'] = f"{self.data_service.mode.title()} DB"
                    return locations
            
            self._data_sources['locations'] = "Fallback Data"
            return self._create_fallback_locations(count)
        except Exception as e:
            print_error(f"Error getting locations: {e}")
            self._data_sources['locations'] = "Fallback Data"
            return self._create_fallback_locations(count)

    def _dict_to_route(self, route_dict: dict) -> Optional[Route]:
        """Convert route dictionary to Route object"""
        try:
            # Get required location data
            origin_data = route_dict.get('location_origin')
            destiny_data = route_dict.get('location_destiny')
            
            # If locations are IDs, we need to fetch them separately
            if isinstance(origin_data, int):
                locations_data = self.data_service.get_all('locations')
                origin_data = next((loc for loc in locations_data if loc.get('id') == origin_data), None)
                destiny_data = next((loc for loc in locations_data if loc.get('id') == route_dict.get('location_destiny_id')), None)
            
            if not origin_data or not destiny_data:
                return None
            
            origin = self._dict_to_location(origin_data)
            destiny = self._dict_to_location(destiny_data)
            
            if not origin or not destiny:
                return None
            
            return Route(
                id=route_dict.get('id', 1),
                location_origin_id=route_dict.get('location_origin_id', origin.id),
                location_destiny_id=route_dict.get('location_destiny_id', destiny.id),
                location_origin=origin,
                location_destiny=destiny,
                profitability=route_dict.get('profitability', -50.0),
                orders=[]
            )
        except Exception as e:
            print_error(f"Error converting route dict: {e}")
            return None

    def _dict_to_truck(self, truck_dict: dict) -> Optional[Truck]:
        """Convert truck dictionary to Truck object"""
        try:
            return Truck(
                id=truck_dict.get('id', 1),
                capacity=truck_dict.get('capacity', 48.0),
                autonomy=truck_dict.get('autonomy', 800.0),
                type=truck_dict.get('type', 'standard'),
                cargo_loads=[]
            )
        except Exception as e:
            print_error(f"Error converting truck dict: {e}")
            return None

    def _dict_to_location(self, location_dict: dict) -> Optional[Location]:
        """Convert location dictionary to Location object"""
        try:
            return Location(
                id=location_dict.get('id', 1),
                lat=float(location_dict.get('lat', 33.7490)),
                lng=float(location_dict.get('lng', -84.3880))
            )
        except Exception as e:
            print_error(f"Error converting location dict: {e}")
            return None

    def _dict_to_package(self, package_dict: dict) -> Optional[Package]:
        """Convert package dictionary to Package object"""
        try:
            from schemas.schemas import CargoType
            
            # Handle cargo type
            cargo_type_str = package_dict.get('type', 'standard')
            if isinstance(cargo_type_str, str):
                cargo_type_map = {
                    'standard': CargoType.STANDARD,
                    'fragile': CargoType.FRAGILE,
                    'hazmat': CargoType.HAZMAT,  
                    'hazardous': CargoType.HAZMAT,
                    'refrigerated': CargoType.REFRIGERATED
                }
                cargo_type = cargo_type_map.get(cargo_type_str.lower(), CargoType.STANDARD)
            else:
                cargo_type = cargo_type_str  # Assume it's already a CargoType enum
            
            return Package(
                id=package_dict.get('id', 1),
                volume=package_dict.get('volume', 1.0),
                weight=package_dict.get('weight', 10.0),
                type=cargo_type,
                cargo_id=package_dict.get('cargo_id')
            )
        except Exception as e:
            print_error(f"Error converting package dict: {e}")
            return None

    def _create_simple_route_from_dict(self, route_dict: dict) -> Optional[Route]:
        """Create a simple route object when full location data is not available"""
        try:
            # Get location IDs from route
            origin_id = route_dict.get('location_origin_id')
            destiny_id = route_dict.get('location_destiny_id')
            
            if not origin_id or not destiny_id:
                print_error("Route missing location IDs")
                return None
            
            # Get all locations to find the origin and destiny
            locations_data = self.data_service.get_all('locations')
            
            origin_dict = next((l for l in locations_data if l.get('id') == origin_id), None)
            destiny_dict = next((l for l in locations_data if l.get('id') == destiny_id), None)
            
            if not origin_dict or not destiny_dict:
                print_error(f"Could not find locations {origin_id} or {destiny_id}")
                return None
                
            origin = self._dict_to_location(origin_dict)
            destiny = self._dict_to_location(destiny_dict)
            
            if not origin or not destiny:
                print_error("Failed to convert location data")
                return None
                
            return Route(
                id=route_dict.get('id', 1),
                location_origin_id=origin_id,
                location_destiny_id=destiny_id,
                location_origin=origin,
                location_destiny=destiny,
                profitability=route_dict.get('profitability', -50.0),
                orders=[]
            )
        except Exception as e:
            print_error(f"Error creating simple route: {e}")
            return None

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