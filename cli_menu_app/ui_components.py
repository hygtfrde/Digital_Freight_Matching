"""
UI Components for CLI Menu Application
Contains colors, formatting utilities, and display functions
"""

import os
from datetime import datetime
from typing import List


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


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(data_service, menu_stack):
    """Print application header with data mode and navigation info"""
    clear_screen()
    print(Colors.CYAN + "=" * 65 + Colors.ENDC)
    print(Colors.BOLD + "🚛 DIGITAL FREIGHT MATCHING SYSTEM".center(65) + Colors.ENDC)
    print(Colors.CYAN + "=" * 65 + Colors.ENDC)
    
    # Display data mode with color coding
    mode = data_service.mode.upper()
    if mode == "API":
        mode_color = Colors.BLUE
        mode_icon = "🌐"
        mode_detail = f" ({data_service.config.api_url})"
    else:
        mode_color = Colors.GREEN
        mode_icon = "💾"
        mode_detail = f" ({data_service.config.database_path})"
    
    print(f"🔗 Data Mode: {mode_color}{mode_icon} {mode}{mode_detail}{Colors.ENDC}")
    print(f"📍 Location: {' > '.join(menu_stack)}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)
    print()


def print_menu_box(title: str, options: List[tuple]):
    """Print a formatted menu with title box and simple options below"""
    width = 65
    
    # Print title box
    print("┌" + "─" * (width - 2) + "┐")
    print("│" + title.center(width - 2) + "│")
    print("└" + "─" * (width - 2) + "┘")
    print()
    
    # Print options without borders
    for key, icon, label in options:
        print(f"  {key}. {icon} {label}")
    print()


def get_input(prompt: str = "Enter choice: ") -> str:
    """Get user input with error handling"""
    try:
        return input(Colors.CYAN + prompt + Colors.ENDC).strip()
    except KeyboardInterrupt:
        print("\n\n" + Colors.WARNING + "Goodbye!" + Colors.ENDC)
        import sys
        sys.exit(0)
    except Exception as e:
        print(Colors.FAIL + f"Input error: {e}" + Colors.ENDC)
        return ""


def pause():
    """Pause for user to read output"""
    input("\n" + Colors.CYAN + "Press Enter to continue..." + Colors.ENDC)


def print_success(message: str):
    """Print success message"""
    print(Colors.GREEN + f"✅ {message}" + Colors.ENDC)


def print_error(message: str):
    """Print error message"""
    print(Colors.FAIL + f"❌ {message}" + Colors.ENDC)


def print_warning(message: str):
    """Print warning message"""
    print(Colors.WARNING + f"⚠️ {message}" + Colors.ENDC)


def print_info(message: str):
    """Print info message"""
    print(Colors.CYAN + f"ℹ️ {message}" + Colors.ENDC)


def format_table_data(data: List[dict], headers: List[str]) -> None:
    """Format and print tabular data"""
    if not data:
        print_info("No data found.")
        return
    
    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = len(header)
    
    for row in data:
        for header in headers:
            value = str(row.get(header, "N/A"))
            col_widths[header] = max(col_widths[header], len(value))
    
    # Print header
    header_line = " | ".join(header.ljust(col_widths[header]) for header in headers)
    print(Colors.BOLD + header_line + Colors.ENDC)
    print("-" * len(header_line))
    
    # Print data rows
    for row in data:
        row_line = " | ".join(str(row.get(header, "N/A")).ljust(col_widths[header]) for header in headers)
        print(row_line)


def print_entity_details(entity: dict, title: str):
    """Print entity details in a formatted way"""
    print(Colors.BOLD + f"\n{title}:" + Colors.ENDC)
    print("-" * len(title))
    
    for key, value in entity.items():
        print(f"{key.replace('_', ' ').title()}: {value}")