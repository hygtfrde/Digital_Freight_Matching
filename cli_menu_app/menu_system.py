"""
Menu System for CLI Menu Application
Handles menu display, navigation, and routing
"""

import sys

from ui_components import (
    print_header, print_menu_box, get_input, pause, print_success, 
    print_error, print_info, format_table_data, Colors
)
from crud_operations import CRUDOperations


class MenuSystem:
    """Handles all menu navigation and display logic"""
    
    def __init__(self, data_service):
        self.data_service = data_service
        self.crud_ops = CRUDOperations(data_service)
        self.running = True
        self.current_menu = "main"
        self.menu_stack = ["Main"]
    
    def show_main_menu(self):
        """Display main menu"""
        print_header(self.data_service, self.menu_stack)
        
        options = [
            ("1", "🗄️", "Database Management"),
            ("2", "🏢", "Entity Management"),
            ("3", "📊", "System Status & Reports"),
            ("4", "⚙️", "System Operations"),
            ("5", "🔍", "Quick Database Check"),
            ("0", "❌", "Exit")
        ]
        
        print_menu_box("MAIN MENU", options)
    
    def show_entity_management_menu(self):
        """Display entity management menu"""
        print_header(self.data_service, self.menu_stack)
        
        options = [
            ("1", "🚛", "Trucks"),
            ("2", "📦", "Orders"),
            ("3", "📍", "Locations"),
            ("4", "🛣️", "Routes"),
            ("5", "👥", "Clients"),
            ("6", "📦", "Packages"),
            ("7", "🚚", "Cargo"),
            ("0", "↩️", "Back to Main Menu")
        ]
        
        print_menu_box("ENTITY MANAGEMENT", options)
    
    def show_database_management_menu(self):
        """Display database management menu"""
        print_header(self.data_service, self.menu_stack)
        
        options = [
            ("1", "📊", "Show Table Statistics"),
            ("2", "🔧", "Database Operations"),
            ("3", "📋", "List All Tables"),
            ("4", "🔍", "Search Database"),
            ("0", "↩️", "Back to Main Menu")
        ]
        
        print_menu_box("DATABASE MANAGEMENT", options)
    
    def show_system_status(self):
        """Show system status and reports"""
        try:
            print_header(self.data_service, self.menu_stack)
            
            print("📊 System Status Report")
            print("=" * 50)
            
            # Health check
            health = self.data_service.health_check()
            if health["status"] == "healthy":
                print_success(f"System Status: {health['message']}")
            else:
                print_error(f"System Status: {health['message']}")
            
            print()
            
            # Get system status
            status = self.data_service.get_system_status()
            
            if isinstance(status, dict):
                # API mode returns dict
                print("📈 Entity Counts:")
                print("-" * 20)
                for entity, count in status.items():
                    if entity != 'status':
                        print(f"{entity.replace('_', ' ').title()}: {count}")
            else:
                # Direct mode returns object with attributes
                print("📈 System Statistics:")
                print("-" * 25)
                print(f"Total Routes: {getattr(status, 'total_routes', 'N/A')}")
                print(f"Active Trucks: {getattr(status, 'trucks', 'N/A')}")
                print(f"Total Orders: {getattr(status, 'orders', 'N/A')}")
                print(f"Locations: {getattr(status, 'locations', 'N/A')}")
                print(f"Clients: {getattr(status, 'clients', 'N/A')}")
            
            print(f"\n_Data Mode: {self.data_service.mode.upper()}")
            if self.data_service.mode == "api":
                print(f"API URL: {self.data_service.config.api_url}")
            else:
                print(f"Database: {self.data_service.config.database_path}")
            
        except Exception as e:
            print_error(f"Failed to get system status: {e}")
    
    def show_system_operations_menu(self):
        """Display system operations menu"""
        print_header(self.data_service, self.menu_stack)
        
        options = [
            ("1", "🔄", "Refresh Connection"),
            ("2", "⚡", "Performance Test"),
            ("3", "🧹", "Cleanup Operations"),
            ("4", "📊", "Generate Reports"),
            ("0", "↩️", "Back to Main Menu")
        ]
        
        print_menu_box("SYSTEM OPERATIONS", options)
    
    def quick_database_check(self):
        """Quick database connectivity and basic stats check"""
        try:
            print_header(self.data_service, self.menu_stack)
            
            print("🔍 Quick Database Check")
            print("=" * 30)
            
            # Test connection
            print("Testing connection...")
            health = self.data_service.health_check()
            
            if health["status"] == "healthy":
                print_success("Database connection: OK")
            else:
                print_error(f"Database connection: {health['message']}")
                return
            
            # Quick stats
            print("\n📊 Quick Statistics:")
            print("-" * 20)
            
            try:
                # Test a few entity counts
                trucks = self.data_service.get_all('trucks')
                orders = self.data_service.get_all('orders')
                locations = self.data_service.get_all('locations')
                
                print(f"Trucks: {len(trucks) if trucks else 0}")
                print(f"Orders: {len(orders) if orders else 0}")
                print(f"Locations: {len(locations) if locations else 0}")
                
                print_success("Database check completed successfully!")
                
            except Exception as e:
                print_error(f"Error during stats check: {e}")
        
        except Exception as e:
            print_error(f"Quick check failed: {e}")
    
    def handle_main_menu_choice(self, choice: str) -> bool:
        """Handle main menu selections"""
        if choice == "1":
            self.menu_stack.append("Database Management")
            self.current_menu = "database"
            return True
        elif choice == "2":
            self.menu_stack.append("Entity Management")
            self.current_menu = "entity"
            return True
        elif choice == "3":
            self.menu_stack.append("System Status")
            self.show_system_status()
            pause()
            return True
        elif choice == "4":
            self.menu_stack.append("System Operations")
            self.current_menu = "operations"
            return True
        elif choice == "5":
            self.menu_stack.append("Quick Check")
            self.quick_database_check()
            pause()
            self.menu_stack.pop()
            return True
        elif choice == "0":
            print("\n" + Colors.WARNING + "Goodbye!" + Colors.ENDC)
            return False
        else:
            print_error("Invalid choice. Please try again.")
            pause()
            return True
    
    def handle_entity_menu_choice(self, choice: str) -> bool:
        """Handle entity management menu selections"""
        entity_map = {
            "1": "trucks",
            "2": "orders", 
            "3": "locations",
            "4": "routes",
            "5": "clients",
            "6": "packages",
            "7": "cargo"
        }
        
        if choice in entity_map:
            entity_type = entity_map[choice]
            entity_name = self.crud_ops.entities[entity_type]['plural']
            self.menu_stack.append(entity_name)
            self.crud_ops.entity_menu(entity_type)
            self.menu_stack.pop()
            return True
        elif choice == "0":
            self.menu_stack.pop()
            self.current_menu = "main"
            return True
        else:
            print_error("Invalid choice. Please try again.")
            pause()
            return True
    
    def handle_database_menu_choice(self, choice: str) -> bool:
        """Handle database management menu selections"""
        if choice == "1":
            self.show_table_statistics()
            pause()
            return True
        elif choice == "2":
            print_info("Database operations menu - Not yet implemented")
            pause()
            return True
        elif choice == "3":
            self.list_all_tables()
            pause()
            return True
        elif choice == "4":
            print_info("Database search - Not yet implemented")
            pause()
            return True
        elif choice == "0":
            self.menu_stack.pop()
            self.current_menu = "main"
            return True
        else:
            print_error("Invalid choice. Please try again.")
            pause()
            return True
    
    def handle_operations_menu_choice(self, choice: str) -> bool:
        """Handle system operations menu selections"""
        if choice == "1":
            print_info("Refreshing connection...")
            health = self.data_service.health_check()
            if health["status"] == "healthy":
                print_success("Connection refreshed successfully!")
            else:
                print_error(f"Connection issue: {health['message']}")
            pause()
            return True
        elif choice == "2":
            print_info("Performance test - Not yet implemented")
            pause()
            return True
        elif choice == "3":
            print_info("Cleanup operations - Not yet implemented")
            pause()
            return True
        elif choice == "4":
            print_info("Report generation - Not yet implemented")
            pause()
            return True
        elif choice == "0":
            self.menu_stack.pop()
            self.current_menu = "main"
            return True
        else:
            print_error("Invalid choice. Please try again.")
            pause()
            return True
    
    def show_table_statistics(self):
        """Show statistics for all tables"""
        try:
            print("📊 Table Statistics")
            print("=" * 30)
            
            stats = []
            for entity_type in self.crud_ops.entities.keys():
                try:
                    entities = self.data_service.get_all(entity_type)
                    count = len(entities) if entities else 0
                    stats.append({
                        'Table': self.crud_ops.entities[entity_type]['plural'],
                        'Count': count
                    })
                except Exception as e:
                    stats.append({
                        'Table': self.crud_ops.entities[entity_type]['plural'],
                        'Count': f"Error: {e}"
                    })
            
            format_table_data(stats, ['Table', 'Count'])
            
        except Exception as e:
            print_error(f"Failed to get table statistics: {e}")
    
    def list_all_tables(self):
        """List all available tables/entities"""
        print("📋 Available Tables/Entities")
        print("=" * 35)
        
        for entity_type, config in self.crud_ops.entities.items():
            print(f"• {config['plural']} ({entity_type})")
            print(f"  Fields: {', '.join(config['headers'])}")
            print()
    
    def run(self):
        """Main menu loop"""
        try:
            while self.running:
                if self.current_menu == "main":
                    self.show_main_menu()
                    choice = get_input()
                    self.running = self.handle_main_menu_choice(choice)
                    
                elif self.current_menu == "entity":
                    self.show_entity_management_menu()
                    choice = get_input()
                    if not self.handle_entity_menu_choice(choice):
                        break
                        
                elif self.current_menu == "database":
                    self.show_database_management_menu()
                    choice = get_input()
                    if not self.handle_database_menu_choice(choice):
                        break
                        
                elif self.current_menu == "operations":
                    self.show_system_operations_menu()
                    choice = get_input()
                    if not self.handle_operations_menu_choice(choice):
                        break
        
        except KeyboardInterrupt:
            print("\n\n" + Colors.WARNING + "Goodbye!" + Colors.ENDC)
            sys.exit(0)
        except Exception as e:
            print_error(f"An error occurred: {e}")
            print_info("Please restart the application.")
            sys.exit(1)