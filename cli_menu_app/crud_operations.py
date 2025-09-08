"""
CRUD Operations for CLI Menu Application
Handles Create, Read, Update, Delete operations for all entities
"""

from ui_components import (
    Colors, print_success, print_error, print_warning, print_info,
    format_table_data, print_entity_details, get_input, pause
)


class CRUDOperations:
    """Handles CRUD operations for all entities"""

    def __init__(self, data_service):
        self.data_service = data_service

        # Entity configurations with display headers
        self.entities = {
            'trucks': {
                'name': 'Truck',
                'plural': 'Trucks',
                'headers': ['id', 'type', 'capacity', 'autonomy'],
                'required_fields': ['type', 'capacity', 'autonomy'],
                'field_types': {
                    'capacity': float,
                    'autonomy': float
                }
            },
            'orders': {
                'name': 'Order',
                'plural': 'Orders',
                'headers': ['id', 'location_origin_id', 'location_destiny_id', 'client_id', 'route_id', 'contract_type'],
                'required_fields': ['location_origin_id', 'location_destiny_id'],
                'field_types': {
                    'location_origin_id': int,
                    'location_destiny_id': int,
                    'client_id': int
                }
            },
            'locations': {
                'name': 'Location',
                'plural': 'Locations',
                'headers': ['id', 'lat', 'lng', 'marked'],
                'required_fields': ['lat', 'lng'],
                'field_types': {
                    'lat': float,
                    'lng': float,
                    'marked': bool
                }
            },
            'routes': {
                'name': 'Route',
                'plural': 'Routes',
                'headers': ['id', 'location_origin_id', 'location_destiny_id', 'profitability', 'truck_id'],
                'required_fields': ['location_origin_id', 'location_destiny_id'],
                'field_types': {
                    'location_origin_id': int,
                    'location_destiny_id': int,
                    'profitability': float,
                    'truck_id': int
                }
            },
            'clients': {
                'name': 'Client',
                'plural': 'Clients',
                'headers': ['id', 'name', 'created_at'],
                'required_fields': ['name'],
                'field_types': {}
            },
            'packages': {
                'name': 'Package',
                'plural': 'Packages',
                'headers': ['id', 'volume', 'weight', 'type', 'cargo_id'],
                'required_fields': ['volume', 'weight', 'type'],
                'field_types': {
                    'volume': float,
                    'weight': float,
                    'cargo_id': int
                }
            },
            'cargo': {
                'name': 'Cargo',
                'plural': 'Cargo Loads',
                'headers': ['id', 'order_id', 'truck_id'],
                'required_fields': ['order_id'],
                'field_types': {
                    'order_id': int,
                    'truck_id': int
                }
            }
        }

    def list_entities(self, entity_type: str) -> bool:
        """List all entities of a given type"""
        try:
            entities = self.data_service.get_all(entity_type)
            config = self.entities[entity_type]

            print(f"\n📋 {config['plural']} List:")
            print("=" * 50)

            if entities:
                format_table_data(entities, config['headers'])
                print(f"\n_Total: {len(entities)} {config['plural'].lower()}")
            else:
                print_info(f"No {config['plural'].lower()} found.")

            return True

        except Exception as e:
            print_error(f"Failed to fetch {entity_type}: {e}")
            return False

    def view_entity_details(self, entity_type: str) -> bool:
        """View details of a specific entity"""
        try:
            entity_id = get_input(f"Enter {self.entities[entity_type]['name']} ID: ")
            if not entity_id.isdigit():
                print_error("Invalid ID. Please enter a number.")
                return False

            entity = self.data_service.get_by_id(entity_type, int(entity_id))
            if entity:
                print_entity_details(entity, f"{self.entities[entity_type]['name']} Details")
            else:
                print_error(f"{self.entities[entity_type]['name']} not found.")

            return True

        except Exception as e:
            print_error(f"Failed to get {entity_type} details: {e}")
            return False

    def create_entity(self, entity_type: str) -> bool:
        """Create a new entity"""
        try:
            config = self.entities[entity_type]
            print(f"\n➕ Create New {config['name']}")
            print("=" * 30)

            entity_data = {}

            # Get required fields
            for field in config['required_fields']:
                while True:
                    # Special handling for cargo type field
                    if field == 'type' and entity_type == 'packages':
                        print("Valid cargo types: standard, fragile, hazmat, refrigerated")
                        value = get_input(f"Enter {field.replace('_', ' ')}: ")
                    else:
                        value = get_input(f"Enter {field.replace('_', ' ')}: ")
                    if not value:
                        print_error(f"{field.replace('_', ' ')} is required.")
                        continue

                    # Type conversion
                    try:
                        if field in config['field_types']:
                            field_type = config['field_types'][field]
                            if field_type == bool:
                                value = value.lower() in ['true', '1', 'yes', 'y']
                            else:
                                value = field_type(value)
                        entity_data[field] = value
                        break
                    except ValueError:
                        print_error(f"Invalid value for {field}. Expected {config['field_types'][field].__name__}.")

            # Get optional fields
            optional_fields = [f for f in config['headers'] if f not in config['required_fields'] and f != 'id']
            for field in optional_fields:
                value = get_input(f"Enter {field.replace('_', ' ')} (optional): ")
                if value:
                    try:
                        if field in config['field_types']:
                            field_type = config['field_types'][field]
                            if field_type == bool:
                                value = value.lower() in ['true', '1', 'yes', 'y']
                            else:
                                value = field_type(value)
                        entity_data[field] = value
                    except ValueError:
                        print_warning(f"Invalid value for {field}, skipping.")

            # Create the entity
            created = self.data_service.create(entity_type, entity_data)
            if created:
                print_success(f"{config['name']} created successfully!")
                print_entity_details(created, f"Created {config['name']}")
            else:
                print_error(f"Failed to create {config['name']}")

            return True

        except Exception as e:
            print_error(f"Failed to create {entity_type}: {e}")
            return False

    def update_entity(self, entity_type: str) -> bool:
        """Update an existing entity"""
        try:
            config = self.entities[entity_type]

            # Get entity ID
            entity_id = get_input(f"Enter {config['name']} ID to update: ")
            if not entity_id.isdigit():
                print_error("Invalid ID. Please enter a number.")
                return False

            entity_id = int(entity_id)

            # Get current entity
            current = self.data_service.get_by_id(entity_type, entity_id)
            if not current:
                print_error(f"{config['name']} not found.")
                return False

            print(f"\n✏️ Update {config['name']} (ID: {entity_id})")
            print("=" * 40)
            print_entity_details(current, "Current Values")
            print("\n_Enter new values (leave blank to keep current):")

            update_data = {}
            updatable_fields = [f for f in config['headers'] if f != 'id']

            for field in updatable_fields:
                current_value = current.get(field, "N/A")
                new_value = get_input(f"{field.replace('_', ' ')} [{current_value}]: ")

                if new_value:
                    try:
                        if field in config['field_types']:
                            field_type = config['field_types'][field]
                            if field_type == bool:
                                new_value = new_value.lower() in ['true', '1', 'yes', 'y']
                            else:
                                new_value = field_type(new_value)
                        update_data[field] = new_value
                    except ValueError:
                        print_warning(f"Invalid value for {field}, keeping current value.")

            if not update_data:
                print_info("No changes made.")
                return True

            # Confirm update
            confirm = get_input("Are you sure you want to save these changes? (y/N): ")
            if confirm.lower() != 'y':
                print_info("Update cancelled.")
                return True

            # Update the entity
            updated = self.data_service.update(entity_type, entity_id, update_data)
            if updated:
                print_success(f"{config['name']} updated successfully!")
                print_entity_details(updated, f"Updated {config['name']}")
            else:
                print_error(f"Failed to update {config['name']}")

            return True

        except Exception as e:
            print_error(f"Failed to update {entity_type}: {e}")
            return False

    def delete_entity(self, entity_type: str) -> bool:
        """Delete an entity"""
        try:
            config = self.entities[entity_type]

            # Get entity ID
            entity_id = get_input(f"Enter {config['name']} ID to delete: ")
            if not entity_id.isdigit():
                print_error("Invalid ID. Please enter a number.")
                return False

            entity_id = int(entity_id)

            # Get current entity
            current = self.data_service.get_by_id(entity_type, entity_id)
            if not current:
                print_error(f"{config['name']} not found.")
                return False

            print(f"\n🗑️ Delete {config['name']} (ID: {entity_id})")
            print("=" * 40)
            print_entity_details(current, f"{config['name']} to Delete")

            # Double confirmation for delete
            print_warning(f"This will permanently delete this {config['name'].lower()}!")

            # First confirmation - type DELETE
            confirm1 = get_input("Type 'DELETE' to confirm: ")
            if confirm1 != 'DELETE':
                print_info("Delete cancelled.")
                return True

            # Second confirmation - y/N
            confirm2 = get_input("Are you absolutely sure? (y/N): ")
            if confirm2.lower() != 'y':
                print_info("Delete cancelled.")
                return True

            # Delete the entity
            success = self.data_service.delete(entity_type, entity_id)
            if success:
                print_success(f"{config['name']} deleted successfully!")
            else:
                print_error(f"Failed to delete {config['name']}")

            return True

        except Exception as e:
            print_error(f"Failed to delete {entity_type}: {e}")
            return False

    def entity_menu(self, entity_type: str) -> bool:
        """Show CRUD menu for a specific entity type"""
        config = self.entities[entity_type]

        while True:
            print(f"\n📦 {config['plural']} Management")
            print("=" * 40)

            options = [
                ("1", "📋", f"List All {config['plural']}"),
                ("2", "🔍", f"View {config['name']} Details"),
                ("3", "➕", f"Create New {config['name']}"),
                ("4", "✏️", f"Update {config['name']}"),
                ("5", "🗑️", f"Delete {config['name']}"),
                ("0", "↩️", "Back to Entity Management")
            ]

            from ui_components import print_menu_box
            print_menu_box(f"{config['plural']} Operations", options)

            choice = get_input()

            if choice == "1":
                self.list_entities(entity_type)
                pause()
            elif choice == "2":
                self.view_entity_details(entity_type)
                pause()
            elif choice == "3":
                self.create_entity(entity_type)
                pause()
            elif choice == "4":
                self.update_entity(entity_type)
                pause()
            elif choice == "5":
                self.delete_entity(entity_type)
                pause()
            elif choice == "0":
                return True
            else:
                print_error("Invalid choice. Please try again.")
                pause()
