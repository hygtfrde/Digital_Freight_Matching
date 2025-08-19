"""
dashboard.py - Dashboard and CLI Interface for Digital Freight Matching System
Integrates with navigation.py for menu management
"""

"""
+-------------------------------------------------------+
|                 🚛 Dashboard Methods                  |
+-------------------+------------------+----------------+
|   Trucks          |   Routes         |   Orders       |
|-------------------|------------------|----------------|
| [ List Trucks ]   | [ List Routes ]  | [ List Orders ]|
| [ Add Truck ]     | [ Add Route ]    | [ Add Order ]  |
| [ Edit Truck ]    | [ Edit Route ]   | [ Edit Order ] |
| [ Delete Truck ]  | [ Delete Route ] | [ Delete Order]|
| [ View Loads ]    | [ Assign Truck ] | [ Match Order ]|
+-------------------+------------------+----------------+
|   Clients         |   Locations      |   Packages     |
|-------------------|------------------|----------------|
| [ List Clients ]  | [ List Loc.  ]   | [ List Pkg.  ] |
| [ Add Client ]    | [ Add Loc.   ]   | [ Add Pkg.   ] |
| [ Edit Client ]   | [ Edit Loc.  ]   | [ Edit Pkg.  ] |
| [ Delete Client ] | [ Delete Loc. ]  | [ Delete Pkg.] |
| [ View Orders ]   | [ View Routes]   | [ Assign to  ] |
|                   |                  |   Cargo        |
+-------------------+------------------+----------------+
|   Cargo           |   Pricing/Match  |   Dashboard    |
|-------------------|------------------|----------------|
| [ List Cargo  ]   | [ Price Route ]  |  [Summary]     |
| [ Add Cargo   ]   | [ Match Order ]  |  [KPIs]        |
| [ Edit Cargo  ]   | [ Profitability] |  [Pending]     |
| [ Delete Cargo]   | [ New Route   ]  |  [Utilization] |
| [ Assign Pkg. ]   |                  |  [Alerts]      |
+-------------------------------------------------------+
"""


from dfm import (
    CargoType, Location, Package, Cargo, Order, Client,
    Truck, Route, PricingService, CriteriaMatcher
)
from navigation import (
    MenuSystem, Menu, MenuItem, MenuLevel, 
    create_crud_menu, create_report_menu
)
from utils import pretty_print_order
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import os


class DFMDashboard:
    """Main dashboard controller for the Digital Freight Matching system"""
    
    def __init__(self):
        """Initialize the dashboard with menu system and data"""
        self.menu_system = MenuSystem()
        
        # Initialize data stores
        self.orders: List[Order] = []
        self.trucks: List[Truck] = []
        self.routes: List[Route] = []
        self.clients: List[Client] = []
        self.pricing_service: Optional[PricingService] = None
        
        # Initialize demo data flag
        self.has_demo_data = False
        
        # Setup menus
        self.setup_menus()
        
        # Set data context for menu system
        self.update_menu_context()
    
    def update_menu_context(self):
        """Update the menu system's data context"""
        self.menu_system.set_data_context({
            'orders': self.orders,
            'trucks': self.trucks,
            'routes': self.routes,
            'clients': self.clients,
            'pricing_service': self.pricing_service
        })
    
    def setup_menus(self):
        """Setup all menu structures"""
        # Create main menu
        main_menu = Menu(
            name="Main",
            title="🚛 DIGITAL FREIGHT MATCHING SYSTEM",
            level=MenuLevel.MAIN
        )
        
        # Create submenus
        order_menu = self.create_order_menu()
        fleet_menu = self.create_fleet_menu()
        route_menu = self.create_route_menu()
        pricing_menu = self.create_pricing_menu()
        client_menu = create_crud_menu("clients", "Client", "👥")
        report_menu = create_report_menu()
        config_menu = self.create_config_menu()
        
        # Add items to main menu
        main_menu.add_item(MenuItem("1", "Order Management", icon="📦", submenu=order_menu))
        main_menu.add_item(MenuItem("2", "Fleet Management", icon="🚛", submenu=fleet_menu))
        main_menu.add_item(MenuItem("3", "Route Management", icon="🗺️", submenu=route_menu))
        main_menu.add_item(MenuItem("4", "Pricing & Matching", icon="💰", submenu=pricing_menu))
        main_menu.add_item(MenuItem("5", "Client Management", icon="👥", submenu=client_menu))
        main_menu.add_item(MenuItem("6", "Reports & Analytics", icon="📊", submenu=report_menu))
        main_menu.add_item(MenuItem("7", "System Configuration", icon="⚙️", submenu=config_menu))
        main_menu.add_item(MenuItem("8", "Quick Search", icon="🔍", action=self.quick_search))
        main_menu.add_item(MenuItem("9", "Run Demo", icon="🎮", action=self.run_demo))
        main_menu.add_item(MenuItem("0", "Exit", icon="❌", action=self.exit_program))
        
        self.main_menu = main_menu
    
    def create_order_menu(self) -> Menu:
        """Create the order management menu"""
        menu = Menu(
            name="Orders",
            title="📦 ORDER MANAGEMENT",
            level=MenuLevel.SUB
        )
        
        menu.add_item(MenuItem("1", "List All Orders", icon="📋", action=self.list_orders))
        menu.add_item(MenuItem("2", "Add New Order", icon="➕", action=self.add_order))
        menu.add_item(MenuItem("3", "View Order Details", icon="🔍", action=self.view_order_details))
        menu.add_item(MenuItem("4", "Edit Order", icon="✏️", action=self.edit_order))
        menu.add_item(MenuItem("5", "Delete Order", icon="🗑️", action=self.delete_order, requires_confirm=True))
        menu.add_item(MenuItem("6", "Match Order to Route", icon="🎯", action=self.match_single_order))
        menu.add_item(MenuItem("7", "View Pending Orders", icon="⏳", action=self.view_pending_orders))
        menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
        
        return menu
    
    def create_fleet_menu(self) -> Menu:
        """Create the fleet management menu"""
        menu = Menu(
            name="Fleet",
            title="🚛 FLEET MANAGEMENT",
            level=MenuLevel.SUB
        )
        
        menu.add_item(MenuItem("1", "List All Trucks", icon="📋", action=self.list_trucks))
        menu.add_item(MenuItem("2", "Add New Truck", icon="➕", action=self.add_truck))
        menu.add_item(MenuItem("3", "View Truck Details", icon="🔍", action=self.view_truck_details))
        menu.add_item(MenuItem("4", "Edit Truck", icon="✏️", action=self.edit_truck))
        menu.add_item(MenuItem("5", "Delete Truck", icon="🗑️", action=self.delete_truck, requires_confirm=True))
        menu.add_item(MenuItem("6", "View Truck Loads", icon="📦", action=self.view_truck_loads))
        menu.add_item(MenuItem("7", "Fleet Utilization", icon="📊", action=self.fleet_utilization))
        menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
        
        return menu
    
    def create_route_menu(self) -> Menu:
        """Create the route management menu"""
        menu = Menu(
            name="Routes",
            title="🗺️ ROUTE MANAGEMENT",
            level=MenuLevel.SUB
        )
        
        menu.add_item(MenuItem("1", "List All Routes", icon="📋", action=self.list_routes))
        menu.add_item(MenuItem("2", "Add New Route", icon="➕", action=self.add_route))
        menu.add_item(MenuItem("3", "View Route Details", icon="🔍", action=self.view_route_details))
        menu.add_item(MenuItem("4", "Edit Route", icon="✏️", action=self.edit_route))
        menu.add_item(MenuItem("5", "Delete Route", icon="🗑️", action=self.delete_route, requires_confirm=True))
        menu.add_item(MenuItem("6", "Optimize Route", icon="⚡", action=self.optimize_route))
        menu.add_item(MenuItem("7", "View Route Path", icon="🗺️", action=self.view_route_path))
        menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
        
        return menu
    
    def create_pricing_menu(self) -> Menu:
        """Create the pricing and matching menu"""
        menu = Menu(
            name="Pricing",
            title="💰 PRICING & MATCHING",
            level=MenuLevel.SUB
        )
        
        menu.add_item(MenuItem("1", "Auto-Match All Orders", icon="🎯", action=self.auto_match_orders))
        menu.add_item(MenuItem("2", "View Pending Orders", icon="📋", action=self.view_pending_orders))
        menu.add_item(MenuItem("3", "Process Pending Queue", icon="🔄", action=self.process_pending))
        menu.add_item(MenuItem("4", "Calculate Route Profitability", icon="💵", action=self.calculate_profitability))
        menu.add_item(MenuItem("5", "Create Route from Pending", icon="🆕", action=self.create_route_from_pending))
        menu.add_item(MenuItem("6", "Matching Statistics", icon="📊", action=self.matching_stats))
        menu.add_item(MenuItem("7", "Configure Matching Rules", icon="⚙️", action=self.configure_matching))
        menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
        
        return menu
    
    def create_config_menu(self) -> Menu:
        """Create the system configuration menu"""
        menu = Menu(
            name="Config",
            title="⚙️ SYSTEM CONFIGURATION",
            level=MenuLevel.SUB
        )
        
        menu.add_item(MenuItem("1", "Load Demo Data", icon="🎮", action=self.load_demo_data))
        menu.add_item(MenuItem("2", "Clear All Data", icon="🗑️", action=self.clear_all_data, requires_confirm=True))
        menu.add_item(MenuItem("3", "Import from File", icon="📥", action=self.import_data))
        menu.add_item(MenuItem("4", "Export to File", icon="📤", action=self.export_data))
        menu.add_item(MenuItem("5", "Database Settings", icon="🗄️", action=self.database_settings))
        menu.add_item(MenuItem("6", "Matching Parameters", icon="🎛️", action=self.matching_parameters))
        menu.add_item(MenuItem("7", "System Info", icon="ℹ️", action=self.system_info))
        menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
        
        return menu
    
    # ============= Action Methods =============
    
    def list_orders(self):
        """List all orders with pagination"""
        if not self.orders:
            print("\n📭 No orders found.")
            input("\nPress Enter to continue...")
            return
        
        def format_order(order):
            print(f"Pickup: ({order.pickup.latitude:.4f}, {order.pickup.longitude:.4f})")
            print(f"  Dropoff: ({order.dropoff.latitude:.4f}, {order.dropoff.longitude:.4f})")
            print(f"  Packages: {len(order.cargo.packages)}")
            print(f"  Volume: {order.cargo.total_volume():.2f}, Weight: {order.cargo.total_weight():.2f}")
        
        self.menu_system.paginated_display(self.orders, format_order)
    
    def add_order(self):
        """Add a new order through wizard"""
        print("\n➕ ADD NEW ORDER")
        print("-" * 50)
        
        try:
            # Get pickup location
            print("\n📍 Pickup Location:")
            pickup_lat = float(input("  Latitude: "))
            pickup_lon = float(input("  Longitude: "))
            
            # Get dropoff location
            print("\n📍 Dropoff Location:")
            dropoff_lat = float(input("  Latitude: "))
            dropoff_lon = float(input("  Longitude: "))
            
            # Get packages
            packages = []
            while True:
                print(f"\n📦 Package {len(packages) + 1}:")
                volume = float(input("  Volume: "))
                weight = float(input("  Weight: "))
                
                print("  Cargo Type:")
                for i, cargo_type in enumerate(CargoType, 1):
                    print(f"    {i}. {cargo_type.value}")
                type_choice = int(input("  Select type (1-4): "))
                cargo_type = list(CargoType)[type_choice - 1]
                
                packages.append(Package(volume, weight, cargo_type))
                
                add_more = input("\n  Add another package? (y/n): ").lower()
                if add_more != 'y':
                    break
            
            # Create order
            order = Order(
                cargo=Cargo(packages),
                pickup=Location(pickup_lat, pickup_lon),
                dropoff=Location(dropoff_lat, dropoff_lon)
            )
            
            self.orders.append(order)
            self.update_menu_context()
            
            print("\n✅ Order added successfully!")
            print(f"Total packages: {len(packages)}")
            print(f"Total volume: {order.cargo.total_volume():.2f}")
            print(f"Total weight: {order.cargo.total_weight():.2f}")
            
        except ValueError as e:
            print(f"\n❌ Invalid input: {e}")
        except Exception as e:
            print(f"\n❌ Error adding order: {e}")
        
        input("\nPress Enter to continue...")
    
    def view_order_details(self):
        """View detailed information about a specific order"""
        if not self.orders:
            print("\n📭 No orders to view.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🔍 VIEW ORDER DETAILS")
        print("-" * 50)
        
        for i, order in enumerate(self.orders, 1):
            print(f"{i}. Order from ({order.pickup.latitude:.2f}, {order.pickup.longitude:.2f}) "
                  f"to ({order.dropoff.latitude:.2f}, {order.dropoff.longitude:.2f})")
        
        try:
            choice = int(input("\nSelect order number: ")) - 1
            if 0 <= choice < len(self.orders):
                order = self.orders[choice]
                print("\n" + "=" * 50)
                pretty_print_order(order)
                print("=" * 50)
            else:
                print("\n❌ Invalid order number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def edit_order(self):
        """Edit an existing order"""
        print("\n✏️ EDIT ORDER - Not yet implemented")
        input("\nPress Enter to continue...")
    
    def delete_order(self):
        """Delete an order"""
        if not self.orders:
            print("\n📭 No orders to delete.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🗑️ DELETE ORDER")
        print("-" * 50)
        
        for i, order in enumerate(self.orders, 1):
            print(f"{i}. Order from ({order.pickup.latitude:.2f}, {order.pickup.longitude:.2f}) "
                  f"to ({order.dropoff.latitude:.2f}, {order.dropoff.longitude:.2f})")
        
        try:
            choice = int(input("\nSelect order to delete: ")) - 1
            if 0 <= choice < len(self.orders):
                self.orders.pop(choice)
                self.update_menu_context()
                print("\n✅ Order deleted successfully!")
            else:
                print("\n❌ Invalid order number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def match_single_order(self):
        """Match a single order to a route"""
        if not self.orders:
            print("\n📭 No orders to match.")
            input("\nPress Enter to continue...")
            return
        
        if not self.pricing_service:
            print("\n❌ Pricing service not initialized. Please load demo data first.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🎯 MATCH ORDER TO ROUTE")
        print("-" * 50)
        
        for i, order in enumerate(self.orders, 1):
            print(f"{i}. Order from ({order.pickup.latitude:.2f}, {order.pickup.longitude:.2f}) "
                  f"to ({order.dropoff.latitude:.2f}, {order.dropoff.longitude:.2f})")
        
        try:
            choice = int(input("\nSelect order to match: ")) - 1
            if 0 <= choice < len(self.orders):
                order = self.orders[choice]
                match = self.pricing_service.match_order(order)
                
                if match:
                    route, truck = match
                    print(f"\n✅ Order matched to Route {self.routes.index(route) + 1} "
                          f"with Truck {self.trucks.index(truck) + 1}")
                else:
                    print("\n❌ No suitable route found. Order added to pending queue.")
                    self.pricing_service.pending_orders.append(order)
            else:
                print("\n❌ Invalid order number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def view_pending_orders(self):
        """View all pending orders"""
        if not self.pricing_service or not self.pricing_service.pending_orders:
            print("\n📭 No pending orders.")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n⏳ PENDING ORDERS ({len(self.pricing_service.pending_orders)} total)")
        print("=" * 50)
        
        for i, order in enumerate(self.pricing_service.pending_orders, 1):
            print(f"\n[{i}]")
            pretty_print_order(order, indent=2)
        
        input("\nPress Enter to continue...")
    
    # Fleet Management Actions
    
    def list_trucks(self):
        """List all trucks"""
        if not self.trucks:
            print("\n🚛 No trucks in fleet.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🚛 FLEET INVENTORY")
        print("-" * 50)
        
        for i, truck in enumerate(self.trucks, 1):
            print(f"\n[{i}] Truck Type: {truck.type}")
            print(f"    Autonomy: {truck.autonomy} km")
            print(f"    Capacity: {truck.capacity} m³")
            print(f"    Available: {truck.available_capacity():.2f} m³")
            print(f"    Cargo loads: {len(truck.cargo)}")
        
        input("\nPress Enter to continue...")
    
    def add_truck(self):
        """Add a new truck to the fleet"""
        print("\n➕ ADD NEW TRUCK")
        print("-" * 50)
        
        try:
            truck_type = input("Truck type (standard/refrigerated/hazmat): ").lower()
            autonomy = float(input("Autonomy (km): "))
            capacity = float(input("Capacity (m³): "))
            
            truck = Truck(autonomy, capacity, truck_type)
            self.trucks.append(truck)
            self.update_menu_context()
            
            print(f"\n✅ {truck_type.capitalize()} truck added to fleet!")
            
        except ValueError:
            print("\n❌ Invalid input. Please enter valid numbers.")
        except Exception as e:
            print(f"\n❌ Error adding truck: {e}")
        
        input("\nPress Enter to continue...")
    
    def view_truck_details(self):
        """View detailed truck information"""
        if not self.trucks:
            print("\n🚛 No trucks to view.")
            input("\nPress Enter to continue...")
            return
        
        self.list_trucks()
        
        try:
            choice = int(input("\nSelect truck number for details: ")) - 1
            if 0 <= choice < len(self.trucks):
                truck = self.trucks[choice]
                print("\n" + "=" * 50)
                print(f"TRUCK DETAILS")
                print("=" * 50)
                print(f"Type: {truck.type}")
                print(f"Autonomy: {truck.autonomy} km")
                print(f"Total Capacity: {truck.capacity} m³")
                print(f"Used Capacity: {truck.capacity - truck.available_capacity():.2f} m³")
                print(f"Available Capacity: {truck.available_capacity():.2f} m³")
                print(f"\nCargo Loads ({len(truck.cargo)}):")
                for i, cargo in enumerate(truck.cargo, 1):
                    print(f"  {i}. Volume: {cargo.total_volume():.2f} m³, "
                          f"Weight: {cargo.total_weight():.2f} kg")
            else:
                print("\n❌ Invalid truck number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def edit_truck(self):
        """Edit truck details"""
        print("\n✏️ EDIT TRUCK - Not yet implemented")
        input("\nPress Enter to continue...")
    
    def delete_truck(self):
        """Delete a truck from the fleet"""
        if not self.trucks:
            print("\n🚛 No trucks to delete.")
            input("\nPress Enter to continue...")
            return
        
        self.list_trucks()
        
        try:
            choice = int(input("\nSelect truck to delete: ")) - 1
            if 0 <= choice < len(self.trucks):
                self.trucks.pop(choice)
                self.update_menu_context()
                print("\n✅ Truck removed from fleet!")
            else:
                print("\n❌ Invalid truck number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def view_truck_loads(self):
        """View current loads for all trucks"""
        if not self.trucks:
            print("\n🚛 No trucks in fleet.")
            input("\nPress Enter to continue...")
            return
        
        print("\n📦 TRUCK LOADS")
        print("=" * 50)
        
        for i, truck in enumerate(self.trucks, 1):
            print(f"\nTruck {i} ({truck.type}):")
            if truck.cargo:
                for j, cargo in enumerate(truck.cargo, 1):
                    print(f"  Load {j}: {cargo.total_volume():.2f} m³, {cargo.total_weight():.2f} kg")
                print(f"  Total: {truck.capacity - truck.available_capacity():.2f}/{truck.capacity} m³")
            else:
                print("  No cargo loaded")
        
        input("\nPress Enter to continue...")
    
    def fleet_utilization(self):
        """Show fleet utilization statistics"""
        if not self.trucks:
            print("\n🚛 No trucks in fleet.")
            input("\nPress Enter to continue...")
            return
        
        print("\n📊 FLEET UTILIZATION")
        print("=" * 50)
        
        total_capacity = sum(t.capacity for t in self.trucks)
        used_capacity = sum(t.capacity - t.available_capacity() for t in self.trucks)
        utilization = (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
        
        print(f"\nFleet Size: {len(self.trucks)} trucks")
        print(f"Total Capacity: {total_capacity:.2f} m³")
        print(f"Used Capacity: {used_capacity:.2f} m³")
        print(f"Available Capacity: {total_capacity - used_capacity:.2f} m³")
        print(f"Utilization Rate: {utilization:.1f}%")
        
        print("\n" + "Utilization Bar:")
        bar_length = 40
        filled = int(bar_length * utilization / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"[{bar}] {utilization:.1f}%")
        
        input("\nPress Enter to continue...")
    
    # Route Management Actions
    
    def list_routes(self):
        """List all routes"""
        if not self.routes:
            print("\n🗺️ No routes defined.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🗺️ ROUTE INVENTORY")
        print("-" * 50)
        
        for i, route in enumerate(self.routes, 1):
            print(f"\n[{i}] Route:")
            print(f"    Origin: ({route.origin.latitude:.2f}, {route.origin.longitude:.2f})")
            print(f"    Destination: ({route.destiny.latitude:.2f}, {route.destiny.longitude:.2f})")
            print(f"    Path points: {len(route.path)}")
            print(f"    Orders: {len(route.orders)}")
            print(f"    Distance: {route.total_distance():.2f} km")
            print(f"    Profitability: ${route.profitability:.2f}")
        
        input("\nPress Enter to continue...")
    
    def add_route(self):
        """Add a new route"""
        print("\n➕ ADD NEW ROUTE")
        print("-" * 50)
        
        try:
            print("\n📍 Origin:")
            origin_lat = float(input("  Latitude: "))
            origin_lon = float(input("  Longitude: "))
            
            print("\n📍 Destination:")
            dest_lat = float(input("  Latitude: "))
            dest_lon = float(input("  Longitude: "))
            
            # Create basic route
            route = Route(
                origin=Location(origin_lat, origin_lon),
                destiny=Location(dest_lat, dest_lon),
                path=[Location(origin_lat, origin_lon), Location(dest_lat, dest_lon)]
            )
            
            self.routes.append(route)
            self.update_menu_context()
            
            print(f"\n✅ Route added successfully!")
            print(f"Distance: {route.total_distance():.2f} km")
            
        except ValueError:
            print("\n❌ Invalid input. Please enter valid numbers.")
        except Exception as e:
            print(f"\n❌ Error adding route: {e}")
        
        input("\nPress Enter to continue...")
    
    def view_route_details(self):
        """View detailed route information"""
        if not self.routes:
            print("\n🗺️ No routes to view.")
            input("\nPress Enter to continue...")
            return
        
        self.list_routes()
        
        try:
            choice = int(input("\nSelect route number for details: ")) - 1
            if 0 <= choice < len(self.routes):
                route = self.routes[choice]
                print("\n" + "=" * 50)
                print("ROUTE DETAILS")
                print("=" * 50)
                print(f"Origin: ({route.origin.latitude:.4f}, {route.origin.longitude:.4f})")
                print(f"Destination: ({route.destiny.latitude:.4f}, {route.destiny.longitude:.4f})")
                print(f"Total Distance: {route.total_distance():.2f} km")
                print(f"Estimated Time: {route.total_time():.2f} hours")
                print(f"Profitability: ${route.profitability:.2f}")
                print(f"\nPath Points ({len(route.path)}):")
                for i, point in enumerate(route.path, 1):
                    print(f"  {i}. ({point.latitude:.4f}, {point.longitude:.4f})")
                print(f"\nOrders ({len(route.orders)}):")
                for i, order in enumerate(route.orders, 1):
                    print(f"  {i}. {order.cargo.total_volume():.2f} m³")
            else:
                print("\n❌ Invalid route number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def edit_route(self):
        """Edit route details"""
        print("\n✏️ EDIT ROUTE - Not yet implemented")
        input("\nPress Enter to continue...")
    
    def delete_route(self):
        """Delete a route"""
        if not self.routes:
            print("\n🗺️ No routes to delete.")
            input("\nPress Enter to continue...")
            return
        
        self.list_routes()
        
        try:
            choice = int(input("\nSelect route to delete: ")) - 1
            if 0 <= choice < len(self.routes):
                self.routes.pop(choice)
                self.update_menu_context()
                print("\n✅ Route deleted successfully!")
            else:
                print("\n❌ Invalid route number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    def optimize_route(self):
        """Optimize a route"""
        print("\n⚡ OPTIMIZE ROUTE - Not yet implemented")
        print("This will reorder waypoints for efficiency")
        input("\nPress Enter to continue...")
    
    def view_route_path(self):
        """View route path visualization"""
        if not self.routes:
            print("\n🗺️ No routes to visualize.")
            input("\nPress Enter to continue...")
            return
        
        self.list_routes()
        
        try:
            choice = int(input("\nSelect route to visualize: ")) - 1
            if 0 <= choice < len(self.routes):
                route = self.routes[choice]
                print("\n" + "=" * 50)
                print("ROUTE PATH VISUALIZATION")
                print("=" * 50)
                
                # Simple ASCII visualization
                print("\n  START")
                for i, point in enumerate(route.path):
                    if i == 0:
                        print(f"    📍 Origin: ({point.latitude:.2f}, {point.longitude:.2f})")
                    elif i == len(route.path) - 1:
                        print(f"    📍 Destination: ({point.latitude:.2f}, {point.longitude:.2f})")
                    else:
                        print(f"    ↓  Waypoint {i}: ({point.latitude:.2f}, {point.longitude:.2f})")
                print("  END")
                
                print(f"\nTotal Distance: {route.total_distance():.2f} km")
            else:
                print("\n❌ Invalid route number")
        except ValueError:
            print("\n❌ Please enter a valid number")
        
        input("\nPress Enter to continue...")
    
    # Pricing & Matching Actions
    
    def auto_match_orders(self):
        """Automatically match all orders to routes"""
        if not self.pricing_service:
            print("\n❌ Pricing service not initialized. Please load demo data first.")
            input("\nPress Enter to continue...")
            return
        
        if not self.orders:
            print("\n📭 No orders to match.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🎯 AUTO-MATCHING ORDERS")
        print("=" * 50)
        
        matched = 0
        pending = 0
        
        for order in self.orders:
            result = self.pricing_service.process_order({
                'cargo': {
                    'packages': [
                        (p.volume, p.weight, p.type.value)
                        for p in order.cargo.packages
                    ]
                },
                'pick-up': {
                    'latitude': order.pickup.latitude,
                    'longitude': order.pickup.longitude
                },
                'drop-off': {
                    'latitude': order.dropoff.latitude,
                    'longitude': order.dropoff.longitude
                }
            })
            
            if result['status'] == 'matched':
                matched += 1
                print(f"✅ Order matched to Route {result['route']}, Truck {result['truck']}")
            else:
                pending += 1
                print(f"⏳ Order added to pending queue: {result['reason']}")
        
        print("\n" + "-" * 50)
        print(f"Results: {matched} matched, {pending} pending")
        
        input("\nPress Enter to continue...")
    
    def process_pending(self):
        """Process pending order queue"""
        if not self.pricing_service or not self.pricing_service.pending_orders:
            print("\n📭 No pending orders to process.")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n🔄 PROCESSING {len(self.pricing_service.pending_orders)} PENDING ORDERS")
        print("=" * 50)
        
        # Try to create new route from pending
        new_route = self.pricing_service.create_new_route_from_pending()
        
        if new_route:
            print("\n✅ Created new route from pending orders!")
            self.routes.append(new_route)
            self.update_menu_context()
        else:
            print("\n❌ Unable to create route. Need at least 2 pending orders.")
        
        input("\nPress Enter to continue...")
    
    def calculate_profitability(self):
        """Calculate profitability for routes"""
        if not self.routes:
            print("\n🗺️ No routes to analyze.")
            input("\nPress Enter to continue...")
            return
        
        print("\n💵 ROUTE PROFITABILITY ANALYSIS")
        print("=" * 50)
        
        cost_per_mile = 1.5
        revenue_per_order = 50.0
        
        total_profit = 0
        for i, route in enumerate(self.routes, 1):
            profit = CriteriaMatcher.calculate_route_profitability(
                route, cost_per_mile, revenue_per_order
            )
            route.profitability = profit
            total_profit += profit
            
            print(f"\nRoute {i}:")
            print(f"  Distance: {route.total_distance():.2f} km")
            print(f"  Orders: {len(route.orders)}")
            print(f"  Revenue: ${len(route.orders) * revenue_per_order:.2f}")
            print(f"  Cost: ${route.total_distance() * 0.621371 * cost_per_mile:.2f}")
            print(f"  Profit: ${profit:.2f}")
        
        print("\n" + "-" * 50)
        print(f"Total Profit: ${total_profit:.2f}")
        
        input("\nPress Enter to continue...")
    
    def create_route_from_pending(self):
        """Create new route from pending orders"""
        if not self.pricing_service:
            print("\n❌ Pricing service not initialized.")
            input("\nPress Enter to continue...")
            return
        
        print("\n🆕 CREATE ROUTE FROM PENDING ORDERS")
        print("This feature will analyze pending orders and create optimal routes.")
        print("Not yet fully implemented.")
        
        input("\nPress Enter to continue...")
    
    def matching_stats(self):
        """Show matching statistics"""
        if not self.pricing_service:
            print("\n❌ Pricing service not initialized.")
            input("\nPress Enter to continue...")
            return
        
        print("\n📊 MATCHING STATISTICS")
        print("=" * 50)
        
        total_orders = len(self.orders)
        pending_orders = len(self.pricing_service.pending_orders) if self.pricing_service else 0
        matched_orders = total_orders - pending_orders
        
        print(f"\nTotal Orders: {total_orders}")
        print(f"Matched Orders: {matched_orders}")
        print(f"Pending Orders: {pending_orders}")
        
        if total_orders > 0:
            match_rate = (matched_orders / total_orders) * 100
            print(f"Match Rate: {match_rate:.1f}%")
            
            # Visual bar
            bar_length = 40
            filled = int(bar_length * match_rate / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\n[{bar}] {match_rate:.1f}%")
        
        input("\nPress Enter to continue...")
    
    def configure_matching(self):
        """Configure matching rules and parameters"""
        print("\n⚙️ MATCHING CONFIGURATION")
        print("=" * 50)
        
        print(f"\nCurrent Settings:")
        print(f"  Max Deviation: {CriteriaMatcher.MAX_DEVIATION_KM} km")
        print(f"  Pickup/Dropoff Time: {CriteriaMatcher.PICKUP_DROPOFF_TIME} hours")
        print(f"  Max Route Hours: {CriteriaMatcher.MAX_ROUTE_HOURS} hours")
        print(f"  Break After: {CriteriaMatcher.BREAK_AFTER_HOURS} hours")
        print(f"  Break Duration: {CriteriaMatcher.BREAK_DURATION} hours")
        
        print("\nModify settings? (Not yet implemented)")
        
        input("\nPress Enter to continue...")
    
    # System Configuration Actions
    


    def clear_all_data(self):
        """Clear all data from the system"""
        print("Are you sure‼? This will remove all orders, trucks, routes, and demo data.")
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        if confirm != 'yes':
            print("\n❌ Action cancelled.")
            input("\nPress Enter to continue...")
            return
        print("\n🗑️ CLEARING ALL DATA")
        print("-" * 50)
        self.orders.clear()
        self.trucks.clear()
        self.routes.clear()
        self.clients.clear()
        self.pricing_service = None
        self.has_demo_data = False
        self.update_menu_context()
        
        print("\n✅ All data cleared successfully!")
        input("\nPress Enter to continue...")
    
    def import_data(self):
        """Import data from file"""
        print("\n📥 IMPORT DATA")
        filename = input("Enter filename (JSON): ")
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Process imported data (simplified)
            print(f"\n✅ Data imported from {filename}")
            
        except FileNotFoundError:
            print(f"\n❌ File {filename} not found")
        except json.JSONDecodeError:
            print(f"\n❌ Invalid JSON in {filename}")
        except Exception as e:
            print(f"\n❌ Error importing: {e}")
        
        input("\nPress Enter to continue...")
    
    def export_data(self):
        """Export data to file"""
        print("\n📤 EXPORT DATA")
        filename = input("Enter filename (JSON): ")
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'orders': len(self.orders),
                'trucks': len(self.trucks),
                'routes': len(self.routes)
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n✅ Data exported to {filename}")
            
        except Exception as e:
            print(f"\n❌ Error exporting: {e}")
        
        input("\nPress Enter to continue...")
    
