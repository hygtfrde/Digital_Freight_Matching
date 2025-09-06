"""
Examples and Tutorials Generator

Generates practical examples and step-by-step tutorials.
"""

from pathlib import Path


class ExamplesGenerator:
    """Generates examples and tutorials"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def generate(self) -> str:
        """Generate examples and tutorials"""
        content = """# Digital Freight Matching System - Examples and Tutorials

## Overview

This document provides step-by-step tutorials and real-world examples for using the Digital Freight Matching system effectively.

## Tutorial 1: Basic Order Processing

### Scenario
ABC Logistics needs to ship 8m³ of standard cargo from Atlanta to Savannah.

### Step 1: Check System Status
```bash
python db_manager.py status
```

Expected output:
```
=== Digital Freight Matching System Status ===
Clients: 2
Trucks: 5 (Total capacity: 240.0 m³)
Routes: 5 (Total daily loss: -$388.15)
Orders: 10
```

### Step 2: Create the Order

#### Via API
```bash
# Create client
curl -X POST http://localhost:8000/clients \\
  -H "Content-Type: application/json" \\
  -d '{"name": "ABC Logistics"}'

# Create pickup location (near Atlanta)
curl -X POST http://localhost:8000/locations \\
  -H "Content-Type: application/json" \\
  -d '{"lat": 33.7500, "lng": -84.3900}'

# Create delivery location (near Savannah)
curl -X POST http://localhost:8000/locations \\
  -H "Content-Type: application/json" \\
  -d '{"lat": 32.0900, "lng": -81.1000}'

# Create order
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 17,
    "location_destiny_id": 18,
    "client_id": 3,
    "contract_type": "third_party"
  }'
```

#### Via CLI
```bash
python cli_menu_app/main.py
# Navigate: Manage Orders → Create New Order
# Follow the guided prompts
```

### Step 3: Add Cargo
```bash
# Create cargo container
curl -X POST http://localhost:8000/cargo \\
  -H "Content-Type: application/json" \\
  -d '{"order_id": 13}'

# Add packages
curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 5.0,
    "weight": 120.0,
    "type": "standard",
    "cargo_id": 13
  }'

curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 3.0,
    "weight": 80.0,
    "type": "standard",
    "cargo_id": 13
  }'
```

### Step 4: Validate and Assign
```bash
# Check order details
curl http://localhost:8000/orders/13

# Assign to Atlanta-Savannah route (Route 1)
curl -X PUT http://localhost:8000/orders/13 \\
  -H "Content-Type: application/json" \\
  -d '{"route_id": 1}'

# Check updated route profitability
curl http://localhost:8000/routes/1
```

### Expected Results
- Order successfully created and assigned
- Route profitability improved (less negative or positive)
- Truck utilization increased
- No constraint violations

## Tutorial 2: Constraint Validation

### Scenario: Understanding Why Orders Fail

#### Example 1: Proximity Violation
```bash
# Create location too far from routes (Miami)
curl -X POST http://localhost:8000/locations \\
  -H "Content-Type: application/json" \\
  -d '{"lat": 25.7617, "lng": -80.1918}'

# Create order with distant pickup
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 19,
    "location_destiny_id": 2,
    "client_id": 3
  }'
```

**Result**: Order will fail proximity validation (>1km from route).

#### Example 2: Capacity Violation
```bash
# Create oversized package (50m³ > 48m³ truck capacity)
curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 50.0,
    "weight": 100.0,
    "type": "standard",
    "cargo_id": 14
  }'
```

**Result**: Order will fail capacity validation.

#### Example 3: Cargo Compatibility
```bash
# Try mixing hazmat and fragile cargo
# This should fail compatibility validation
```

### Validation Testing
```python
# Test order validation programmatically
python -c "
from order_processor import OrderProcessor
from app.database import get_session, Order, Route, Truck
from sqlmodel import Session

with Session(engine) as session:
    processor = OrderProcessor()
    order = session.get(Order, 13)
    route = session.get(Route, 1)
    truck = session.get(Truck, 1)
    
    result = processor.validate_order_for_route(order, route, truck)
    print(f'Valid: {result.is_valid}')
    for error in result.errors:
        print(f'Error: {error.result} - {error.message}')
"
```

## Tutorial 3: Profitability Optimization

### Scenario: Maximizing Route Profitability

#### Step 1: Analyze Current Performance
```python
python -c "
from app.database import get_session, Route
from sqlmodel import Session, select

with Session(engine) as session:
    routes = session.exec(select(Route)).all()
    total_loss = sum(r.profitability for r in routes)
    
    print('Current Route Performance:')
    for route in routes:
        print(f'Route {route.id}: \${route.profitability:.2f}')
    print(f'Total Daily Loss: \${total_loss:.2f}')
"
```

#### Step 2: Add Multiple Compatible Orders
```bash
# Create high-value order 1
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 1,
    "location_destiny_id": 2,
    "client_id": 3,
    "contract_type": "premium"
  }'

# Add 15m³ cargo (good utilization)
curl -X POST http://localhost:8000/cargo \\
  -H "Content-Type: application/json" \\
  -d '{"order_id": 16}'

curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 15.0,
    "weight": 300.0,
    "type": "standard",
    "cargo_id": 15
  }'

# Create compatible fragile order
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 1,
    "location_destiny_id": 2,
    "client_id": 3,
    "contract_type": "fragile_handling"
  }'

curl -X POST http://localhost:8000/cargo \\
  -H "Content-Type: application/json" \\
  -d '{"order_id": 17}'

curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 10.0,
    "weight": 150.0,
    "type": "fragile",
    "cargo_id": 16
  }'
```

#### Step 3: Assign and Analyze Impact
```bash
# Assign both orders to Route 1
curl -X PUT http://localhost:8000/orders/16 \\
  -H "Content-Type: application/json" \\
  -d '{"route_id": 1}'

curl -X PUT http://localhost:8000/orders/17 \\
  -H "Content-Type: application/json" \\
  -d '{"route_id": 1}'

# Check improvement
curl http://localhost:8000/analytics/summary
```

## Tutorial 4: System Validation and Testing

### Business Requirements Validation
```python
# Run comprehensive validation
python -c "
from validation.business_validator import BusinessValidator
from app.database import get_session, Order, Route, Truck
from sqlmodel import Session, select

with Session(engine) as session:
    validator = BusinessValidator()
    
    orders = session.exec(select(Order)).all()
    routes = session.exec(select(Route)).all()
    trucks = session.exec(select(Truck)).all()
    
    reports = validator.validate_all_requirements(orders, routes, trucks)
    
    print('Business Requirements Validation:')
    for report in reports:
        print(f'Requirement {report.requirement_id}: {report.status.value.upper()}')
        print(f'  {report.details}')
        if report.recommendations:
            for rec in report.recommendations:
                print(f'  - {rec}')
        print()
"
```

### Performance Testing
```python
# Test system performance
python -c "
from performance.performance_assessor import PerformanceAssessor
from app.database import get_session, Order, Route, Truck
from sqlmodel import Session, select

with Session(engine) as session:
    assessor = PerformanceAssessor()
    
    orders = session.exec(select(Order)).all()[:5]
    routes = session.exec(select(Route)).all()
    trucks = session.exec(select(Truck)).all()
    
    metrics = assessor.profile_order_processing(orders, routes, trucks)
    
    print('Performance Assessment:')
    print(f'Execution Time: {metrics.execution_time_ms:.1f}ms')
    print(f'Memory Usage: {metrics.memory_usage_mb:.1f}MB')
    print(f'Success: {metrics.success}')
    
    meets_req = metrics.execution_time_ms <= 5000
    print(f'Meets 5-second requirement: {meets_req}')
"
```

## Tutorial 5: Advanced Scenarios

### Cargo Type Compatibility Testing
```python
# Test cargo compatibility rules
python -c "
from schemas.schemas import Cargo, Package, CargoType

# Hazmat cargo
hazmat_cargo = Cargo(id=1, order_id=1, packages=[
    Package(id=1, volume=5.0, weight=100.0, type=CargoType.HAZMAT, cargo_id=1)
])

# Fragile cargo
fragile_cargo = Cargo(id=2, order_id=2, packages=[
    Package(id=2, volume=3.0, weight=50.0, type=CargoType.FRAGILE, cargo_id=2)
])

# Test compatibility
compatible = hazmat_cargo.is_compatible_with(fragile_cargo)
print(f'Hazmat + Fragile compatible: {compatible}')
print(f'Hazmat types: {hazmat_cargo.get_types()}')
print(f'Fragile types: {fragile_cargo.get_types()}')
"
```

### Truck Type Requirements
```python
# Test truck-cargo compatibility
python -c "
from schemas.schemas import Truck, Cargo, Package, CargoType

# Standard truck
standard_truck = Truck(
    id=1, capacity=48.0, autonomy=800.0, type='standard', 
    routes=[], cargo_loads=[]
)

# Refrigerated cargo
refrig_cargo = Cargo(id=1, order_id=1, packages=[
    Package(id=1, volume=10.0, weight=200.0, type=CargoType.REFRIGERATED, cargo_id=1)
])

# Test compatibility
compatible = standard_truck.is_compatible_with_cargo(refrig_cargo)
print(f'Standard truck + Refrigerated cargo: {compatible}')

# Refrigerated truck
refrig_truck = Truck(
    id=2, capacity=45.0, autonomy=850.0, type='refrigerated',
    routes=[], cargo_loads=[]
)
compatible = refrig_truck.is_compatible_with_cargo(refrig_cargo)
print(f'Refrigerated truck + Refrigerated cargo: {compatible}')
"
```

## Common Workflows

### Daily Operations Checklist
```bash
# 1. Check system status
python db_manager.py status

# 2. Review overnight orders
curl http://localhost:8000/orders

# 3. Check route profitability
curl http://localhost:8000/routes

# 4. Run business validation
python validation/business_validator.py

# 5. Check performance metrics
python performance/performance_assessor.py

# 6. Review system analytics
curl http://localhost:8000/analytics/summary
```

### Troubleshooting Workflow
```bash
# 1. Check if order fails validation
python -c "
# Test specific order validation
# (Insert validation code here)
"

# 2. Verify system integrity
python db_manager.py verify

# 3. Check logs for errors
tail -f logs/dfm-api.log  # If using production setup

# 4. Test API connectivity
curl http://localhost:8000/

# 5. Run integration tests
python tests/integration/test_integration_suite.py
```

## Best Practices

### Order Creation
- Always validate locations are within 1km of route paths
- Check available truck capacity before creating large orders
- Consider cargo type compatibility when planning shipments
- Use meaningful client names and order references

### Performance Optimization
- Process orders in batches for better performance
- Cache frequently accessed route and location data
- Monitor memory usage during bulk operations
- Use database indexes for common queries

### Error Handling
- Always validate orders before assignment
- Implement retry logic for transient failures
- Log all validation errors for analysis
- Provide clear error messages to users

### Monitoring
- Regularly check system analytics for trends
- Monitor truck utilization rates
- Track profitability improvements over time
- Set up alerts for constraint violations

## Integration Examples

### Python Integration
```python
# Complete order processing example
import requests

class DFMIntegration:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def process_order(self, pickup_lat, pickup_lng, delivery_lat, delivery_lng, 
                     cargo_volume, cargo_weight, client_name):
        # Create client
        client_resp = requests.post(f"{self.base_url}/clients", 
                                  json={"name": client_name})
        client_id = client_resp.json()["id"]
        
        # Create locations
        pickup_resp = requests.post(f"{self.base_url}/locations",
                                  json={"lat": pickup_lat, "lng": pickup_lng})
        pickup_id = pickup_resp.json()["id"]
        
        delivery_resp = requests.post(f"{self.base_url}/locations",
                                    json={"lat": delivery_lat, "lng": delivery_lng})
        delivery_id = delivery_resp.json()["id"]
        
        # Create order
        order_resp = requests.post(f"{self.base_url}/orders", json={
            "location_origin_id": pickup_id,
            "location_destiny_id": delivery_id,
            "client_id": client_id,
            "contract_type": "third_party"
        })
        order_id = order_resp.json()["id"]
        
        # Add cargo
        cargo_resp = requests.post(f"{self.base_url}/cargo",
                                 json={"order_id": order_id})
        cargo_id = cargo_resp.json()["id"]
        
        # Add package
        requests.post(f"{self.base_url}/packages", json={
            "volume": cargo_volume,
            "weight": cargo_weight,
            "type": "standard",
            "cargo_id": cargo_id
        })
        
        return order_id

# Usage
dfm = DFMIntegration()
order_id = dfm.process_order(
    pickup_lat=33.7500, pickup_lng=-84.3900,
    delivery_lat=32.0900, delivery_lng=-81.1000,
    cargo_volume=8.0, cargo_weight=200.0,
    client_name="Integration Test Client"
)
print(f"Created order: {order_id}")
```

This comprehensive tutorial collection provides practical guidance for all major system operations and real-world scenarios.
"""
        
        file_path = self.output_dir / "examples-and-tutorials.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)