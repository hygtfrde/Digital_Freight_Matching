# Digital Freight Matching System - Technical Documentation

## System Architecture

### Layered Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ CLI Menu    │  │ FastAPI     │  │ Web UI      │            │
│  │ Interface   │  │ REST API    │  │ (Future)    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Order       │  │ Route       │  │ Validation  │            │
│  │ Processor   │  │ Optimizer   │  │ Engine      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ SQLModel    │  │ Database    │  │ Schema      │            │
│  │ ORM         │  │ Manager     │  │ Validation  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ SQLite      │  │ File System │  │ Configuration│            │
│  │ Database    │  │ Storage     │  │ Files       │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### Business Logic Layer
- **Order Processor** (`order_processor.py`): Order validation and route matching
- **Route Optimizer** (`dfm.py`): Route optimization algorithms
- **Validation Engine** (`validation/`): Business rules enforcement
- **Performance Assessor** (`performance/`): System monitoring

#### Data Access Layer
- **SQLModel ORM** (`app/database.py`): Type-safe database operations
- **Database Manager** (`db_manager.py`): Database lifecycle management
- **Schema Validation** (`schemas/schemas.py`): Pydantic models with business logic

## Algorithms

### Order-to-Route Matching

Multi-stage validation process:

```python
def match_order_to_route(order: Order, route: Route, truck: Truck) -> ValidationResult:
    # Stage 1: Geographic Proximity (≤1km)
    if not validate_proximity_constraint(order, route):
        return ValidationResult.INVALID_PROXIMITY
    
    # Stage 2: Capacity (48m³, 9180 lbs)
    if not validate_capacity_constraint(order, truck):
        return ValidationResult.INVALID_CAPACITY
    
    # Stage 3: Time (≤10 hours including stops)
    if not validate_time_constraint(route, order):
        return ValidationResult.INVALID_TIME
    
    # Stage 4: Cargo Compatibility
    if not validate_cargo_compatibility(order, truck):
        return ValidationResult.INCOMPATIBLE_CARGO
    
    return ValidationResult.VALID
```

### Distance Calculation

Uses Haversine formula for geographic accuracy:

```python
def haversine_distance(lat1, lng1, lat2, lng2) -> float:
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlng/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
```

### Profitability Optimization

```python
def optimize_route_profitability(route: Route, orders: List[Order]) -> float:
    baseline_cost = route.base_distance() * COST_PER_KM
    
    best_profit = 0
    for order_combination in valid_combinations(orders, route):
        revenue = len(order_combination) * REVENUE_PER_ORDER
        additional_cost = calculate_detour_costs(order_combination, route)
        net_profit = revenue - baseline_cost - additional_cost
        
        if net_profit > best_profit:
            best_profit = net_profit
    
    return best_profit
```

## Data Models

### Entity Relationships
```
Client ──→ Order ──→ Cargo ──→ Package
   │         │         │
   │         ▼         ▼
   │      Route ──→ Truck
   │         │
   ▼         ▼
Location ←──────────────┘
```

### Core Models

#### Location
```python
class Location(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    lat: float  # Latitude
    lng: float  # Longitude
    marked: bool = False
    
    def distance_to(self, other: "Location") -> float:
        # Haversine formula implementation
```

#### Order
```python
class Order(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    location_origin_id: int = Field(foreign_key="location.id")
    location_destiny_id: int = Field(foreign_key="location.id")
    client_id: Optional[int] = Field(foreign_key="client.id")
    route_id: Optional[int] = Field(foreign_key="route.id")
    
    def total_volume(self) -> float:
        return sum(c.total_volume() for c in self.cargo)
```

#### Truck
```python
class Truck(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    capacity: float  # 48m³ max per business requirements
    autonomy: float  # Range in km
    type: str  # "standard", "refrigerated", "hazmat"
    
    def available_capacity(self) -> float:
        used = sum(cargo.total_volume() for cargo in self.cargo_loads)
        return self.capacity - used
```

## Design Decisions

### Architecture Choices

#### SQLModel ORM
**Decision**: Use SQLModel for database operations and API validation.
**Rationale**: 
- Type safety with Python type hints
- Code reuse between database and API models
- Excellent FastAPI integration
- Superior developer experience

#### SQLite Database
**Decision**: Use SQLite for data storage.
**Rationale**:
- Zero configuration setup
- Single file portability
- Sufficient performance for expected load
- Easy development and testing

**Production Consideration**: Consider PostgreSQL for production deployment with concurrent access needs.

#### Layered Architecture
**Decision**: Clear separation between presentation, business logic, data access, and storage.
**Rationale**:
- Maintainability through separation of concerns
- Testability of business logic independent of UI/database
- Flexibility to swap implementations
- Scalability through independent layer scaling

### Algorithm Choices

#### Constraint Validation Order
**Decision**: Validate in order: proximity → capacity → time → compatibility.
**Rationale**:
- Performance: Check fastest constraints first
- User experience: Provide most relevant error messages
- Business priority: Geographic constraints are most fundamental

#### Distance Calculation
**Decision**: Use Haversine formula for geographic distances.
**Rationale**:
- Accuracy for distances up to ~1000km
- Fast mathematical calculation
- No external dependencies

**Trade-off**: Doesn't account for actual road routes, but sufficient for proximity validation.

## Performance Considerations

### Optimization Strategies
- **Database Indexing**: Foreign keys and frequently queried fields
- **Lazy Loading**: SQLModel relationships loaded on demand
- **Batch Processing**: Handle multiple orders efficiently
- **Caching**: Distance calculations and validation results

### Scalability Patterns
- **Connection Pooling**: For database access under load
- **Async Processing**: FastAPI's async capabilities
- **Horizontal Scaling**: Multiple API instances behind load balancer

### Memory Management
- Process orders in configurable batches
- Use generators for large datasets
- Implement garbage collection hints for long-running processes

## Testing Strategy

### Multi-Level Testing
- **Unit Tests**: Individual component validation
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Response time and throughput validation
- **Business Tests**: Requirements compliance validation

### Test Isolation
- Separate test database with cleanup between tests
- Mock external dependencies
- Deterministic test data for consistent results

## Security Considerations

### Input Validation
- Pydantic models for comprehensive input validation
- SQL injection prevention through ORM
- Type safety through Python type hints

### Error Handling
- Structured error responses with specific codes
- Sanitized error messages (no sensitive data exposure)
- Comprehensive logging for debugging

## Future Enhancements

### Microservices Migration
Consider splitting into services:
- Order processing service
- Route optimization service
- Analytics service
- Notification service

### Advanced Features
- Real-time route tracking
- Machine learning for demand prediction
- Integration with external routing services
- Advanced spatial indexing for large-scale operations
