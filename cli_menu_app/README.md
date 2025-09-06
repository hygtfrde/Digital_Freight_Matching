# CLI Menu Application

Modular CLI Dashboard for the Digital Freight Matching System.

## Structure

- **main.py** - Main entry point with argument parsing
- **menu_system.py** - Menu navigation and display logic
- **crud_operations.py** - CRUD operations for all entities
- **ui_components.py** - UI utilities, colors, and formatting functions
- **data_service.py** - Hybrid data service supporting both API and direct DB access

## Usage

```bash
# Run with default settings
python main.py

# Direct database mode
python main.py --mode=direct

# API mode 
python main.py --mode=api --api-url=http://localhost:8000

# Use production environment
python main.py --environment=production
```

## Features

- ✅ Modular architecture
- ✅ Hybrid data access (API + Direct DB)
- ✅ Full CRUD operations for all entities
- ✅ Interactive menu navigation
- ✅ Color-coded UI
- ✅ Error handling and validation
- ✅ Configuration management

## Entities Supported

- Trucks
- Orders  
- Locations
- Routes
- Clients
- Packages
- Cargo

Each entity supports full CRUD operations with safety features like confirmation prompts for deletions.