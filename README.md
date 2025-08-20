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

### 1. Initialize Database
```bash
# Initialize with contract data (safe - prevents duplicates)
python db_manager.py init

# Or force reinitialize if needed
python db_manager.py init --force
```

### 2. Verify Database
```bash
# Check database status and metrics
python db_manager.py status

# Verify data integrity
python db_manager.py verify
```

### 3. Use the System
```bash
# Interactive CLI Dashboard
python cli_dashboard.py

# Or start API server
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

## Interactive CLI Dashboard

The `cli_dashboard.py` provides a comprehensive interactive interface:

```bash
# Launch interactive dashboard
python cli_dashboard.py
```

**Features:**
- **Database Management** - Initialize, verify, reset database
- **System Status & Reports** - Comprehensive analytics and metrics
- **System Operations** - Configuration and data management
- **Real-time Monitoring** - Live system status and health checks

## System Architecture

```
User Input → Validation → Business Logic (DFM) → Database → Feedback
     ↑                                                        │
     └────────────────────────────────────────────────────────┘
```

### Core Components

- **Database Manager** (`db_manager.py`): Unified database operations and CLI
- **Data Models** (`app/database.py`): SQLModel-based entities
- **Business Logic** (`dfm.py`): Route matching and optimization algorithms
- **API Layer** (`app/main.py`): FastAPI REST endpoints
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

## Business Logic

### Matching Criteria
1. **Geographic Proximity**: Order locations near route path (≤1km deviation)
2. **Capacity Constraints**: Total cargo fits in truck capacity
3. **Time Windows**: Pickup/delivery within route schedule
4. **Cargo Compatibility**: No conflicting cargo types (hazmat, fragile, etc.)

### Optimization Goals
1. **Maximize Revenue**: Select highest-paying compatible orders
2. **Minimize Detours**: Prefer orders along existing route
3. **Balance Load**: Distribute weight evenly across trucks
4. **Maintain Schedule**: Stay within time constraints

## Development

### Project Structure
```
├── app/
│   ├── database.py          # Data models and database setup
│   └── main.py             # FastAPI application
├── schemas/
│   └── schemas.py          # Pydantic schemas with business logic
├── db_manager.py           # Unified database manager and CLI
├── cli_dashboard.py        # Interactive CLI dashboard
├── test_db_manager.py      # Comprehensive test suite
├── dfm.py                  # Core business logic
├── utils.py                # Utility functions
└── requirements.txt        # Python dependencies
```

### Running Tests
```bash
# Test database manager (comprehensive test suite)
python test_db_manager.py

# Test business logic  
python dfm.py

# Interactive system management
python cli_dashboard.py
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

### Success Criteria
- Convert all 5 routes from losses to profits
- Achieve >80% truck capacity utilization
- Maintain >90% order match rate
- Generate >$500/day profit across all routes

## Troubleshooting

### Common Issues

**Database not found**
```bash
python db_manager.py init  # Initialize database
```

**Import errors**
```bash
pip install -r requirements.txt  # Install dependencies
```

**Database integrity issues**
```bash
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `python test_db_manager.py`
5. Submit a pull request

## License

This project is licensed under the MIT License.