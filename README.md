# Digital Freight Matching System

A logistics optimization system for matching freight orders to available truck routes, designed to convert unprofitable routes into profitable ones through intelligent order consolidation.

## Business Context

**Infinity and Beyond** logistics company has a problem:
- 5 existing routes with 4-year binding contracts
- Currently losing $388.15 per day across all routes
- Need to fill unused truck capacity with 3rd party orders
- Goal: Convert all routes from losses to profits

## Current Route Performance

| Route | Destination | Distance | Daily Loss | Truck Capacity |
|-------|-------------|----------|------------|----------------|
| 1 | Ringgold | 202 miles | -$53.51 | 48 m³ |
| 2 | Augusta | 189.2 miles | -$50.12 | 48 m³ |
| 3 | Savannah | 496 miles | -$131.40 | 48 m³ |
| 4 | Albany | 364 miles | -$96.43 | 48 m³ |
| 5 | Columbus | 214 miles | -$56.69 | 48 m³ |

**Total Daily Loss: $388.15**

## Quick Start

### 1. Setup Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(fastapi|sqlmodel|pyyaml|pytest)"
```

### 2. Initialize Database
```bash
# Initialize with contract data (safe - prevents duplicates)
python db_manager.py init

# Or force reinitialize if needed
python db_manager.py init --force
```

### 3. Verify Database
```bash
# Check database status and metrics
python db_manager.py status

# Verify data integrity
python db_manager.py verify
```

### 4. Use the System
```bash
# Interactive CLI Menu App
python cli_menu_app/main.py

# Or start API server (runs on port 8000)
python app/main.py
```

## Database Management CLI

The `db_manager.py` script provides all database operations:

```bash
# Initialize database (safe - prevents duplicates)
python db_manager.py init

# Force initialization (may create duplicates)
python db_manager.py init --force

# Show database status and metrics
python db_manager.py status

# Verify database integrity
python db_manager.py verify

# Reset database (removes all data)
python db_manager.py reset --confirm
```

## Interactive CLI Menu App

The CLI Menu App (`cli_menu_app/main.py`) provides a modern, modular interactive interface:

```bash
# Launch API with default settings (auto-detects best connection mode)
python cli_menu_app/main.py

# Force direct database mode
python cli_menu_app/main.py --mode=direct

# API mode (requires running API server on port 8000)
python cli_menu_app/main.py --mode=api --api-url=http://localhost:8000

# Production environment
python cli_menu_app/main.py --environment=production
```

**Features:**
- **Full CRUD Operations** - Create, read, update, delete all entities (trucks, orders, locations, routes, clients, packages, cargo)
- **Hybrid Data Access** - Works with both direct database and API modes
- **Interactive Menu Navigation** - User-friendly menu system with color-coded UI
- **Safety Features** - Confirmation prompts for destructive operations
- **Configuration Management** - Flexible configuration options

## Using the System

### Real-World Workflow: Converting Losses to Profits

The system is designed to solve a specific business problem: **converting $388.15 daily losses into profits** by filling unused truck capacity with third-party orders.

#### Step 1: Check Current System Status
```bash
# See the current financial situation
python db_manager.py status
```
**Expected Output:** Shows -$388.15 daily loss across 5 routes

#### Step 2: Launch the Interactive Interface
```bash
# Start the CLI Menu App for hands-on management
python cli_menu_app/main.py
```

#### Step 3: Explore Current Data
In the CLI Menu App:
1. Choose **"3. 📊 System Status & Reports"**
2. Select **"1. 📈 Financial Summary"** to see route profitability
3. Select **"2. 🚛 Truck Utilization"** to see available capacity
4. Select **"3. 📦 Order Status"** to see current orders

#### Step 4: Add Profitable Third-Party Orders
1. Choose **"2. 🏢 Entity Management"**
2. Select **"4. 📋 Order Management"**
3. Choose **"1. ➕ Create New Order"**
4. Add orders that:
   - Pick up/deliver within 1km of existing routes
   - Fit within truck capacity (48m³, 9180 lbs)
   - Complete within 10-hour time limits

#### Step 5: Run Business Validation
```bash
# Validate that all business requirements are met
python -c "
from validation.business_validator import BusinessValidator
from sqlmodel import Session
from app.database import engine, select, Order, Route, Truck

with Session(engine) as session:
    validator = BusinessValidator()
    
    orders = session.exec(select(Order)).all()
    routes = session.exec(select(Route)).all() 
    trucks = session.exec(select(Truck)).all()
    
    reports = validator.validate_all_requirements(orders, routes, trucks)
    summary = validator.generate_summary_report(reports)
    
    print(f'Overall Status: {summary[\"overall_status\"]}')
    print(f'Requirements Passed: {summary[\"passed_count\"]}/5')
    print(f'Daily P&L Improvement: Check route profitability')
"
```

### Alternative: API-Based Usage

For programmatic access or integration with other systems:

#### Step 1: Start API Server
```bash
# Start API server (runs on port 8000)
python app/main.py
```

#### Step 2: Access Web Interface
Open http://localhost:8000 in your browser to see:
- System overview and current losses
- Interactive API documentation at `/docs`
- Real-time data via REST endpoints

#### Step 3: Use REST API
```bash
# Check current routes and profitability
curl http://localhost:8000/routes

# View truck capacity utilization  
curl http://localhost:8000/trucks

# Get system analytics
curl http://localhost:8000/analytics/summary

# Add new orders via API
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"location_origin_id": 1, "location_destiny_id": 2, "client_id": 1}'
```

### Key Success Metrics to Monitor

**Financial Goals:**
- Convert -$388.15 daily loss to positive profit
- Target: >$500/day profit across all routes

**Operational Goals:**
- Truck utilization: >80% capacity usage
- Order match rate: >90% successful assignments
- Route compliance: All 5 contract routes preserved

**How to Check Progress:**
```bash
# Quick financial check
python db_manager.py status | grep "Daily Profit/Loss"

# Detailed validation report
python -m pytest tests/test_business_validator.py::TestValidationIntegration::test_validate_all_requirements -v
```

## System Architecture

```
User Input → Validation → Business Logic (DFM) → Database → Feedback
     ↑                                                        │
     └────────────────────────────────────────────────────────┘
```

### Core Components

- **CLI Menu App** (`cli_menu_app/`): Modern modular CLI interface with hybrid data access
- **Database Manager** (`db_manager.py`): Unified database operations and CLI
- **Data Models** (`app/database.py`): SQLModel-based entities
- **Business Logic** (`dfm.py`): Route matching and optimization algorithms
- **API Layer** (`app/main.py`): FastAPI REST endpoints (port 8000)
- **Database** (`logistics.db`): SQLite with contract and order data

## Database Schema

### Core Entities
- **Client**: Companies placing orders
- **Location**: Pickup and delivery coordinates  
- **Order**: Freight requests with cargo details
- **Route**: Predefined paths between locations
- **Truck**: Vehicle specifications and capacity
- **Cargo**: Shipment containers
- **Package**: Individual items with volume/weight/type

### Relationships
```
Client → Order → Cargo → Package
Location ← Order → Route → Truck
```

## Business Logic & Practical Examples

### The Core Problem
Your company has 5 trucks running daily routes that are losing money:
- **Route 1** (Atlanta → Ringgold): Losing $53.51/day, truck only 30% full
- **Route 2** (Atlanta → Augusta): Losing $50.12/day, truck only 25% full  
- **Route 3** (Atlanta → Savannah): Losing $131.40/day, truck only 40% full
- **Route 4** (Atlanta → Albany): Losing $96.43/day, truck only 35% full
- **Route 5** (Atlanta → Columbus): Losing $56.69/day, truck only 20% full

### The Solution Strategy
Fill empty truck space with profitable third-party orders that:

#### 1. **Geographic Proximity** (≤1km deviation)
```
✅ GOOD: Order pickup in Marietta (near Atlanta → Ringgold route)
❌ BAD: Order pickup in Miami (nowhere near any route)
```

#### 2. **Capacity Constraints** (48m³, 9180 lbs per truck)
```
✅ GOOD: 5 pallets, 10m³ total, 2000 lbs → Fits easily
❌ BAD: 60m³ shipment → Exceeds truck capacity
```

#### 3. **Time Windows** (10 hours max including stops)
```
✅ GOOD: 2 stops, 6-hour drive → 7 hours total (within limit)
❌ BAD: 8 stops, 8-hour drive → 12 hours total (exceeds limit)
```

#### 4. **Profitability Requirements**
```
✅ TARGET: Add orders worth $150/day to Route 1 → Convert -$53.51 to +$96.49 profit
✅ TARGET: Add orders worth $200/day to Route 3 → Convert -$131.40 to +$68.60 profit
```

### Real Example Workflow

**Scenario:** Route 1 (Atlanta → Ringgold) is losing $53.51/day

1. **Check available capacity:**
   ```bash
   python cli_menu_app/main.py
   # Navigate to: System Status → Truck Utilization
   # See: Truck 1 has 33.6m³ available space (70% unused!)
   ```

2. **Find compatible orders:**
   - Look for pickups near Atlanta or along I-75 North
   - Deliveries near Ringgold or along the route
   - Total cargo ≤ 33.6m³ and ≤ 6500 lbs remaining capacity

3. **Add profitable order:**
   ```bash
   # In CLI Menu: Entity Management → Order Management → Create New Order
   # Example: Pickup in Marietta, delivery in Dalton
   # Cargo: 8m³, 1500 lbs, pays $75
   ```

4. **Validate business rules:**
   ```bash
   python -c "from validation.business_validator import BusinessValidator; ..."
   # Confirms: ✅ Proximity OK, ✅ Capacity OK, ✅ Time OK
   ```

5. **Check profitability improvement:**
   ```bash
   python db_manager.py status
   # Route 1 now shows: -$53.51 + $75 = +$21.49 daily profit!
   ```

### Success Metrics Dashboard
Monitor these KPIs to track progress toward profitability:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Daily P&L | -$388.15 | +$500.00 | 🔴 Need +$888.15 |
| Truck Utilization | ~30% | >80% | 🔴 Need +50% |
| Route 1 Profit | -$53.51 | +$50.00 | 🔴 Need +$103.51 |
| Route 2 Profit | -$50.12 | +$50.00 | 🔴 Need +$100.12 |
| Route 3 Profit | -$131.40 | +$150.00 | 🔴 Need +$281.40 |
| Route 4 Profit | -$96.43 | +$100.00 | 🔴 Need +$196.43 |
| Route 5 Profit | -$56.69 | +$50.00 | 🔴 Need +$106.69 |

## Development

### Project Structure
```
├── app/
│   ├── database.py          # Data models and database setup
│   └── main.py             # FastAPI application (port 8000)
├── cli_menu_app/
│   ├── main.py             # CLI Menu App entry point
│   ├── menu_system.py      # Menu navigation logic
│   ├── crud_operations.py  # CRUD operations for all entities
│   ├── data_service.py     # Hybrid data access (API/direct DB)
│   └── ui_components.py    # UI utilities and colors
├── schemas/
│   └── schemas.py          # Pydantic schemas with business logic
├── db_manager.py           # Unified database manager and CLI
├── test_db_manager.py      # Comprehensive test suite
├── dfm.py                  # Core business logic
├── utils.py                # Utility functions
└── requirements.txt        # Python dependencies
```

### Running Tests

#### Prerequisites
```bash
# Activate virtual environment first
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# All testing dependencies should be installed with requirements.txt
# But if you need to install them separately:
pip install pytest pytest-cov pytest-watch pytest-xdist
```

#### Running All Tests (Recommended)
```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run tests with coverage report
python -m pytest tests/ --cov=validation --cov=schemas --cov=app --cov-report=html

# Run tests and generate coverage report in terminal
python -m pytest tests/ --cov=validation --cov=schemas --cov=app --cov-report=term-missing
```

#### Running Specific Test Files
```bash
# Business validation tests
python -m pytest tests/test_business_validator.py -v

# Database manager tests
python -m pytest tests/test_db_manager.py -v

# Route calculation tests
python -m pytest tests/test_route_calculation_service.py -v

# Order processing tests
python -m pytest tests/test_order_processor.py -v

# All validation-related tests
python -m pytest tests/test_*validator*.py -v
```

#### Running Tests Directly (Alternative)
```bash
# Individual test files can also be run directly
python tests/test_business_validator.py
python tests/test_db_manager.py

# Or use the test runner script
python run_tests.py                           # All tests
python run_tests.py test_business_validator   # Specific test
```

#### Test Categories
- **Unit Tests**: `tests/test_*.py` - Individual component testing
- **Integration Tests**: `tests/integration/` - Cross-component testing  
- **Performance Tests**: `tests/performance/` - Load and performance testing

#### Test Coverage
The test suite covers:
- ✅ Business requirement validation (5 core requirements)
- ✅ Database operations and integrity
- ✅ Route calculation algorithms
- ✅ Order processing and matching
- ✅ Cargo aggregation services
- ✅ Network caching and optimization

#### Continuous Testing
```bash
# Watch for file changes and auto-run tests (requires pytest-watch)
pip install pytest-watch
ptw tests/

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
python -m pytest tests/ -n auto
```

### Database Operations

The `DatabaseManager` class provides programmatic access:

```python
from sqlmodel import Session
from database import engine
from db_manager import DatabaseManager

with Session(engine) as session:
    db_manager = DatabaseManager(session)
    
    # Initialize database
    success = db_manager.initialize_database()
    
    # Get system status
    status = db_manager.get_system_status()
    print(f"Daily P&L: ${status.daily_profit_loss:.2f}")
    
    # Verify integrity
    counts = db_manager.verify_integrity()
```

## Performance Metrics

The system tracks key performance indicators:

- **Route Profitability**: Daily profit/loss per route
- **Truck Utilization**: Percentage of capacity used
- **Order Match Rate**: Percentage of orders successfully matched
- **Revenue Growth**: Improvement in daily profits

### Quick Win Examples

**Immediate Actions You Can Take:**

1. **Route 5 (Atlanta → Columbus) - Easiest Win**
   ```bash
   # Current: -$56.69/day, 20% capacity used
   # Opportunity: 38.4m³ available space
   # Quick win: Add 2-3 small orders worth $30-40 each
   # Result: Convert to +$50/day profit
   ```

2. **Route 2 (Atlanta → Augusta) - High Volume Opportunity**  
   ```bash
   # Current: -$50.12/day, 25% capacity used
   # Opportunity: 36m³ available space  
   # Strategy: One large shipment worth $120+
   # Result: Convert to +$70/day profit
   ```

3. **Route 3 (Atlanta → Savannah) - Biggest Impact**
   ```bash
   # Current: -$131.40/day (biggest loss)
   # Opportunity: 28.8m³ available space
   # Strategy: Premium coastal shipping orders
   # Target: $200+ in additional revenue
   # Result: Convert to +$70/day profit
   ```

### Success Criteria
- Convert all 5 routes from losses to profits
- Achieve >80% truck capacity utilization  
- Maintain >90% order match rate
- Generate >$500/day profit across all routes

**Progress Tracking:**
```bash
# Daily check - run this every morning
python db_manager.py status | grep -E "(Daily Profit|Utilization)"

# Weekly validation - comprehensive business rule check  
python -m pytest tests/test_business_validator.py -v

# Monthly review - full system analytics
python cli_menu_app/main.py
# Navigate to: System Status & Reports → Financial Summary
```

## Troubleshooting

### Common Issues

**Database not found**
```bash
# Activate virtual environment first
source venv/bin/activate  # On macOS/Linux
python db_manager.py init  # Initialize database
```

**Import errors**
```bash
# Activate virtual environment and install dependencies
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

**Database integrity issues**
```bash
# Activate virtual environment first
source venv/bin/activate  # On macOS/Linux
python db_manager.py verify  # Check integrity
python db_manager.py reset --confirm  # Reset if needed
python db_manager.py init  # Reinitialize
```

### Expected Database State
After initialization, you should see:
- Clients: 2 (Too-Big-To-Fail + Example Client)
- Locations: 16+ (Georgia cities + order locations)  
- Trucks: 5 (Contract trucks)
- Routes: 5 (Atlanta to destinations)
- Orders: 10+ (Contract + example orders)
- Daily Loss: -$388.15

### Setup Troubleshooting

**Missing dependencies (yaml, colorama, etc.)**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # On macOS/Linux

# Install missing dependencies
pip install pyyaml colorama rich

# Or reinstall all requirements
pip install -r requirements.txt --force-reinstall
```

**CLI Menu App won't start**
```bash
# Check if all dependencies are installed
python -c "import yaml, colorama, rich; print('All CLI dependencies OK')"

# If that fails, install missing packages:
pip install pyyaml colorama rich
```

**API Server warnings about deprecated methods**
```bash
# The FastAPI server will show deprecation warnings but still work
# These are non-critical and don't affect functionality
python app/main.py  # Should still start successfully on port 8000
```

**Module import errors**
```bash
# Make sure you're running from the project root directory
pwd  # Should show .../Digital_Freight_Matching

# Activate virtual environment
source venv/bin/activate

# Try running again
python cli_menu_app/main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `python test_db_manager.py`
5. Submit a pull request

## License

This project is licensed under the MIT License.