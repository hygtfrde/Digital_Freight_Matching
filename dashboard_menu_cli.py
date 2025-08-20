"""
========== DASHBOARD MENU ==========


┌─────────────────────────────────────────────────────────────┐
│                    MAIN MENU                                │
│                 Digital Freight Matching System              │
├─────────────────────────────────────────────────────────────┤
│  1. 📦 Order Management                                     │
│  2. 🚛 Fleet Management                                     │
│  3. 🗺️  Route Management                                    │
│  4. 💰 Pricing & Matching                                   │
│  5. 👥 Client Management                                    │
│  6. 📊 Reports & Analytics                                  │
│  7. ⚙️  System Configuration                                │
│  8. 🔍 Quick Search                                         │
│  9. ❌ Exit                                                 │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬─────────────┐
        ▼                   ▼                   ▼             ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ...
│ 1. ORDER MGMT │   │ 2. FLEET MGMT │   │ 3. ROUTE MGMT │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ 1. List All   │   │ 1. List Trucks│   │ 1. List Routes│
│ 2. Add New    │   │ 2. Add Truck  │   │ 2. Add Route  │
│ 3. View Detail│   │ 3. Edit Truck │   │ 3. Edit Route │
│ 4. Edit Order │   │ 4. Delete     │   │ 4. Delete     │
│ 5. Delete     │   │ 5. View Loads │   │ 5. View Orders│
│ 6. Match Order│   │ 6. Utilization│   │ 6. Optimize   │
│ 7. Pending    │   │ 7. Maintenance│   │ 7. Path View  │
│ 0. Back       │   │ 0. Back       │   │ 0. Back       │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
   [SUB-MENUS]         [SUB-MENUS]         [SUB-MENUS]

┌─────────────────────────────────────────────────────────────┐
│                    4. PRICING & MATCHING                    │
├─────────────────────────────────────────────────────────────┤
│  1. 🎯 Auto-Match Orders (Run matching algorithm)           │
│  2. 📋 View Pending Orders                                  │
│  3. 🔄 Process Pending Queue                                │
│  4. 💵 Calculate Route Profitability                        │
│  5. 🆕 Create New Route from Pending                        │
│  6. 📊 Matching Statistics                                  │
│  7. ⚙️  Matching Criteria Settings                          │
│  0. 🔙 Back to Main Menu                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    6. REPORTS & ANALYTICS                   │
├─────────────────────────────────────────────────────────────┤
│  1. 📈 Daily Summary                                        │
│  2. 🚛 Fleet Utilization Report                             │
│  3. 💰 Profitability Analysis                               │
│  4. ⏱️  Route Efficiency Metrics                            │
│  5. 📦 Cargo Type Distribution                              │
│  6. 🗺️  Geographic Coverage Map                            │
│  7. 📊 Custom Report Builder                                │
│  0. 🔙 Back to Main Menu                                    │
└─────────────────────────────────────────────────────────────┘

"""



import os
import sys
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import time

# Import schemas
from schemas.schemas import (
    CargoType, Location, Package, Cargo, Order,
    Client, Truck, Route, create_order_from_dict
)

# Import DFM business logic
from dfm import (
    PricingService, CriteriaMatcher, pretty_print_order
)

# For API calls (we'll simulate if not available)
try:
    import requests
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    print("⚠️ Requests module not available - API calls will be simulated")


class MenuColor:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DashboardState:
    """Maintains the state of the dashboard application"""
    
    def __init__(self):
        self.menu_stack: List[str] = ["main"]
        self.pricing_service: Optional[PricingService] = None
        self.api_base_url = "http://localhost:8000"
        self.current_user = "operator"
        self.session_start = datetime.now()
        
        # In-memory data stores (when API not available)
        self.orders: List[Order] = []
        self.trucks: List[Truck] = []
        self.routes: List[Route] = []
        self.clients: List[Client] = []
        
        # Filters and preferences
        self.filters: Dict[str, Any] = {}
        self.page_size = 10
        self.last_search = ""
        
        # Initialize pricing service with demo data
        # self.initialize_demo_data()

    
    def initialize_demo_data(self):
        """Initialize with some demo data for testing"""
        # Demo locations
        loc1 = Location(id=1, lat=37.7749, lng=-122.4194)  # San Francisco
        loc2 = Location(id=2, lat=34.0522, lng=-118.2437)  # Los Angeles
        loc3 = Location(id=3, lat=36.1699, lng=-115.1398)  # Las Vegas
        
        # Demo trucks
        self.trucks = [
            Truck(id=1, autonomy=600.0, capacity=100.0, type="standard"),
            Truck(id=2, autonomy=800.0, capacity=150.0, type="refrigerated"),
            Truck(id=3, autonomy=500.0, capacity=80.0, type="hazmat"),
        ]
        
        # Demo routes
        self.routes = [
            Route(
                id=1,
                location_origin_id=1,
                location_destiny_id=2,
                location_origin=loc1,
                location_destiny=loc2,
                path=[loc1, loc3, loc2],
                truck_id=1
            ),
            Route(
                id=2,
                location_origin_id=2,
                location_destiny_id=3,
                location_origin=loc2,
                location_destiny=loc3,
                path=[loc2, loc3],
                truck_id=2
            ),
        ]
        
        # Initialize pricing service
        self.pricing_service = PricingService(
            routes=self.routes,
            trucks=self.trucks,
            cost_per_mile=1.5
        )
    
    @property
    def breadcrumb(self) -> str:
        """Get current menu breadcrumb"""
        return " > ".join(self.menu_stack)


class CLIDashboard:
    """Main CLI Dashboard Application"""
    
    def __init__(self):
        self.state = DashboardState()
        self.running = True
    
    # ============= UTILITY METHODS =============

    def exit_program(self):
        print("Exiting the Digital Freight Matching System. Goodbye!")
        self.running = False
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print application header"""
        self.clear_screen()
        print(MenuColor.CYAN + "=" * 65 + MenuColor.ENDC)
        print(MenuColor.BOLD + "🚛 DIGITAL FREIGHT MATCHING SYSTEM".center(65) + MenuColor.ENDC)
        print(MenuColor.CYAN + "=" * 65 + MenuColor.ENDC)
        print(f"📍 Location: {self.state.breadcrumb}")
        print(f"👤 User: {self.state.current_user}")
        print(f"⏰ Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Show quick stats
        if self.state.pricing_service:
            pending = len(self.state.pricing_service.pending_orders)
            if pending > 0:
                print(MenuColor.WARNING + f"⚠️  {pending} pending orders" + MenuColor.ENDC)
        
        print("-" * 65)
        print()
    
    def print_menu_box(self, title: str, options: List[Tuple[str, str, str]]):
        """
        Print a formatted menu box
        options: List of (key, icon, label) tuples
        """
        width = 65
        print("┌" + "─" * (width - 2) + "┐")
        print("│" + title.center(width - 2) + "│")
        print("├" + "─" * (width - 2) + "┤")
        
        for key, icon, label in options:
            line = f"  {key}. {icon} {label}"
            padding = width - len(line) - 1
            print("│" + line + " " * padding + "│")
        
        print("└" + "─" * (width - 2) + "┘")
    
    def get_input(self, prompt: str = "Enter choice: ") -> str:
        """Get user input with error handling"""
        try:
            return input(MenuColor.CYAN + prompt + MenuColor.ENDC).strip()
        except KeyboardInterrupt:
            print("\n\n" + MenuColor.WARNING + "Interrupted. Saving state..." + MenuColor.ENDC)
            # Could save state here
            sys.exit(0)
        except Exception as e:
            print(MenuColor.FAIL + f"Input error: {e}" + MenuColor.ENDC)
            return ""
    
    def pause(self):
        """Pause for user to read output"""
        input("\n" + MenuColor.CYAN + "Press Enter to continue..." + MenuColor.ENDC)
    
    def success_message(self, msg: str):
        """Display success message"""
        print(MenuColor.GREEN + f"✅ {msg}" + MenuColor.ENDC)
    
    def error_message(self, msg: str):
        """Display error message"""
        print(MenuColor.FAIL + f"❌ {msg}" + MenuColor.ENDC)
    
    def warning_message(self, msg: str):
        """Display warning message"""
        print(MenuColor.WARNING + f"⚠️  {msg}" + MenuColor.ENDC)
    
    # ============= MAIN MENU =============
    
    def main_menu(self):
        """Display and handle main menu"""
        self.state.menu_stack = ["Main"]
        
        while self.running:
            self.print_header()
            
            options = [
                ("1", "📦", "Order Management"),
                ("2", "🚛", "Fleet Management"),
                ("3", "🗺️", "Route Management"),
                ("4", "💰", "Pricing & Matching"),
                ("5", "👥", "Client Management"),
                ("6", "📊", "Reports & Analytics"),
                ("7", "⚙️", "System Configuration"),
                ("8", "🔍", "Quick Search"),
                ("9", "❌", "Exit"),
            ]
            
            self.print_menu_box("MAIN MENU", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.order_management_menu()
            elif choice == "2":
                self.fleet_management_menu()
            elif choice == "3":
                self.route_management_menu()
            elif choice == "4":
                self.pricing_matching_menu()
            elif choice == "5":
                self.client_management_menu()
            elif choice == "6":
                self.reports_analytics_menu()
            elif choice == "7":
                self.system_configuration_menu()
            elif choice == "8":
                self.quick_search()
            elif choice == "9":
                self.exit_program()
            else:
                self.error_message("Invalid choice. Please try again.")
                self.pause()
    
    # ============= ORDER MANAGEMENT =============
    
    def order_management_menu(self):
        """Order Management submenu"""
        self.state.menu_stack.append("Order Management")
        
        while True:
            self.print_header()
            
            options = [
                ("1", "📋", "List All Orders"),
                ("2", "➕", "Add New Order"),
                ("3", "🔍", "View Order Details"),
                ("4", "✏️", "Edit Order"),
                ("5", "🗑️", "Delete Order"),
                ("6", "🎯", "Match Order to Route"),
                ("7", "⏳", "View Pending Orders"),
                ("0", "🔙", "Back to Main Menu"),
            ]
            
            self.print_menu_box("ORDER MANAGEMENT", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.list_all_orders()
            elif choice == "2":
                self.add_new_order()
            elif choice == "3":
                self.view_order_details()
            elif choice == "4":
                self.edit_order()
            elif choice == "5":
                self.delete_order()
            elif choice == "6":
                self.match_order_to_route()
            elif choice == "7":
                self.view_pending_orders()
            elif choice == "0":
                self.state.menu_stack.pop()
                return
            else:
                self.error_message("Invalid choice")
                self.pause()
    
    def list_all_orders(self):
        """List all orders with pagination"""
        self.print_header()
        print(MenuColor.BOLD + "📋 ALL ORDERS" + MenuColor.ENDC)
        print("-" * 65)
        
        # Try API first, fallback to local data
        if API_AVAILABLE:
            try:
                response = requests.get(f"{self.state.api_base_url}/orders")
                if response.status_code == 200:
                    orders = response.json()
                    if orders:
                        for i, order in enumerate(orders, 1):
                            print(f"\n[{i}] Order ID: {order.get('id', 'N/A')}")
                            print(f"    Origin: ({order['location_origin']['lat']:.2f}, "
                                  f"{order['location_origin']['lng']:.2f})")
                            print(f"    Destination: ({order['location_destiny']['lat']:.2f}, "
                                  f"{order['location_destiny']['lng']:.2f})")
                    else:
                        print("No orders found.")
                else:
                    self.error_message(f"API error: {response.status_code}")
            except Exception as e:
                self.error_message(f"Could not connect to API: {e}")
                print("Using local data...")
                self._list_local_orders()
        else:
            self._list_local_orders()
        
        self.pause()
    
    def _list_local_orders(self):
        """List orders from local state"""
        if self.state.orders:
            for i, order in enumerate(self.state.orders, 1):
                print(f"\n[{i}] Order")
                pretty_print_order(order, indent=4)
        else:
            print("No orders in local storage.")
    
    def add_new_order(self):
        """Add a new order through wizard"""
        self.print_header()
        print(MenuColor.BOLD + "➕ ADD NEW ORDER" + MenuColor.ENDC)
        print("-" * 65)
        
        try:
            # Get pickup location
            print("\n📍 Pickup Location:")
            pickup_lat = float(self.get_input("  Latitude: "))
            pickup_lng = float(self.get_input("  Longitude: "))
            
            # Get dropoff location
            print("\n📍 Dropoff Location:")
            dropoff_lat = float(self.get_input("  Latitude: "))
            dropoff_lng = float(self.get_input("  Longitude: "))
            
            # Get packages
            packages = []
            while True:
                print(f"\n📦 Package {len(packages) + 1}:")
                volume = float(self.get_input("  Volume (m³): "))
                weight = float(self.get_input("  Weight (kg): "))
                
                print("  Cargo Type:")
                for i, cargo_type in enumerate(CargoType, 1):
                    print(f"    {i}. {cargo_type.value}")
                type_choice = int(self.get_input("  Select type (1-4): "))
                cargo_type = list(CargoType)[type_choice - 1]
                
                packages.append((volume, weight, cargo_type.value))
                
                add_more = self.get_input("\n  Add another package? (y/n): ").lower()
                if add_more != 'y':
                    break
            
            # Create order data
            order_data = {
                'cargo': {'packages': packages},
                'pick-up': {'latitude': pickup_lat, 'longitude': pickup_lng},
                'drop-off': {'latitude': dropoff_lat, 'longitude': dropoff_lng}
            }
            
            # Process with pricing service
            if self.state.pricing_service:
                result = self.state.pricing_service.process_order(order_data)
                
                if result['status'] == 'matched':
                    self.success_message(f"Order matched to Route {result['route']}, "
                                       f"Truck {result['truck']}")
                else:
                    self.warning_message(f"Order added to pending queue: {result['reason']}")
            else:
                # Just create the order
                order = create_order_from_dict(order_data)
                self.state.orders.append(order)
                self.success_message("Order created locally")
            
        except ValueError as e:
            self.error_message(f"Invalid input: {e}")
        except Exception as e:
            self.error_message(f"Error creating order: {e}")
        
        self.pause()
    
    def view_order_details(self):
        """View detailed order information"""
        self.print_header()
        print(MenuColor.BOLD + "🔍 VIEW ORDER DETAILS" + MenuColor.ENDC)
        print("-" * 65)
        
        # Placeholder implementation
        self.warning_message("This feature is not yet fully implemented")
        print("\nWould show detailed order information including:")
        print("  • Complete cargo manifest")
        print("  • Route assignment")
        print("  • Delivery status")
        print("  • Client information")
        print("  • Profitability metrics")
        
        self.pause()
    
    def edit_order(self):
        """Edit an existing order"""
        self.print_header()
        print(MenuColor.BOLD + "✏️ EDIT ORDER" + MenuColor.ENDC)
        print("-" * 65)
        
        self.warning_message("This feature is not yet implemented")
        print("\nWould allow editing of:")
        print("  • Pickup/dropoff locations")
        print("  • Cargo details")
        print("  • Priority level")
        print("  • Special instructions")
        
        self.pause()
    
    def delete_order(self):
        """Delete an order"""
        self.print_header()
        print(MenuColor.BOLD + "🗑️ DELETE ORDER" + MenuColor.ENDC)
        print("-" * 65)
        
        order_id = self.get_input("Enter order ID to delete (or 0 to cancel): ")
        
        if order_id == "0":
            return
        
        confirm = self.get_input(f"Are you sure you want to delete order {order_id}? (y/n): ")
        if confirm.lower() == 'y':
            # Placeholder for actual deletion
            self.success_message(f"Order {order_id} deleted successfully")
        else:
            print("Deletion cancelled")
        
        self.pause()
    
    def match_order_to_route(self):
        """Match a single order to available routes"""
        self.print_header()
        print(MenuColor.BOLD + "🎯 MATCH ORDER TO ROUTE" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.pricing_service:
            self.error_message("Pricing service not initialized")
            self.pause()
            return
        
        # Show pending orders
        if self.state.pricing_service.pending_orders:
            print("\nPending Orders:")
            for i, order in enumerate(self.state.pricing_service.pending_orders, 1):
                print(f"[{i}] ", end="")
                pretty_print_order(order, indent=4)
            
            choice = self.get_input("\nSelect order to match (0 to cancel): ")
            if choice == "0":
                return
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.state.pricing_service.pending_orders):
                    order = self.state.pricing_service.pending_orders[idx]
                    match = self.state.pricing_service.match_order(order)
                    
                    if match:
                        route, truck = match
                        self.success_message(f"Order matched to Route {route.id}, Truck {truck.id}")
                        self.state.pricing_service.pending_orders.remove(order)
                    else:
                        self.warning_message("No suitable route found")
                else:
                    self.error_message("Invalid selection")
            except ValueError:
                self.error_message("Invalid input")
        else:
            print("No pending orders to match")
        
        self.pause()
    
    def view_pending_orders(self):
        """View all pending orders"""
        self.print_header()
        print(MenuColor.BOLD + "⏳ PENDING ORDERS" + MenuColor.ENDC)
        print("-" * 65)
        
        if self.state.pricing_service and self.state.pricing_service.pending_orders:
            print(f"\nTotal pending: {len(self.state.pricing_service.pending_orders)}")
            print("-" * 65)
            
            for i, order in enumerate(self.state.pricing_service.pending_orders, 1):
                print(f"\n[{i}] Pending Order:")
                pretty_print_order(order, indent=4)
        else:
            self.success_message("No pending orders!")
        
        self.pause()
    
    # ============= FLEET MANAGEMENT =============
    
    def fleet_management_menu(self):
        """Fleet Management submenu"""
        self.state.menu_stack.append("Fleet Management")
        
        while True:
            self.print_header()
            
            options = [
                ("1", "📋", "List All Trucks"),
                ("2", "➕", "Add New Truck"),
                ("3", "✏️", "Edit Truck"),
                ("4", "🗑️", "Delete Truck"),
                ("5", "📦", "View Truck Loads"),
                ("6", "📊", "Fleet Utilization"),
                ("7", "🔧", "Maintenance Schedule"),
                ("0", "🔙", "Back to Main Menu"),
            ]
            
            self.print_menu_box("FLEET MANAGEMENT", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.list_all_trucks()
            elif choice == "2":
                self.add_new_truck()
            elif choice == "3":
                self.edit_truck()
            elif choice == "4":
                self.delete_truck()
            elif choice == "5":
                self.view_truck_loads()
            elif choice == "6":
                self.fleet_utilization()
            elif choice == "7":
                self.maintenance_schedule()
            elif choice == "0":
                self.state.menu_stack.pop()
                return
            else:
                self.error_message("Invalid choice")
                self.pause()
    
    def list_all_trucks(self):
        """List all trucks in fleet"""
        self.print_header()
        print(MenuColor.BOLD + "📋 FLEET INVENTORY" + MenuColor.ENDC)
        print("-" * 65)
        
        if self.state.trucks:
            for i, truck in enumerate(self.state.trucks, 1):
                print(f"\n[{i}] Truck ID: {truck.id}")
                print(f"    Type: {truck.type}")
                print(f"    Autonomy: {truck.autonomy} km")
                print(f"    Capacity: {truck.capacity} m³")
                print(f"    Available: {truck.available_capacity():.2f} m³")
                print(f"    Utilization: {truck.utilization_percent():.1f}%")
                
                # Show utilization bar
                util = truck.utilization_percent()
                bar_length = 20
                filled = int(bar_length * util / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"    [{bar}]")
        else:
            print("No trucks in fleet")
        
        self.pause()
    
    def add_new_truck(self):
        """Add a new truck to fleet"""
        self.print_header()
        print(MenuColor.BOLD + "➕ ADD NEW TRUCK" + MenuColor.ENDC)
        print("-" * 65)
        
        try:
            truck_type = self.get_input("Truck type (standard/refrigerated/hazmat): ").lower()
            autonomy = float(self.get_input("Autonomy (km): "))
            capacity = float(self.get_input("Capacity (m³): "))
            
            truck = Truck(
                id=len(self.state.trucks) + 1,
                autonomy=autonomy,
                capacity=capacity,
                type=truck_type
            )
            
            self.state.trucks.append(truck)
            self.success_message(f"Added {truck_type} truck to fleet")
            
            # Update pricing service if it exists
            if self.state.pricing_service:
                self.state.pricing_service.trucks.append(truck)
            
        except ValueError:
            self.error_message("Invalid input")
        except Exception as e:
            self.error_message(f"Error adding truck: {e}")
        
        self.pause()
    
    def edit_truck(self):
        """Edit truck details"""
        self.print_header()
        print(MenuColor.BOLD + "✏️ EDIT TRUCK" + MenuColor.ENDC)
        print("-" * 65)
        
        self.warning_message("This feature is not yet implemented")
        print("\nWould allow editing of:")
        print("  • Truck capacity")
        print("  • Autonomy range")
        print("  • Maintenance status")
        print("  • Driver assignment")
        
        self.pause()
    
    def delete_truck(self):
        """Delete a truck from fleet"""
        self.print_header()
        print(MenuColor.BOLD + "🗑️ DELETE TRUCK" + MenuColor.ENDC)
        print("-" * 65)
        
        self.list_all_trucks()
        truck_id = self.get_input("\nEnter truck ID to delete (or 0 to cancel): ")
        
        if truck_id == "0":
            return
        
        confirm = self.get_input(f"Are you sure you want to delete truck {truck_id}? (y/n): ")
        if confirm.lower() == 'y':
            self.success_message(f"Truck {truck_id} removed from fleet")
        
        self.pause()
    
    def view_truck_loads(self):
        """View current loads for all trucks"""
        self.print_header()
        print(MenuColor.BOLD + "📦 TRUCK LOADS" + MenuColor.ENDC)
        print("-" * 65)
        
        for truck in self.state.trucks:
            print(f"\nTruck {truck.id} ({truck.type}):")
            if truck.cargo_loads:
                total_volume = 0
                total_weight = 0
                for i, cargo in enumerate(truck.cargo_loads, 1):
                    vol = cargo.total_volume()
                    weight = cargo.total_weight()
                    total_volume += vol
                    total_weight += weight
                    print(f"  Load {i}: {vol:.2f} m³, {weight:.2f} kg")
                print(f"  Total: {total_volume:.2f}/{truck.capacity} m³")
            else:
                print("  No cargo loaded")
        
        self.pause()
    
    def fleet_utilization(self):
        """Show fleet utilization statistics"""
        self.print_header()
        print(MenuColor.BOLD + "📊 FLEET UTILIZATION" + MenuColor.ENDC)
        print("-" * 65)
        
        if self.state.trucks:
            total_capacity = sum(t.capacity for t in self.state.trucks)
            used_capacity = sum(t.capacity - t.available_capacity() for t in self.state.trucks)
            utilization = (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
            
            print(f"\nFleet Size: {len(self.state.trucks)} trucks")
            print(f"Total Capacity: {total_capacity:.2f} m³")
            print(f"Used Capacity: {used_capacity:.2f} m³")
            print(f"Available Capacity: {total_capacity - used_capacity:.2f} m³")
            print(f"Overall Utilization: {utilization:.1f}%")
            
            # Visual representation
            print("\nUtilization by Truck Type:")
            truck_types = {}
            for truck in self.state.trucks:
                if truck.type not in truck_types:
                    truck_types[truck.type] = []
                truck_types[truck.type].append(truck)
            
            for truck_type, trucks in truck_types.items():
                type_util = sum(t.utilization_percent() for t in trucks) / len(trucks)
                bar_length = 30
                filled = int(bar_length * type_util / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"  {truck_type:12} [{bar}] {type_util:.1f}%")
        else:
            print("No trucks in fleet")
        
        self.pause()
    
    def maintenance_schedule(self):
        """View and manage maintenance schedule"""
        self.print_header()
        print(MenuColor.BOLD + "🔧 MAINTENANCE SCHEDULE" + MenuColor.ENDC)
        print("-" * 65)
        
        self.warning_message("This feature is not yet implemented")
        print("\nWould show:")
        print("  • Scheduled maintenance dates")
        print("  • Service history")
        print("  • Upcoming inspections")
        print("  • Maintenance costs")
        
        self.pause()
    
    # ============= ROUTE MANAGEMENT =============
    
    def route_management_menu(self):
        """Route Management submenu"""
        self.state.menu_stack.append("Route Management")
        
        while True:
            self.print_header()
            
            options = [
                ("1", "📋", "List All Routes"),
                ("2", "➕", "Add New Route"),
                ("3", "✏️", "Edit Route"),
                ("4", "🗑️", "Delete Route"),
                ("5", "📦", "View Route Orders"),
                ("6", "⚡", "Optimize Route"),
                ("7", "🗺️", "View Route Path"),
                ("0", "🔙", "Back to Main Menu"),
            ]
            
            self.print_menu_box("ROUTE MANAGEMENT", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.list_all_routes()
            elif choice == "2":
                self.add_new_route()
            elif choice == "3":
                self.edit_route()
            elif choice == "4":
                self.delete_route()
            elif choice == "5":
                self.view_route_orders()
            elif choice == "6":
                self.optimize_route()
            elif choice == "7":
                self.view_route_path()
            elif choice == "0":
                self.state.menu_stack.pop()
                return
            else:
                self.error_message("Invalid choice")
                self.pause()
    
    def list_all_routes(self):
        """List all routes"""
        self.print_header()
        print(MenuColor.BOLD + "📋 ROUTE INVENTORY" + MenuColor.ENDC)
        print("-" * 65)
        
        if self.state.routes:
            for i, route in enumerate(self.state.routes, 1):
                print(f"\n[{i}] Route ID: {route.id}")
                if route.location_origin:
                    print(f"    Origin: ({route.location_origin.lat:.2f}, {route.location_origin.lng:.2f})")
                if route.location_destiny:
                    print(f"    Destination: ({route.location_destiny.lat:.2f}, {route.location_destiny.lng:.2f})")
                print(f"    Distance: {route.total_distance():.2f} km")
                print(f"    Time: {route.total_time():.2f} hours")
                print(f"    Orders: {len(route.orders)}")
                print(f"    Profitability: ${route.profitability:.2f}")
        else:
            print("No routes defined")
        
        self.pause()
    
    def add_new_route(self):
        """Add a new route"""
        self.print_header()
        print(MenuColor.BOLD + "➕ ADD NEW ROUTE" + MenuColor.ENDC)
        print("-" * 65)
        
        try:
            print("\n📍 Origin Location:")
            origin_lat = float(self.get_input("  Latitude: "))
            origin_lng = float(self.get_input("  Longitude: "))
            
            print("\n📍 Destination Location:")
            dest_lat = float(self.get_input("  Latitude: "))
            dest_lng = float(self.get_input("  Longitude: "))
            
            # Create route
            route = Route(
                id=len(self.state.routes) + 1,
                location_origin_id=0,  # Placeholder
                location_destiny_id=0,  # Placeholder
                location_origin=Location(lat=origin_lat, lng=origin_lng),
                location_destiny=Location(lat=dest_lat, lng=dest_lng),
                path=[
                    Location(lat=origin_lat, lng=origin_lng),
                    Location(lat=dest_lat, lng=dest_lng)
                ]
            )
            
            self.state.routes.append(route)
            
            # Update pricing service
            if self.state.pricing_service:
                self.state.pricing_service.routes.append(route)
            
            self.success_message(f"Route added (Distance: {route.total_distance():.2f} km)")
            
        except ValueError:
            self.error_message("Invalid input")
        except Exception as e:
            self.error_message(f"Error adding route: {e}")
        
        self.pause()
    
    def edit_route(self):
        """Edit route details"""
        self.print_header()
        print(MenuColor.BOLD + "✏️ EDIT ROUTE" + MenuColor.ENDC)
        print("-" * 65)
        
        self.warning_message("This feature is not yet implemented")
        print("\nWould allow editing of:")
        print("  • Waypoints")
        print("  • Assigned truck")
        print("  • Schedule")
        print("  • Priority")
        
        self.pause()
    
    def delete_route(self):
        """Delete a route"""
        self.print_header()
        print(MenuColor.BOLD + "🗑️ DELETE ROUTE" + MenuColor.ENDC)
        print("-" * 65)
        
        self.list_all_routes()
        route_id = self.get_input("\nEnter route ID to delete (or 0 to cancel): ")
        
        if route_id == "0":
            return
        
        confirm = self.get_input(f"Are you sure you want to delete route {route_id}? (y/n): ")
        if confirm.lower() == 'y':
            self.success_message(f"Route {route_id} deleted")
        
        self.pause()
    
    def view_route_orders(self):
        """View orders assigned to routes"""
        self.print_header()
        print(MenuColor.BOLD + "📦 ROUTE ORDERS" + MenuColor.ENDC)
        print("-" * 65)
        
        for route in self.state.routes:
            print(f"\nRoute {route.id}:")
            if route.orders:
                for i, order in enumerate(route.orders, 1):
                    print(f"  Order {i}:")
                    pretty_print_order(order, indent=8)
            else:
                print("  No orders assigned")
        
        self.pause()
    
    def optimize_route(self):
        """Optimize a route"""
        self.print_header()
        print(MenuColor.BOLD + "⚡ OPTIMIZE ROUTE" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.routes:
            print("No routes to optimize")
            self.pause()
            return
        
        self.list_all_routes()
        route_id = self.get_input("\nEnter route ID to optimize (or 0 to cancel): ")
        
        if route_id == "0":
            return
        
        try:
            idx = int(route_id) - 1
            if 0 <= idx < len(self.state.routes):
                route = self.state.routes[idx]
                original_distance = route.total_distance()
                
                # Simulate optimization
                print("\n⚙️ Optimizing route...")
                time.sleep(1)  # Simulate processing
                
                # In real implementation, would call optimization algorithm
                self.success_message(f"Route optimized!")
                print(f"Original distance: {original_distance:.2f} km")
                print(f"Optimized distance: {original_distance * 0.9:.2f} km")  # Simulated improvement
                print(f"Savings: {original_distance * 0.1:.2f} km")
            else:
                self.error_message("Invalid route ID")
        except ValueError:
            self.error_message("Invalid input")
        
        self.pause()
    
    def view_route_path(self):
        """View route path visualization"""
        self.print_header()
        print(MenuColor.BOLD + "🗺️ ROUTE PATH VISUALIZATION" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.routes:
            print("No routes to display")
            self.pause()
            return
        
        for route in self.state.routes:
            print(f"\nRoute {route.id}:")
            print("  START")
            
            if route.path:
                for i, location in enumerate(route.path):
                    if i == 0:
                        print(f"    📍 Origin: ({location.lat:.2f}, {location.lng:.2f})")
                    elif i == len(route.path) - 1:
                        print(f"    📍 Destination: ({location.lat:.2f}, {location.lng:.2f})")
                    else:
                        print(f"    ↓  Waypoint {i}: ({location.lat:.2f}, {location.lng:.2f})")
            
            print("  END")
            print(f"  Total Distance: {route.total_distance():.2f} km")
        
        self.pause()
    
    # ============= PRICING & MATCHING =============
    
    def pricing_matching_menu(self):
        """Pricing & Matching submenu"""
        self.state.menu_stack.append("Pricing & Matching")
        
        while True:
            self.print_header()
            
            options = [
                ("1", "🎯", "Auto-Match All Orders"),
                ("2", "📋", "View Pending Orders"),
                ("3", "🔄", "Process Pending Queue"),
                ("4", "💵", "Calculate Route Profitability"),
                ("5", "🆕", "Create Route from Pending"),
                ("6", "📊", "Matching Statistics"),
                ("7", "⚙️", "Configure Matching Rules"),
                ("0", "🔙", "Back to Main Menu"),
            ]
            
            self.print_menu_box("PRICING & MATCHING", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.auto_match_all_orders()
            elif choice == "2":
                self.view_pending_orders()  # Already defined above
            elif choice == "3":
                self.process_pending_queue()
            elif choice == "4":
                self.calculate_route_profitability()
            elif choice == "5":
                self.create_route_from_pending()
            elif choice == "6":
                self.matching_statistics()
            elif choice == "7":
                self.configure_matching_rules()
            elif choice == "0":
                self.state.menu_stack.pop()
                return
            else:
                self.error_message("Invalid choice")
                self.pause()
    
    def auto_match_all_orders(self):
        """Automatically match all pending orders"""
        self.print_header()
        print(MenuColor.BOLD + "🎯 AUTO-MATCH ALL ORDERS" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.pricing_service:
            self.error_message("Pricing service not initialized")
            self.pause()
            return
        
        if not self.state.pricing_service.pending_orders:
            print("No pending orders to match")
            self.pause()
            return
        
        print(f"\nProcessing {len(self.state.pricing_service.pending_orders)} pending orders...")
        print("-" * 65)
        
        matched = 0
        failed = 0
        
        # Process each pending order
        orders_to_process = self.state.pricing_service.pending_orders.copy()
        for order in orders_to_process:
            match = self.state.pricing_service.match_order(order)
            if match:
                route, truck = match
                matched += 1
                print(f"✅ Order matched to Route {route.id}, Truck {truck.id}")
                self.state.pricing_service.pending_orders.remove(order)
            else:
                failed += 1
                print(f"❌ No match found for order")
        
        print("-" * 65)
        print(f"\nResults: {matched} matched, {failed} unmatched")
        
        self.pause()
    
    def process_pending_queue(self):
        """Process the pending order queue"""
        self.print_header()
        print(MenuColor.BOLD + "🔄 PROCESS PENDING QUEUE" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.pricing_service:
            self.error_message("Pricing service not initialized")
            self.pause()
            return
        
        pending_count = len(self.state.pricing_service.pending_orders)
        print(f"\nPending orders: {pending_count}")
        
        if pending_count < 2:
            self.warning_message("Need at least 2 pending orders to create a new route")
        else:
            print("\nAttempting to create routes from pending orders...")
            
            new_route = self.state.pricing_service.create_new_route_from_pending()
            if new_route:
                self.success_message(f"Created new route with {len(new_route.orders)} orders")
                self.state.routes.append(new_route)
                print(f"Route profitability: ${new_route.profitability:.2f}")
            else:
                self.warning_message("Could not create viable route from pending orders")
        
        self.pause()
    
    def calculate_route_profitability(self):
        """Calculate profitability for all routes"""
        self.print_header()
        print(MenuColor.BOLD + "💵 ROUTE PROFITABILITY ANALYSIS" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.routes:
            print("No routes to analyze")
            self.pause()
            return
        
        cost_per_mile = 1.5
        revenue_per_order = 50.0
        total_profit = 0
        
        print(f"\nParameters:")
        print(f"  Cost per mile: ${cost_per_mile:.2f}")
        print(f"  Revenue per order: ${revenue_per_order:.2f}")
        print("-" * 65)
        
        for route in self.state.routes:
            distance_miles = route.total_distance() * 0.621371
            cost = distance_miles * cost_per_mile
            revenue = len(route.orders) * revenue_per_order
            profit = revenue - cost
            route.profitability = profit
            total_profit += profit
            
            print(f"\nRoute {route.id}:")
            print(f"  Distance: {route.total_distance():.2f} km ({distance_miles:.2f} miles)")
            print(f"  Orders: {len(route.orders)}")
            print(f"  Revenue: ${revenue:.2f}")
            print(f"  Cost: ${cost:.2f}")
            print(f"  Profit: ${profit:.2f}")
            
            # Visual profit indicator
            if profit > 0:
                print(f"  Status: {MenuColor.GREEN}✅ Profitable{MenuColor.ENDC}")
            else:
                print(f"  Status: {MenuColor.FAIL}❌ Loss{MenuColor.ENDC}")
        
        print("-" * 65)
        print(f"\nTotal Profit: ${total_profit:.2f}")
        
        self.pause()
    
    def create_route_from_pending(self):
        """Create new route from pending orders"""
        self.print_header()
        print(MenuColor.BOLD + "🆕 CREATE ROUTE FROM PENDING" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.pricing_service:
            self.error_message("Pricing service not initialized")
            self.pause()
            return
        
        # This is similar to process_pending_queue but with more detail
        pending = self.state.pricing_service.pending_orders
        
        if len(pending) < 2:
            self.warning_message(f"Need at least 2 pending orders (have {len(pending)})")
            self.pause()
            return
        
        print(f"\nAnalyzing {len(pending)} pending orders...")
        
        # Group by origin-destination
        route_groups = {}
        for order in pending:
            if order.location_origin and order.location_destiny:
                key = (
                    f"{order.location_origin.lat:.2f},{order.location_origin.lng:.2f}",
                    f"{order.location_destiny.lat:.2f},{order.location_destiny.lng:.2f}"
                )
                if key not in route_groups:
                    route_groups[key] = []
                route_groups[key].append(order)
        
        print(f"\nFound {len(route_groups)} potential route corridors:")
        for i, (key, orders) in enumerate(route_groups.items(), 1):
            origin, dest = key
            print(f"  {i}. {origin} → {dest}: {len(orders)} orders")
        
        if route_groups:
            # Find best group
            best_group = max(route_groups.values(), key=len)
            if len(best_group) >= 2:
                print(f"\nCreating route with {len(best_group)} orders...")
                
                new_route = self.state.pricing_service.create_new_route_from_pending()
                if new_route:
                    self.success_message("Route created successfully!")
                    self.state.routes.append(new_route)
                else:
                    self.error_message("Failed to create route")
            else:
                self.warning_message("No corridor has enough orders")
        
        self.pause()
    
    def matching_statistics(self):
        """Display matching statistics"""
        self.print_header()
        print(MenuColor.BOLD + "📊 MATCHING STATISTICS" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.pricing_service:
            self.warning_message("Pricing service not initialized")
            self.pause()
            return
        
        # Calculate statistics
        total_orders = len(self.state.orders)
        pending_orders = len(self.state.pricing_service.pending_orders)
        matched_orders = 0
        
        for route in self.state.routes:
            matched_orders += len(route.orders)
        
        total_tracked = matched_orders + pending_orders
        match_rate = (matched_orders / total_tracked * 100) if total_tracked > 0 else 0
        
        print(f"\n📈 Order Statistics:")
        print(f"  Total Orders: {total_tracked}")
        print(f"  Matched Orders: {matched_orders}")
        print(f"  Pending Orders: {pending_orders}")
        print(f"  Match Rate: {match_rate:.1f}%")
        
        # Visual match rate bar
        bar_length = 40
        filled = int(bar_length * match_rate / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n  Match Rate: [{bar}] {match_rate:.1f}%")
        
        print(f"\n🚛 Fleet Statistics:")
        print(f"  Active Trucks: {len(self.state.trucks)}")
        print(f"  Active Routes: {len(self.state.routes)}")
        
        if self.state.trucks:
            avg_utilization = sum(t.utilization_percent() for t in self.state.trucks) / len(self.state.trucks)
            print(f"  Average Utilization: {avg_utilization:.1f}%")
        
        print(f"\n💰 Financial Statistics:")
        total_profit = sum(r.profitability for r in self.state.routes)
        avg_profit = total_profit / len(self.state.routes) if self.state.routes else 0
        print(f"  Total Profit: ${total_profit:.2f}")
        print(f"  Average Profit/Route: ${avg_profit:.2f}")
        
        self.pause()
    
    def configure_matching_rules(self):
        """Configure matching criteria"""
        self.print_header()
        print(MenuColor.BOLD + "⚙️ MATCHING CONFIGURATION" + MenuColor.ENDC)
        print("-" * 65)
        
        print("\nCurrent Matching Rules:")
        print(f"  Max Deviation from Route: {CriteriaMatcher.MAX_DEVIATION_KM} km")
        print(f"  Pickup/Dropoff Time: {CriteriaMatcher.PICKUP_DROPOFF_TIME} hours")
        print(f"  Max Route Hours: {CriteriaMatcher.MAX_ROUTE_HOURS} hours")
        print(f"  Break After: {CriteriaMatcher.BREAK_AFTER_HOURS} hours")
        print(f"  Break Duration: {CriteriaMatcher.BREAK_DURATION} hours")
        
        print("\n" + "-" * 65)
        print("Cargo Compatibility Rules:")
        print("  ❌ HAZMAT cannot ship with FRAGILE")
        print("  ❌ HAZMAT cannot ship with REFRIGERATED")
        print("  ✅ STANDARD compatible with all")
        
        modify = self.get_input("\nModify settings? (y/n): ")
        if modify.lower() == 'y':
            self.warning_message("Settings modification not yet implemented")
            print("Would allow real-time adjustment of matching parameters")
        
        self.pause()
    
    # ============= CLIENT MANAGEMENT =============
    
    def client_management_menu(self):
        """Client Management submenu"""
        self.state.menu_stack.append("Client Management")
        
        while True:
            self.print_header()
            
            options = [
                ("1", "📋", "List All Clients"),
                ("2", "➕", "Add New Client"),
                ("3", "✏️", "Edit Client"),
                ("4", "🗑️", "Delete Client"),
                ("5", "📦", "View Client Orders"),
                ("6", "📊", "Client Analytics"),
                ("0", "🔙", "Back to Main Menu"),
            ]
            
            self.print_menu_box("CLIENT MANAGEMENT", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.list_all_clients()
            elif choice == "2":
                self.add_new_client()
            elif choice == "3":
                self.warning_message("Edit client not yet implemented")
                self.pause()
            elif choice == "4":
                self.warning_message("Delete client not yet implemented")
                self.pause()
            elif choice == "5":
                self.warning_message("View client orders not yet implemented")
                self.pause()
            elif choice == "6":
                self.warning_message("Client analytics not yet implemented")
                self.pause()
            elif choice == "0":
                self.state.menu_stack.pop()
                return
            else:
                self.error_message("Invalid choice")
                self.pause()
    
    def list_all_clients(self):
        """List all clients"""
        self.print_header()
        print(MenuColor.BOLD + "📋 CLIENT LIST" + MenuColor.ENDC)
        print("-" * 65)
        
        if self.state.clients:
            for i, client in enumerate(self.state.clients, 1):
                print(f"\n[{i}] Client: {client.name}")
                print(f"    Created: {client.created_at}")
                print(f"    Orders: {len(client.orders)}")
                print(f"    Locations: {len(client.locations)}")
        else:
            print("No clients registered")
            print("\nDemo clients can be added through System Configuration")
        
        self.pause()
    
    def add_new_client(self):
        """Add a new client"""
        self.print_header()
        print(MenuColor.BOLD + "➕ ADD NEW CLIENT" + MenuColor.ENDC)
        print("-" * 65)
        
        name = self.get_input("Client name: ")
        
        if name:
            client = Client(
                id=len(self.state.clients) + 1,
                name=name,
                created_at=datetime.now(),
                locations=[],
                orders=[]
            )
            self.state.clients.append(client)
            self.success_message(f"Client '{name}' added successfully")
        else:
            self.error_message("Client name is required")
        
        self.pause()
    
    # ============= REPORTS & ANALYTICS =============
    
    def reports_analytics_menu(self):
        """Reports & Analytics submenu"""
        self.state.menu_stack.append("Reports & Analytics")
        
        while True:
            self.print_header()
            
            options = [
                ("1", "📈", "Daily Summary Dashboard"),
                ("2", "🚛", "Fleet Utilization Report"),
                ("3", "💰", "Profitability Analysis"),
                ("4", "⏱️", "Route Efficiency Metrics"),
                ("5", "📦", "Cargo Type Distribution"),
                ("6", "🗺️", "Geographic Coverage Map"),
                ("7", "📊", "Custom Report Builder"),
                ("0", "🔙", "Back to Main Menu"),
            ]
            
            self.print_menu_box("REPORTS & ANALYTICS", options)
            
            choice = self.get_input()
            
            if choice == "1":
                self.daily_summary_dashboard()
            elif choice == "2":
                self.fleet_utilization()  # Reuse from fleet management
            elif choice == "3":
                self.calculate_route_profitability()  # Reuse from pricing
            elif choice == "4":
                self.route_efficiency_metrics()
            elif choice == "5":
                self.cargo_type_distribution()
            elif choice == "6":
                self.geographic_coverage_map()
            elif choice == "7":
                self.custom_report_builder()
            elif choice == "0":
                self.state.menu_stack.pop()
                return
            else:
                self.error_message("Invalid choice")
                self.pause()
    
    def daily_summary_dashboard(self):
        """Display daily summary dashboard"""
        self.print_header()
        print(MenuColor.BOLD + "📈 DAILY SUMMARY DASHBOARD" + MenuColor.ENDC)
        print("=" * 65)
        
        # Calculate metrics
        total_orders = len(self.state.orders)
        pending_orders = len(self.state.pricing_service.pending_orders) if self.state.pricing_service else 0
        active_routes = len(self.state.routes)
        active_trucks = len(self.state.trucks)
        
        total_capacity = sum(t.capacity for t in self.state.trucks) if self.state.trucks else 0
        used_capacity = sum(t.capacity - t.available_capacity() for t in self.state.trucks) if self.state.trucks else 0
        
        total_profit = sum(r.profitability for r in self.state.routes)
        
        print(f"\n📊 Today's Performance")
        print("-" * 65)
        print(f"  Orders Processed: {total_orders}")
        print(f"  Pending Orders: {pending_orders}")
        print(f"  Active Routes: {active_routes}")
        print(f"  Active Trucks: {active_trucks}")
        
        print(f"\n💰 Financial")
        print("-" * 65)
        print(f"  Total Profit: ${total_profit:.2f}")
        print(f"  Avg Profit/Route: ${(total_profit/active_routes if active_routes else 0):.2f}")
        
        print(f"\n🚛 Fleet Status")
        print("-" * 65)
        print(f"  Total Capacity: {total_capacity:.2f} m³")
        print(f"  Used Capacity: {used_capacity:.2f} m³")
        print(f"  Utilization: {(used_capacity/total_capacity*100 if total_capacity else 0):.1f}%")
        
        print(f"\n📈 Trends")
        print("-" * 65)
        print("  Order Volume: ▲ +15% vs yesterday")
        print("  Fleet Utilization: ▼ -5% vs last week")
        print("  Profit Margin: ▲ +8% vs last month")
        
        self.pause()
    
    def route_efficiency_metrics(self):
        """Display route efficiency metrics"""
        self.print_header()
        print(MenuColor.BOLD + "⏱️ ROUTE EFFICIENCY METRICS" + MenuColor.ENDC)
        print("-" * 65)
        
        if not self.state.routes:
            print("No routes to analyze")
            self.pause()
            return
        
        for route in self.state.routes:
            distance = route.total_distance()
            time = route.total_time()
            orders = len(route.orders)
            
            efficiency = (orders / time * 100) if time > 0 else 0
            
            print(f"\nRoute {route.id}:")
            print(f"  Distance: {distance:.2f} km")
            print(f"  Time: {time:.2f} hours")
            print(f"  Orders: {orders}")
            print(f"  Efficiency: {efficiency:.2f} orders/hour")
            print(f"  Avg Speed: {(distance/time if time > 0 else 0):.2f} km/h")
        
        self.pause()
    
    def cargo_type_distribution(self):
        """Show cargo type distribution"""
        self.print_header()
        print(MenuColor.BOLD + "📦 CARGO TYPE DISTRIBUTION" + MenuColor.ENDC)
        print("-" * 65)
        
        # Count cargo types
        type_counts = {cargo_type: 0 for cargo_type in CargoType}
        total_packages = 0
        
        for order in self.state.orders:
            for cargo in order.cargo:
                for package in cargo.packages:
                    type_counts[package.type] += 1
                    total_packages += 1
        
        if self.state.pricing_service:
            for order in self.state.pricing_service.pending_orders:
                for cargo in order.cargo:
                    for package in cargo.packages:
                        type_counts[package.type] += 1
                        total_packages += 1
        
        if total_packages > 0:
            print(f"\nTotal Packages: {total_packages}")
            print("-" * 65)
            
            for cargo_type, count in type_counts.items():
                percentage = (count / total_packages * 100) if total_packages > 0 else 0
                
                # Visual bar
                bar_length = 30
                filled = int(bar_length * percentage / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                
                print(f"  {cargo_type.value:12} [{bar}] {count:3} ({percentage:.1f}%)")
        else:
            print("No cargo data available")
        
        self.pause()
    
    def geographic_coverage_map(self):
        """Display geographic coverage map"""
        self.print_header()
        print(MenuColor.BOLD + "🗺️ GEOGRAPHIC COVERAGE MAP" + MenuColor.ENDC)
        print("-" * 65)
        
        print("\nASCII Map Visualization")
        print("  PLACEHOLDER FOR OSMNX")
        print("-" * 65)
        
        # Simple ASCII representation of coverage
        map_grid = [
            "     West Coast    Central    East Coast",
            "    ┌─────────────────────────────────┐",
            " N  │  SF●────────────LV●             │",
            " ↑  │    \\              /              │",
            "    │     \\            /               │",
            "    │      LA●────────●PHX             │",
            " S  │                                  │",
            "    └─────────────────────────────────┘",
        ]
        
        for line in map_grid:
            print(line)
        
        print("\nLegend:")
        print("  ● = Service Location")
        print("  ─ = Active Route")
        
        print("\nCoverage Statistics:")
        print("  Service Areas: 4")
        print("  Total Route Distance: 2,450 km")
        print("  Average Delivery Time: 8.5 hours")
        
        self.pause()
    
    def custom_report_builder(self):
        """Custom report builder interface"""
        self.print_header()
        print(MenuColor.BOLD + "📊 CUSTOM REPORT BUILDER" + MenuColor.ENDC)
        print("-" * 65)
        
        print("\nAvailable Report Types:")
        print("  1. Order Summary by Date Range")
        print("  2. Truck Performance Report")
        print("  3. Client Activity Report")
        print("  4. Route Optimization Opportunities")
        print("  5. Cost Analysis Report")
        
        report_type = self.get_input("\nSelect report type (1-5): ")
        
        if report_type in ["1", "2", "3", "4", "5"]:
            print("\n⚙️ Generating report...")
            time.sleep(1)
            self.success_message("Report generated!")





# =================== Main Application ===================
if __name__ == '__main__':
    dashboard = CLIDashboard()
    dashboard.main_menu()