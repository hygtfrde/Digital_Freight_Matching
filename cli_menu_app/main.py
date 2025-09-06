#!/usr/bin/env python3
"""
Main Entry Point for CLI Menu Application
Digital Freight Matching System - Modular CLI Dashboard
"""

import sys
import argparse
import os

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import from local cli_menu_app data_service (not root)
from menu_system import MenuSystem
from ui_components import print_error, print_success, Colors
from data_service import create_data_service


# TODO: This function 'main' is duplicated in db_manager.py

# TODO: This function 'main' is duplicated in db_manager.py

def main():
    """Main entry point for the CLI application"""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Digital Freight Matching CLI Dashboard",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py                              # Use default configuration
  python main.py --mode=direct               # Force direct database mode
  python main.py --mode=api --api-url=http://localhost:8000  # API mode
  python main.py --environment=production    # Use production config
            """
        )

        parser.add_argument('--mode', choices=['direct', 'api'],
                          help='Data access mode (direct/api)')
        parser.add_argument('--api-url', type=str,
                          help='API base URL (for API mode)')
        parser.add_argument('--api-timeout', type=int,
                          help='API timeout in seconds')
        parser.add_argument('--database-path', type=str,
                          help='Path to database file (for direct mode)')
        parser.add_argument('--environment', choices=['development', 'production'],
                          help='Environment configuration to use')
        parser.add_argument('--config-file', type=str,
                          help='Path to configuration file')

        args = parser.parse_args()

        # Convert args to dict for data service
        cli_args = {k: v for k, v in vars(args).items() if v is not None}

        print(f"{Colors.CYAN}🚛 Digital Freight Matching System - CLI Dashboard{Colors.ENDC}")
        print(f"{Colors.CYAN}{'=' * 60}{Colors.ENDC}")

        # Initialize data service
        print("Initializing data service...")
        data_service = create_data_service(cli_args)

        # Test connection
        health = data_service.health_check()
        if health["status"] != "healthy":
            print_error(f"Failed to connect: {health['message']}")
            print_error("Try running with --mode=direct or ensure API server is running for --mode=api")
            sys.exit(1)

        print_success(f"Connected in {data_service.mode} mode")

        # Initialize and run menu system
        menu_system = MenuSystem(data_service)
        menu_system.run()

    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Goodbye!{Colors.ENDC}")
        sys.exit(0)

    except Exception as e:
        print_error(f"Failed to initialize dashboard: {e}")
        print_error("Try running with --mode=direct or ensure API server is running for --mode=api")
        sys.exit(1)


if __name__ == "__main__":
    main()
