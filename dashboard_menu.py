"""
========== DASHBOARD MENU ==========

User Input → Validation → Business Logic (DFM) → Database → Feedback
     ↑                                                        │
     └────────────────────────────────────────────────────────┘

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

from dfm import (
    CargoType, Location, Package, Cargo, Order, Client,
    Truck, Route, PricingService
)
from typing import List



"""
dashboard.py - Dashboard and CLI Interface for Digital Freight Matching System
Integrates with navigation.py for menu management
"""

from dfm import (
    CargoType, Location, Package, Cargo, Order, Client,
    Truck, Route, PricingService, CriteriaMatcher
)
from navigation import (
    MenuSystem, Menu, MenuItem, MenuLevel, 
    create_crud_menu, create_report_menu
)
from typing import List, Optional, Dict, Any
import json
from datetime import datetime


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