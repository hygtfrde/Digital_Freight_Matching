#!/usr/bin/env python3
"""
CLI Dashboard for Digital Freight Matching System
Integrates with db_manager.py for database operations
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import Session

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import engine
from db_manager import DatabaseManager, SystemStatus


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class CLIDashboard:
    """Main CLI Dashboard for Digital Freight Matching System"""
    
    def __init__(self):
        self.running = True
        self.current_menu = "main"
        self.menu_stack = ["Main"]
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print application header"""
        self.clear_screen()
        print(Colors.CYAN + "=" * 65 + Colors.ENDC)
        print(Colors.BOLD + "🚛 DIGITAL FREIGHT MATCHING SYSTEM".center(65) + Colors.ENDC)
        print(Colors.CYAN + "=" * 65 + Colors.ENDC)
        print(f"📍 Location: {' > '.join(self.menu_stack)}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 65)
        print()
    
    def print_menu_box(self, title: str, options: List[tuple]):
        """Print a formatted menu box"""
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
            return input(Colors.CYAN + prompt + Colors.ENDC).strip()
        except KeyboardInterrupt:
            print("\n\n" + Colors.WARNING + "Goodbye!" + Colors.ENDC)
            sys.exit(0)
        except Exception as e:
            print(Colors.FAIL + f"Input error: {e}" + Colors.ENDC)
            return ""
    
    def pause(self):
        """Pause for user to read output"""
        input("\n" + Colors.CYAN + "Press Enter to continue..." + Colors.ENDC)
    
    def success_message(self, msg: str):
        """Display success message"""
        print(Colors.GREEN + f"✅ {msg}" + Colors.ENDC)
    
    def error_message(self, msg: str):
        """Display error message"""
        print(Colors.FAIL + f"❌ {msg}" + Colors.ENDC)
    
    def warning_message(self, msg: str):
        """Display warning message"""
        print(Colors.WARNING + f"⚠️  {msg}" + Colors.ENDC)
    
    def run(self):
        """Main application loop"""
        while self.running:
            if self.current_menu == "main":
                self.main_menu()
            elif self.current_menu == "database":
                self.database_menu()
            elif self.current_menu == "system":
                self.system_menu()
            elif self.current_menu == "reports":
                self.reports_menu()
            else:
                self.current_menu = "main"
    
    def main_menu(self):
        """Display and handle main menu"""
        self.menu_stack = ["Main"]
        self.print_header()
        
        options = [
            ("1", "🗄️", "Database Management"),
            ("2", "📊", "System Status & Reports"),
            ("3", "⚙️", "System Operations"),
            ("4", "🔍", "Quick Database Check"),
            ("5", "❌", "Exit"),
        ]
        
        self.print_menu_box("MAIN MENU", options)
        
        choice = self.get_input()
        
        if choice == "1":
            self.current_menu = "database"
        elif choice == "2":
            self.current_menu = "reports"
        elif choice == "3":
            self.current_menu = "system"
        elif choice == "4":
            self.quick_database_check()
        elif choice == "5":
            self.exit_program()
        else:
            self.error_message("Invalid choice. Please try again.")
            self.pause()
    
    def database_menu(self):
        """Database management menu"""
        self.menu_stack = ["Main", "Database"]
        self.print_header()
        
        options = [
            ("1", "🔄", "Initialize Database"),
            ("2", "🔄", "Force Reinitialize Database"),
            ("3", "✅", "Verify Database Integrity"),
            ("4", "📊", "Show Database Status"),
            ("5", "🗑️", "Reset Database"),
            ("6", "🧪", "Run Database Tests"),
            ("0", "🔙", "Back to Main Menu"),
        ]
        
        self.print_menu_box("DATABASE MANAGEMENT", options)
        
        choice = self.get_input()
        
        if choice == "1":
            self.initialize_database()
        elif choice == "2":
            self.force_initialize_database()
        elif choice == "3":
            self.verify_database()
        elif choice == "4":
            self.show_database_status()
        elif choice == "5":
            self.reset_database()
        elif choice == "6":
            self.run_database_tests()
        elif choice == "0":
            self.current_menu = "main"
        else:
            self.error_message("Invalid choice")
            self.pause()
    
    def system_menu(self):
        """System operations menu"""
        self.menu_stack = ["Main", "System"]
        self.print_header()
        
        options = [
            ("1", "🎮", "Load Demo Data"),
            ("2", "🧹", "Clear All Data"),
            ("3", "📥", "Import Data"),
            ("4", "📤", "Export Data"),
            ("5", "ℹ️", "System Information"),
            ("6", "🔧", "Configuration"),
            ("0", "🔙", "Back to Main Menu"),
        ]
        
        self.print_menu_box("SYSTEM OPERATIONS", options)
        
        choice = self.get_input()
        
        if choice == "1":
            self.load_demo_data()
        elif choice == "2":
            self.clear_all_data()
        elif choice == "3":
            self.import_data()
        elif choice == "4":
            self.export_data()
        elif choice == "5":
            self.system_information()
        elif choice == "6":
            self.configuration()
        elif choice == "0":
            self.current_menu = "main"
        else:
            self.error_message("Invalid choice")
            self.pause()
    
    def reports_menu(self):
        """Reports and analytics menu"""
        self.menu_stack = ["Main", "Reports"]
        self.print_header()
        
        options = [
            ("1", "📈", "System Status Dashboard"),
            ("2", "💰", "Financial Summary"),
            ("3", "🚛", "Fleet Utilization"),
            ("4", "📦", "Order Statistics"),
            ("5", "🗺️", "Route Analysis"),
            ("6", "📊", "Comprehensive Report"),
            ("0", "🔙", "Back to Main Menu"),
        ]
        
        self.print_menu_box("REPORTS & ANALYTICS", options)
        
        choice = self.get_input()
        
        if choice == "1":
            self.system_status_dashboard()
        elif choice == "2":
            self.financial_summary()
        elif choice == "3":
            self.fleet_utilization_report()
        elif choice == "4":
            self.order_statistics()
        elif choice == "5":
            self.route_analysis()
        elif choice == "6":
            self.comprehensive_report()
        elif choice == "0":
            self.current_menu = "main"
        else:
            self.error_message("Invalid choice")
            self.pause()
    
    # Database Management Actions
    
    def initialize_database(self):
        """Initialize database with contract data"""
        self.print_header()
        print(Colors.BOLD + "🔄 INITIALIZE DATABASE" + Colors.ENDC)
        print("-" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                success = db_manager.initialize_database()
                
                if success:
                    self.success_message("Database initialized successfully!")
                else:
                    self.warning_message("Database already initialized (skipped to prevent duplicates)")
                    
        except Exception as e:
            self.error_message(f"Database initialization failed: {e}")
        
        self.pause()
    
    def force_initialize_database(self):
        """Force reinitialize database"""
        self.print_header()
        print(Colors.BOLD + "🔄 FORCE REINITIALIZE DATABASE" + Colors.ENDC)
        print("-" * 65)
        
        self.warning_message("This may create duplicate data!")
        confirm = self.get_input("Are you sure? (y/n): ")
        
        if confirm.lower() != 'y':
            print("Operation cancelled")
            self.pause()
            return
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                success = db_manager.initialize_database(force_reinit=True)
                
                if success:
                    self.success_message("Database force reinitialized!")
                else:
                    self.warning_message("Initialization completed with existing data reuse")
                    
        except Exception as e:
            self.error_message(f"Force initialization failed: {e}")
        
        self.pause()
    
    def verify_database(self):
        """Verify database integrity"""
        self.print_header()
        print(Colors.BOLD + "✅ VERIFY DATABASE INTEGRITY" + Colors.ENDC)
        print("-" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                counts = db_manager.verify_integrity()
                
                print("\nDatabase Entity Counts:")
                print("-" * 30)
                for entity, count in counts.items():
                    print(f"{entity.capitalize():12}: {count:>6}")
                
                self.success_message("Database integrity check completed!")
                
        except Exception as e:
            self.error_message(f"Integrity check failed: {e}")
        
        self.pause()
    
    def show_database_status(self):
        """Show comprehensive database status"""
        self.print_header()
        print(Colors.BOLD + "📊 DATABASE STATUS" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                self._display_system_status(status)
                
        except Exception as e:
            self.error_message(f"Failed to get status: {e}")
        
        self.pause()
    
    def reset_database(self):
        """Reset database"""
        self.print_header()
        print(Colors.BOLD + "🗑️ RESET DATABASE" + Colors.ENDC)
        print("-" * 65)
        
        self.warning_message("This will DELETE ALL database data!")
        confirm = self.get_input("Type 'DELETE' to confirm: ")
        
        if confirm != 'DELETE':
            print("Reset cancelled")
            self.pause()
            return
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                success = db_manager.reset_database(confirm=True)
                
                if success:
                    self.success_message("Database reset completed!")
                else:
                    self.error_message("Database reset failed")
                    
        except Exception as e:
            self.error_message(f"Reset failed: {e}")
        
        self.pause()
    
    def run_database_tests(self):
        """Run database tests"""
        self.print_header()
        print(Colors.BOLD + "🧪 RUN DATABASE TESTS" + Colors.ENDC)
        print("-" * 65)
        
        print("Running comprehensive database tests...")
        
        try:
            import subprocess
            result = subprocess.run([sys.executable, "test_db_manager.py"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.success_message("All tests passed!")
                print("\nTest Summary:")
                # Parse test output for summary
                lines = result.stdout.split('\n')
                for line in lines[-10:]:
                    if line.strip():
                        print(f"  {line}")
            else:
                self.error_message("Some tests failed!")
                print("\nTest Output:")
                print(result.stdout)
                if result.stderr:
                    print("\nErrors:")
                    print(result.stderr)
                    
        except Exception as e:
            self.error_message(f"Failed to run tests: {e}")
        
        self.pause()
    
    # System Operations
    
    def load_demo_data(self):
        """Load demo data"""
        self.print_header()
        print(Colors.BOLD + "🎮 LOAD DEMO DATA" + Colors.ENDC)
        print("-" * 65)
        
        print("Loading demo data is handled by database initialization.")
        print("The contract data includes:")
        print("  • Too-Big-To-Fail Company (contract client)")
        print("  • 5 specialized trucks")
        print("  • 5 routes from Atlanta to Georgia cities")
        print("  • Contract orders with cargo")
        print("  • Example client with sample orders")
        
        self.pause()
    
    def clear_all_data(self):
        """Clear all data"""
        self.print_header()
        print(Colors.BOLD + "🧹 CLEAR ALL DATA" + Colors.ENDC)
        print("-" * 65)
        
        self.warning_message("This will remove ALL data from the database!")
        confirm = self.get_input("Type 'CLEAR' to confirm: ")
        
        if confirm != 'CLEAR':
            print("Operation cancelled")
            self.pause()
            return
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                success = db_manager.reset_database(confirm=True)
                
                if success:
                    self.success_message("All data cleared!")
                else:
                    self.error_message("Clear operation failed")
                    
        except Exception as e:
            self.error_message(f"Clear failed: {e}")
        
        self.pause()
    
    def import_data(self):
        """Import data from file"""
        self.print_header()
        print(Colors.BOLD + "📥 IMPORT DATA" + Colors.ENDC)
        print("-" * 65)
        
        self.warning_message("Data import functionality not yet implemented")
        print("\nWould allow importing from:")
        print("  • JSON files")
        print("  • CSV files")
        print("  • Database backups")
        
        self.pause()
    
    def export_data(self):
        """Export data to file"""
        self.print_header()
        print(Colors.BOLD + "📤 EXPORT DATA" + Colors.ENDC)
        print("-" * 65)
        
        self.warning_message("Data export functionality not yet implemented")
        print("\nWould allow exporting to:")
        print("  • JSON format")
        print("  • CSV format")
        print("  • Database backup")
        
        self.pause()
    
    def system_information(self):
        """Display system information"""
        self.print_header()
        print(Colors.BOLD + "ℹ️ SYSTEM INFORMATION" + Colors.ENDC)
        print("=" * 65)
        
        print(f"Python Version: {sys.version}")
        print(f"Platform: {sys.platform}")
        print(f"Current Directory: {os.getcwd()}")
        print(f"Database File: logistics.db")
        
        # Check if database file exists
        if os.path.exists("logistics.db"):
            stat = os.stat("logistics.db")
            print(f"Database Size: {stat.st_size:,} bytes")
            print(f"Last Modified: {datetime.fromtimestamp(stat.st_mtime)}")
        else:
            print("Database File: Not found")
        
        print(f"\nAvailable Commands:")
        print(f"  • Database Manager: python db_manager.py")
        print(f"  • Run Tests: python test_db_manager.py")
        print(f"  • CLI Dashboard: python cli_dashboard.py")
        
        self.pause()
    
    def configuration(self):
        """System configuration"""
        self.print_header()
        print(Colors.BOLD + "🔧 CONFIGURATION" + Colors.ENDC)
        print("-" * 65)
        
        self.warning_message("Configuration functionality not yet implemented")
        print("\nWould allow configuring:")
        print("  • Database connection settings")
        print("  • Logging levels")
        print("  • Performance parameters")
        print("  • Business rules")
        
        self.pause()
    
    # Reports and Analytics
    
    def system_status_dashboard(self):
        """Display system status dashboard"""
        self.print_header()
        print(Colors.BOLD + "📈 SYSTEM STATUS DASHBOARD" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                self._display_system_status(status)
                
        except Exception as e:
            self.error_message(f"Failed to get system status: {e}")
        
        self.pause()
    
    def financial_summary(self):
        """Display financial summary"""
        self.print_header()
        print(Colors.BOLD + "💰 FINANCIAL SUMMARY" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                print(f"\n💰 Financial Metrics")
                print("-" * 30)
                print(f"Daily Profit/Loss: ${status.daily_profit_loss:.2f}")
                
                if status.total_routes > 0:
                    avg_profit = status.daily_profit_loss / status.total_routes
                    print(f"Average per Route: ${avg_profit:.2f}")
                
                # Calculate annual projection
                annual_projection = status.daily_profit_loss * 365
                print(f"Annual Projection: ${annual_projection:,.2f}")
                
                # Status indicator
                if status.daily_profit_loss > 0:
                    print(f"Status: {Colors.GREEN}✅ Profitable{Colors.ENDC}")
                else:
                    print(f"Status: {Colors.FAIL}❌ Loss-making{Colors.ENDC}")
                
                print(f"\n📊 Business Metrics")
                print("-" * 30)
                print(f"Active Contracts: {status.active_contracts}")
                print(f"Pending Orders: {status.pending_orders}")
                print(f"Fleet Utilization: {status.truck_utilization:.1f}%")
                
        except Exception as e:
            self.error_message(f"Failed to get financial summary: {e}")
        
        self.pause()
    
    def fleet_utilization_report(self):
        """Display fleet utilization report"""
        self.print_header()
        print(Colors.BOLD + "🚛 FLEET UTILIZATION REPORT" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                print(f"\n🚛 Fleet Overview")
                print("-" * 30)
                print(f"Total Trucks: {status.trucks}")
                print(f"Utilization Rate: {status.truck_utilization:.1f}%")
                
                # Visual utilization bar
                bar_length = 40
                filled = int(bar_length * status.truck_utilization / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"\nUtilization: [{bar}] {status.truck_utilization:.1f}%")
                
                # Utilization status
                if status.truck_utilization > 80:
                    print(f"Status: {Colors.WARNING}⚠️ High Utilization{Colors.ENDC}")
                elif status.truck_utilization > 60:
                    print(f"Status: {Colors.GREEN}✅ Good Utilization{Colors.ENDC}")
                else:
                    print(f"Status: {Colors.CYAN}📈 Room for Growth{Colors.ENDC}")
                
        except Exception as e:
            self.error_message(f"Failed to get fleet report: {e}")
        
        self.pause()
    
    def order_statistics(self):
        """Display order statistics"""
        self.print_header()
        print(Colors.BOLD + "📦 ORDER STATISTICS" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                print(f"\n📦 Order Metrics")
                print("-" * 30)
                print(f"Total Orders: {status.orders}")
                print(f"Active Contracts: {status.active_contracts}")
                print(f"Pending Orders: {status.pending_orders}")
                
                if status.orders > 0:
                    contract_rate = (status.active_contracts / status.orders) * 100
                    print(f"Contract Rate: {contract_rate:.1f}%")
                
                print(f"\n📊 Order Distribution")
                print("-" * 30)
                print(f"Cargo Loads: {status.cargo_loads}")
                print(f"Total Packages: {status.packages}")
                
                if status.cargo_loads > 0:
                    avg_packages = status.packages / status.cargo_loads
                    print(f"Avg Packages/Load: {avg_packages:.1f}")
                
        except Exception as e:
            self.error_message(f"Failed to get order statistics: {e}")
        
        self.pause()
    
    def route_analysis(self):
        """Display route analysis"""
        self.print_header()
        print(Colors.BOLD + "🗺️ ROUTE ANALYSIS" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                print(f"\n🗺️ Route Metrics")
                print("-" * 30)
                print(f"Total Routes: {status.total_routes}")
                print(f"Daily P&L: ${status.daily_profit_loss:.2f}")
                
                if status.total_routes > 0:
                    avg_profit = status.daily_profit_loss / status.total_routes
                    print(f"Avg Profit/Route: ${avg_profit:.2f}")
                
                # Route performance indicator
                if status.daily_profit_loss > 0:
                    print(f"Performance: {Colors.GREEN}✅ Profitable Routes{Colors.ENDC}")
                else:
                    print(f"Performance: {Colors.FAIL}❌ Loss-making Routes{Colors.ENDC}")
                    print(f"Optimization needed to achieve profitability")
                
        except Exception as e:
            self.error_message(f"Failed to get route analysis: {e}")
        
        self.pause()
    
    def comprehensive_report(self):
        """Display comprehensive system report"""
        self.print_header()
        print(Colors.BOLD + "📊 COMPREHENSIVE SYSTEM REPORT" + Colors.ENDC)
        print("=" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                status = db_manager.get_system_status()
                
                self._display_system_status(status)
                
                print(f"\n🎯 Key Performance Indicators")
                print("-" * 40)
                
                # Calculate KPIs
                if status.orders > 0:
                    contract_rate = (status.active_contracts / status.orders) * 100
                    print(f"Contract Fulfillment Rate: {contract_rate:.1f}%")
                
                if status.total_routes > 0:
                    avg_route_profit = status.daily_profit_loss / status.total_routes
                    print(f"Average Route Profitability: ${avg_route_profit:.2f}")
                
                print(f"Fleet Efficiency: {status.truck_utilization:.1f}%")
                
                # Business health indicators
                print(f"\n🏥 Business Health")
                print("-" * 40)
                
                health_score = 0
                if status.daily_profit_loss > 0:
                    health_score += 40
                    print(f"✅ Profitability: Positive")
                else:
                    print(f"❌ Profitability: Negative")
                
                if status.truck_utilization > 60:
                    health_score += 30
                    print(f"✅ Fleet Utilization: Good ({status.truck_utilization:.1f}%)")
                else:
                    print(f"⚠️ Fleet Utilization: Low ({status.truck_utilization:.1f}%)")
                
                if status.pending_orders < status.active_contracts:
                    health_score += 30
                    print(f"✅ Order Management: Balanced")
                else:
                    print(f"⚠️ Order Management: High Pending ({status.pending_orders})")
                
                print(f"\nOverall Health Score: {health_score}/100")
                
        except Exception as e:
            self.error_message(f"Failed to generate comprehensive report: {e}")
        
        self.pause()
    
    def quick_database_check(self):
        """Quick database status check"""
        self.print_header()
        print(Colors.BOLD + "🔍 QUICK DATABASE CHECK" + Colors.ENDC)
        print("-" * 65)
        
        try:
            with Session(engine) as session:
                db_manager = DatabaseManager(session)
                existing_data, counts = db_manager.check_existing_data()
                
                print("Database Status:")
                for entity, count in counts.items():
                    status_icon = "✅" if count > 0 else "❌"
                    print(f"  {status_icon} {entity.capitalize()}: {count}")
                
                # Quick health check
                total_entities = sum(counts.values())
                if total_entities == 0:
                    self.warning_message("Database is empty - run initialization")
                elif counts.get('clients', 0) > 0 and counts.get('routes', 0) > 0:
                    self.success_message("Database appears healthy")
                else:
                    self.warning_message("Database may need initialization")
                    
        except Exception as e:
            self.error_message(f"Database check failed: {e}")
        
        self.pause()
    
    def _display_system_status(self, status: SystemStatus):
        """Helper to display system status"""
        print(f"\n📊 System Overview")
        print("-" * 30)
        print(f"Total Routes: {status.total_routes}")
        print(f"Daily Profit/Loss: ${status.daily_profit_loss:.2f}")
        print(f"Pending Orders: {status.pending_orders}")
        print(f"Active Contracts: {status.active_contracts}")
        print(f"Truck Utilization: {status.truck_utilization:.1f}%")
        
        print(f"\n🗄️ Database Entities")
        print("-" * 30)
        print(f"Clients: {status.clients}")
        print(f"Locations: {status.locations}")
        print(f"Trucks: {status.trucks}")
        print(f"Orders: {status.orders}")
        print(f"Cargo Loads: {status.cargo_loads}")
        print(f"Packages: {status.packages}")
        
        print(f"\n⏰ Last Updated: {status.last_updated}")
    
    def exit_program(self):
        """Exit the program"""
        self.print_header()
        print(Colors.GREEN + "Thank you for using Digital Freight Matching System!" + Colors.ENDC)
        print("Goodbye! 👋")
        self.running = False


def main():
    """Main entry point"""
    dashboard = CLIDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()