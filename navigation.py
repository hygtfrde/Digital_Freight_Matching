"""
navigation.py - Core Navigation and Menu System for Digital Freight Matching
This module handles all CLI navigation, state management, and user interaction patterns.
It could further be extended into a cross-platform GUI application, ie: Flet, PyQt, etc.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pickle
from pathlib import Path


class MenuLevel(Enum):
    """Enumeration of menu hierarchy levels"""
    MAIN = "main"
    SUB = "sub"
    ACTION = "action"
    CONFIRM = "confirm"
    RESULT = "result"


@dataclass
class MenuItem:
    """Represents a single menu item with its properties"""
    key: str  # Key to press (e.g., '1', '2', etc.)
    label: str  # Display label
    action: Optional[Callable] = None  # Function to execute
    submenu: Optional['Menu'] = None  # Submenu to navigate to
    requires_confirm: bool = False  # Whether action needs confirmation
    shortcut: Optional[str] = None  # Alternative key shortcut
    icon: str = ""  # Optional emoji/icon for display
    
    def display(self) -> str:
        """Format menu item for display"""
        icon_str = f"{self.icon} " if self.icon else ""
        shortcut_str = f" ({self.shortcut})" if self.shortcut else ""
        return f"  {self.key}. {icon_str}{self.label}{shortcut_str}"


@dataclass
class Menu:
    """Represents a menu with items and metadata"""
    name: str
    title: str
    items: List[MenuItem] = field(default_factory=list)
    parent: Optional['Menu'] = None
    level: MenuLevel = MenuLevel.MAIN
    
    def add_item(self, item: MenuItem) -> None:
        """Add an item to this menu"""
        self.items.append(item)
        if item.submenu:
            item.submenu.parent = self
    
    def get_item(self, key: str) -> Optional[MenuItem]:
        """Get menu item by key or shortcut"""
        for item in self.items:
            if item.key == key or item.shortcut == key:
                return item
        return None
    
    def display(self) -> str:
        """Generate the display string for this menu"""
        lines = []
        width = 65
        
        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        title_centered = self.title.center(width - 2)
        lines.append("│" + title_centered + "│")
        lines.append("├" + "─" * (width - 2) + "┤")
        
        # Menu items
        for item in self.items:
            item_text = item.display()
            padding = width - len(item_text) - 1
            lines.append("│" + item_text + " " * padding + "│")
        
        # Footer
        lines.append("└" + "─" * (width - 2) + "┘")
        
        return "\n".join(lines)


@dataclass
class NavigationState:
    """Tracks the current state of navigation"""
    menu_stack: List[Menu] = field(default_factory=list)
    history: List[Tuple[datetime, str]] = field(default_factory=list)  # (timestamp, action)
    filters: Dict[str, Any] = field(default_factory=dict)
    sort_preferences: Dict[str, str] = field(default_factory=dict)
    last_action: Optional[str] = None
    session_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def current_menu(self) -> Optional[Menu]:
        """Get the current menu from the stack"""
        return self.menu_stack[-1] if self.menu_stack else None
    
    @property
    def breadcrumb(self) -> str:
        """Generate breadcrumb trail"""
        if not self.menu_stack:
            return "Home"
        return " > ".join(menu.name for menu in self.menu_stack)
    
    def push_menu(self, menu: Menu) -> None:
        """Navigate to a new menu"""
        self.menu_stack.append(menu)
        self.add_history(f"Navigated to {menu.name}")
    
    def pop_menu(self) -> Optional[Menu]:
        """Go back to previous menu"""
        if len(self.menu_stack) > 1:
            popped = self.menu_stack.pop()
            self.add_history(f"Back from {popped.name}")
            return self.current_menu
        return None
    
    def go_to_main(self) -> None:
        """Return to main menu"""
        if self.menu_stack:
            main = self.menu_stack[0]
            self.menu_stack = [main]
            self.add_history("Returned to main menu")
    
    def add_history(self, action: str) -> None:
        """Add action to history"""
        self.history.append((datetime.now(), action))
        self.last_action = action
        # Keep only last 100 history items
        if len(self.history) > 100:
            self.history = self.history[-100:]


class MenuSystem:
    """
    Main menu system controller that manages navigation and user interaction
    """
    
    def __init__(self, session_file: str = ".dfm_session.pkl"):
        """Initialize the menu system"""
        self.state = NavigationState()
        self.session_file = Path(session_file)
        self.running = False
        self.menus: Dict[str, Menu] = {}
        
        # Universal command handlers
        self.universal_commands = {
            'h': self.show_help,
            '?': self.show_help,
            'm': self.go_to_main,
            'b': self.go_back,
            'q': self.quick_exit,
            'history': self.show_history,
            'save': self.save_session,
            'load': self.load_session,
        }
        
        # Initialize with empty data stores (will be set by dashboard)
        self.data_context = {
            'orders': [],
            'trucks': [],
            'routes': [],
            'clients': [],
            'pricing_service': None
        }
    
    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self) -> None:
        """Display the application header with context info"""
        print("=" * 65)
        print("🚛 DIGITAL FREIGHT MATCHING SYSTEM".center(65))
        print("=" * 65)
        print(f"📍 Location: {self.state.breadcrumb}")
        
        # Show relevant stats based on context
        if self.data_context.get('orders'):
            pending = sum(1 for o in self.data_context['orders'] if not hasattr(o, 'matched') or not o.matched)
            print(f"📦 Orders: {len(self.data_context['orders'])} total, {pending} pending")
        if self.data_context.get('trucks'):
            print(f"🚛 Fleet: {len(self.data_context['trucks'])} trucks")
        
        print("-" * 65)
        print()
    
    def show_help(self) -> None:
        """Display help information"""
        help_text = """
        ╔════════════════════════════════════════════════════════════╗
        ║                    HELP - Navigation Commands              ║
        ╠════════════════════════════════════════════════════════════╣
        ║  Universal Commands (available anywhere):                  ║
        ║  • h or ?     : Show this help                            ║
        ║  • m          : Return to main menu                       ║
        ║  • b          : Go back to previous menu                  ║
        ║  • q          : Quick save and exit                       ║
        ║  • history    : Show action history                       ║
        ║  • save       : Save current session                      ║
        ║  • load       : Load previous session                     ║
        ║                                                            ║
        ║  Navigation:                                               ║
        ║  • Enter menu number to select                            ║
        ║  • 0 usually goes back                                    ║
        ║  • Some items have letter shortcuts                       ║
        ╚════════════════════════════════════════════════════════════╝
        """
        print(help_text)
        input("\nPress Enter to continue...")
    
    def go_to_main(self) -> None:
        """Navigate to main menu"""
        self.state.go_to_main()
    
    def go_back(self) -> None:
        """Go back one menu level"""
        if not self.state.pop_menu():
            print("Already at main menu")
    
    def quick_exit(self) -> None:
        """Save session and exit"""
        self.save_session()
        print("\n✅ Session saved. Goodbye!")
        self.running = False
        sys.exit(0)
    
    def show_history(self) -> None:
        """Display action history"""
        print("\n📜 Recent Actions:")
        print("-" * 50)
        for timestamp, action in self.state.history[-10:]:
            print(f"{timestamp.strftime('%H:%M:%S')} - {action}")
        print("-" * 50)
        input("\nPress Enter to continue...")
    
    def save_session(self) -> None:
        """Save current session state to file"""
        try:
            session_data = {
                'state': self.state,
                'timestamp': datetime.now(),
                'data_context_summary': {
                    'num_orders': len(self.data_context.get('orders', [])),
                    'num_trucks': len(self.data_context.get('trucks', [])),
                    'num_routes': len(self.data_context.get('routes', []))
                }
            }
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            print("✅ Session saved successfully")
        except Exception as e:
            print(f"❌ Error saving session: {e}")
    
    def load_session(self) -> bool:
        """Load previous session state from file"""
        if not self.session_file.exists():
            return False
        
        try:
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            self.state = session_data['state']
            timestamp = session_data['timestamp']
            
            print(f"✅ Loaded session from {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return False
    
    def get_input(self, prompt: str = "Enter choice: ", valid_choices: Optional[List[str]] = None) -> str:
        """Get user input with validation"""
        while True:
            try:
                choice = input(prompt).strip().lower()
                
                # Check universal commands first
                if choice in self.universal_commands:
                    return choice
                
                # Validate against specific choices if provided
                if valid_choices and choice not in valid_choices:
                    print(f"❌ Invalid choice. Please enter: {', '.join(valid_choices)}")
                    continue
                
                return choice
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted. Save session? (y/n): ", end="")
                if input().lower() == 'y':
                    self.save_session()
                sys.exit(0)
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def confirm_action(self, message: str) -> bool:
        """Get confirmation for an action"""
        response = self.get_input(f"\n⚠️  {message} (y/n): ", ['y', 'n'])
        return response == 'y'
    
    def paginated_display(self, items: List[Any], formatter: Callable, page_size: int = 10) -> None:
        """Display items with pagination"""
        total_pages = (len(items) + page_size - 1) // page_size
        current_page = 0
        
        while True:
            self.clear_screen()
            self.show_header()
            
            # Display current page items
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, len(items))
            
            print(f"\n📋 Showing items {start_idx + 1}-{end_idx} of {len(items)}")
            print("-" * 50)
            
            for i, item in enumerate(items[start_idx:end_idx], start=start_idx):
                print(f"\n[{i + 1}] ", end="")
                formatter(item)
            
            print("\n" + "-" * 50)
            print(f"Page {current_page + 1} of {total_pages}")
            print("Commands: [n]ext, [p]revious, [b]ack, [#] to select")
            
            choice = self.get_input("Choice: ")
            
            if choice == 'n' and current_page < total_pages - 1:
                current_page += 1
            elif choice == 'p' and current_page > 0:
                current_page -= 1
            elif choice == 'b':
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    return items[idx]
            elif choice in self.universal_commands:
                self.universal_commands[choice]()
                if choice == 'b':
                    break
    
    def run(self, main_menu: Menu) -> None:
        """Main run loop for the menu system"""
        self.running = True
        self.state.push_menu(main_menu)
        self.menus['main'] = main_menu
        
        # Try to load previous session
        if self.session_file.exists():
            print("Found previous session. Load it? (y/n): ", end="")
            if input().lower() == 'y':
                self.load_session()
        
        while self.running:
            try:
                self.clear_screen()
                self.show_header()
                
                current_menu = self.state.current_menu
                if not current_menu:
                    print("❌ No menu available")
                    break
                
                # Display current menu
                print(current_menu.display())
                
                # Get valid choices for this menu
                valid_choices = [item.key for item in current_menu.items]
                valid_choices.extend([item.shortcut for item in current_menu.items if item.shortcut])
                
                # Get user input
                choice = self.get_input("\nEnter choice: ", valid_choices)
                
                # Handle universal commands
                if choice in self.universal_commands:
                    self.universal_commands[choice]()
                    continue
                
                # Handle menu selection
                menu_item = current_menu.get_item(choice)
                if menu_item:
                    if menu_item.submenu:
                        # Navigate to submenu
                        self.state.push_menu(menu_item.submenu)
                    elif menu_item.action:
                        # Execute action
                        if menu_item.requires_confirm:
                            if self.confirm_action(f"Execute {menu_item.label}?"):
                                menu_item.action()
                        else:
                            menu_item.action()
                    
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")
    
    def set_data_context(self, context: Dict[str, Any]) -> None:
        """Set the data context for the menu system"""
        self.data_context.update(context)


# Factory functions for creating standard menu patterns

def create_crud_menu(name: str, entity_type: str, icon: str = "📋") -> Menu:
    """Create a standard CRUD menu for an entity type"""
    menu = Menu(
        name=f"{entity_type}_management",
        title=f"{icon} {entity_type.upper()} MANAGEMENT",
        level=MenuLevel.SUB
    )
    
    menu.add_item(MenuItem("1", f"List All {entity_type}s", icon="📋"))
    menu.add_item(MenuItem("2", f"Add New {entity_type}", icon="➕"))
    menu.add_item(MenuItem("3", f"Search {entity_type}s", icon="🔍"))
    menu.add_item(MenuItem("4", f"Edit {entity_type}", icon="✏️"))
    menu.add_item(MenuItem("5", f"Delete {entity_type}", icon="🗑️", requires_confirm=True))
    menu.add_item(MenuItem("6", f"Import {entity_type}s", icon="📥"))
    menu.add_item(MenuItem("7", f"Export {entity_type}s", icon="📤"))
    menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
    
    return menu


def create_report_menu() -> Menu:
    """Create a standard reports menu"""
    menu = Menu(
        name="reports",
        title="📊 REPORTS & ANALYTICS",
        level=MenuLevel.SUB
    )
    
    menu.add_item(MenuItem("1", "Daily Summary Dashboard", icon="📈"))
    menu.add_item(MenuItem("2", "Fleet Utilization Report", icon="🚛"))
    menu.add_item(MenuItem("3", "Profitability Analysis", icon="💰"))
    menu.add_item(MenuItem("4", "Route Efficiency Metrics", icon="⏱️"))
    menu.add_item(MenuItem("5", "Cargo Type Distribution", icon="📦"))
    menu.add_item(MenuItem("6", "Geographic Coverage Map", icon="🗺️"))
    menu.add_item(MenuItem("7", "Custom Report Builder", icon="🔧"))
    menu.add_item(MenuItem("8", "Export All Reports", icon="💾"))
    menu.add_item(MenuItem("0", "Back to Main Menu", icon="🔙"))
    
    return menu