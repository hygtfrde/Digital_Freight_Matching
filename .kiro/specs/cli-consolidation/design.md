# Design Document

## Overview

The consolidated CLI system will streamline the Digital Freight Matching application by removing redundant components and focusing on core business functionality. The design maintains the existing SQLModel database schema and DFM business logic while providing a single, efficient command-line interface for freight matching operations.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Application                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Main CLI      │  │  Order Matcher  │  │  Database   │ │
│  │   Interface     │  │   (dfm.py)      │  │  Manager    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Database Layer                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              SQLModel Schema                            │ │
│  │  Location | Order | Route | Truck | Cargo | Package    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input → CLI Parser → Business Logic → Database → Response
     ↑                                                    │
     └────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Consolidated CLI Interface (`dfm_cli.py`)

**Purpose**: Single entry point for all system operations
**Replaces**: `dashboard_menu_cli.py`, `dashboard_methods.py`

**Core Operations**:
- System status and overview
- Order processing and matching
- Route management and optimization
- Database management

**Interface Design**:
```
DFM System v2.0
================
Current Status: 5 routes, -$388.15/day loss, 3 pending orders

Commands:
  status          - Show system overview
  match [order]   - Match order to routes  
  routes          - Manage routes
  orders          - Manage orders
  init            - Initialize database
  help            - Show help
  exit            - Exit system

dfm> _
```

### 2. Database Manager (`db_manager.py`)

**Purpose**: Unified database operations
**Replaces**: `safe_db_init.py`, `simple_db_init.py`, `unified_db_init.py`, `init_contract_data.py`

**Key Methods**:
```python
class DatabaseManager:
    def initialize_database(self) -> bool
    def verify_integrity(self) -> Dict[str, int]
    def get_system_status(self) -> SystemStatus
    def reset_database(self, confirm: bool = False) -> bool
```

### 3. Order Processing Engine (`order_processor.py`)

**Purpose**: Handle order matching with business constraints
**Extends**: Existing `dfm.py` logic

**Key Methods**:
```python
class OrderProcessor:
    def validate_order_format(self, order_data: dict) -> bool
    def check_proximity_constraint(self, order: Order, route: Route) -> Tuple[bool, float]
    def calculate_time_impact(self, order: Order, route: Route) -> float
    def process_order_request(self, order_data: dict) -> MatchResult
```

**Key Methods**:
```python
class RouteOptimizer:
    def calculate_route_profitability(self, route: Route) -> float
    def suggest_order_assignments(self) -> List[OrderAssignment]
    def create_new_route_from_pending(self) -> Optional[Route]
    def optimize_route_sequence(self, route: Route) -> Route
```

## Data Models

### Enhanced Order Format Support

The system will handle the specified order format:
```json
{
  "cargo": {
    "packages": [[volume_cbm, weight_pounds, "type"], ...]
  },
  "pick-up": {
    "latitude": 33.754413815792205,
    "longitude": -84.3875298776525
  },
  "drop-off": {
    "latitude": 34.87433824316913,
    "longitude": -85.08447506395166
  }
}
```

### Route Format Support

Routes will be represented as:
```json
{
  "route": [
    {
      "latitude": 33.754413815792205,
      "longitude": -84.3875298776525
    }
  ]
}
```

### System Status Model

```python
@dataclass
class SystemStatus:
    total_routes: int
    daily_profit_loss: float
    pending_orders: int
    truck_utilization: float
    active_contracts: int
    last_updated: datetime
```

## Error Handling

### Input Validation
- **Order Format Validation**: Verify required fields and data types
- **Coordinate Validation**: Ensure latitude/longitude are within valid ranges
- **Capacity Validation**: Check volume and weight constraints
- **Time Validation**: Verify route time constraints

### Business Rule Enforcement
- **Proximity Constraint**: Reject orders outside 1km limit
- **Capacity Constraint**: Prevent overloading trucks
- **Time Constraint**: Enforce 10-hour daily limit
- **Profitability Constraint**: Ensure new routes are profitable

### Error Recovery
- **Database Errors**: Rollback transactions and provide recovery options
- **Calculation Errors**: Fallback to safe defaults and log issues
- **Input Errors**: Clear error messages with correction guidance

## Testing Strategy

### Unit Tests
- **Order Processing**: Test proximity calculations, capacity checks, time calculations
- **Route Optimization**: Test profitability calculations, route creation
- **Database Operations**: Test initialization, data integrity, error handling
- **CLI Interface**: Test command parsing, input validation, output formatting

### Integration Tests
- **End-to-End Order Flow**: From input to database storage
- **Route Matching**: Complete order-to-route assignment process
- **Database Initialization**: Full system setup from clean state
- **Error Scenarios**: Invalid inputs, constraint violations, system failures

### Business Logic Tests
- **1km Proximity Rule**: Verify distance calculations and constraints
- **Capacity Management**: Test volume and weight limit enforcement
- **Time Calculations**: Verify 15-minute stops and deviation time
- **Profitability Rules**: Test cost calculations and profit requirements

### Performance Tests
- **Order Processing Speed**: Measure matching algorithm performance
- **Database Query Performance**: Test with realistic data volumes
- **Memory Usage**: Monitor resource consumption during operations

## Implementation Phases

### Phase 1: Core Consolidation
1. Create unified CLI interface
2. Consolidate database initialization
3. Remove duplicate scripts
4. Implement basic order processing

### Phase 2: Business Logic Enhancement
1. Implement precise proximity checking (1km constraint)
2. Add time calculation with 15-minute stops
3. Enhance profitability calculations
4. Add route optimization features

### Phase 3: System Polish
1. Add comprehensive error handling
2. Implement data validation
3. Add system monitoring and status
4. Create user documentation

## File Structure Changes

### Files to Remove
- `simple_db_init.py` (replaced by `db_manager.py`)
- `unified_db_init.py` (replaced by `db_manager.py`)
- `init_contract_data.py` (integrated into `db_manager.py`)
- `dashboard_menu_cli.py` (replaced by `dfm_cli.py`)
- `dashboard_methods.py` (functionality moved to specialized modules)

### Files to Create
- `dfm_cli.py` - Main CLI interface
- `db_manager.py` - Unified database management
- `order_processor.py` - Order processing and validation
- `route_optimizer.py` - Route optimization and profitability

### Files to Preserve
- `app/database.py` - SQLModel schema (unchanged)
- `dfm.py` - Core business logic (enhanced)
- `schemas/schemas.py` - Data validation schemas
- `safe_db_init.py` - Keep as backup initialization method

## Configuration Management

### Cost Data Integration
- Support for Mr. Lightyear's cost spreadsheet updates
- Configurable cost-per-mile values
- Dynamic profitability recalculation

### System Parameters
```python
class SystemConfig:
    MAX_DEVIATION_KM = 1.0
    PICKUP_DROPOFF_TIME_MINUTES = 15
    MAX_ROUTE_HOURS = 10
    BREAK_AFTER_HOURS = 4
    BREAK_DURATION_MINUTES = 30
    COST_PER_MILE = 1.50  # Updated from spreadsheet
```

## Security Considerations

### Data Validation
- Sanitize all user inputs
- Validate coordinate ranges
- Check for SQL injection in dynamic queries

### Access Control
- Simple operator-level access (no authentication needed for CLI)
- File system permissions for database access
- Audit logging for critical operations

## Monitoring and Logging

### System Metrics
- Order processing success rate
- Route utilization percentages
- Daily profit/loss tracking
- System performance metrics

### Audit Trail
- Order creation and modification
- Route assignments and changes
- Database initialization events
- Error occurrences and resolutions