# Digital Freight Matching

A logistics optimization system for matching freight orders to available trucks and routes.

## Quick Start

### Database Setup (Refactored - Safe Initialization)

The database setup has been refactored to prevent duplicate data seeding:

```bash
# Safe initialization (recommended)
python manage_db.py init

# Check database status
python manage_db.py status

# Verify data integrity
python manage_db.py verify
```

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed information about the safe initialization system.

### Alternative Setup Methods

```bash
# Full setup with virtual environment
python setup_dfm.py

# Simple setup
python setup_database.py

# Manual initialization
python safe_db_init.py
```

### Start the Application

```bash
# API Server
python app/main.py

# CLI Dashboard
python dashboard_menu_cli.py
```

## Core Components

### Database & API
- **app/database.py**: SQLModel-based database schema
- **app/main.py**: FastAPI server with REST endpoints
- **safe_db_init.py**: Safe database initialization (prevents duplicates)
- **manage_db.py**: CLI for database management

### Business Logic
- **dfm.py**: Digital Freight Matching core logic
- **schemas/schemas.py**: Data validation schemas
- **api.py**: Basic CRUD operations

### User Interfaces
- **dashboard_menu_cli.py**: Interactive CLI dashboard
- **dashboard_methods.py**: Dashboard implementation methods

### Setup & Utilities
- **setup_dfm.py**: Complete environment setup
- **verify_database.py**: Database verification
- **utils.py**: Shared utilities





# Are Dashboard Methods Implemented, Stubbed, or Missing?
Coverage of Dashboard Methods

Trucks

List Trucks: Yes (list_trucks)
Add Truck: Yes (add_truck)
Edit Truck: Stub (edit_truck prints "not yet implemented")
Delete Truck: Yes (delete_truck)
View Loads: Yes (view_truck_loads)
Routes

List Routes: Yes (list_routes)
Add Route: Yes (add_route)
Edit Route: Stub (edit_route)
Delete Route: Yes (delete_route)
Assign Truck: Not explicit (could be part of order/route logic, but not a direct menu item)
View Routes: Yes (view_route_details, view_route_path)
Optimize Route: Stub (optimize_route)
Orders

List Orders: Yes (list_orders)
Add Order: Yes (add_order)
Edit Order: Stub (edit_order)
Delete Order: Yes (delete_order)
Match Order: Yes (match_single_order, auto_match_orders)
Clients

List Clients: No (unless added via create_crud_menu)
Add Client: No (unless added via create_crud_menu)
Edit/Delete/View Orders: No (unless handled by create_crud_menu)
Locations

List/Add/Edit/Delete/View: No explicit menu/actions
Packages

List/Add/Edit/Delete/Assign to Cargo: No explicit menu/actions
Cargo

List/Add/Edit/Delete/Assign Packages: No explicit menu/actions
Pricing/Matching

Price Route: Yes (calculate_profitability)
Match Order: Yes
Profitability: Yes
New Route: Stub (create_route_from_pending)
Dashboard/Analytics

Summary, KPIs, Pending, Utilization, Alerts: Some support (via analytics menus/reports, but not all are shown in this snippet)
System Configuration

Load Demo Data, Clear Data, Import/Export, Database Settings, Matching Parameters, System Info: Yes (all present or stubbed)
What is Missing or Only Partially Covered:

Locations, Packages, Cargo:
There are no explicit menus or actions for these entities in your DFMDashboard.
If you want full dashboard coverage as per your matrix, you would need to add:

Menus and stub actions for Locations (list/add/edit/delete/view)
Menus and stub actions for Packages (list/add/edit/delete/assign)
Menus and stub actions for Cargo (list/add/edit/delete/assign)
Assign Truck/Assign to Cargo/Assign Packages:
Not exposed as a top-level menu action.

Clients:
You use create_crud_menu("clients",...), which may provide full CRUD, but it's not shown in detail in this snippet.

Summary Table

Feature	Supported?	Note
Trucks CRUD	Yes/Stub	Assign not explicit
Routes CRUD	Yes/Stub	Assign/Optimize as stub
Orders CRUD/Match	Yes/Stub	
Clients CRUD	Yes?	If provided by create_crud_menu
Locations CRUD	No	Not present
Packages CRUD	No	Not present
Cargo CRUD	No	Not present
Pricing/Matching	Yes/Stub	Partial/Stub for some advanced flows
Dashboard/Analytics	Partial	Depends on report/analytics menus
System Config	Yes/Stub	