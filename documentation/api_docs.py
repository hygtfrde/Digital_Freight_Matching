"""
API Documentation Generator

Generates REST API documentation with examples.
"""

from pathlib import Path


class APIDocsGenerator:
    """Generates API documentation"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def generate(self) -> str:
        """Generate API documentation"""
        content = """# Digital Freight Matching System - API Documentation

## Overview

The DFM API provides RESTful endpoints for managing logistics operations. Built with FastAPI, it includes automatic OpenAPI/Swagger documentation.

## Base URL
```
http://localhost:8000
```

## Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Response Format

All responses follow consistent JSON format:
```json
{
  "data": {...},
  "status": "success|error", 
  "message": "Description",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Authentication
Currently no authentication required. Implement appropriate auth for production.

## Endpoints

### System Information

#### GET / - Welcome Page
```bash
curl http://localhost:8000/
```
Returns HTML welcome page with system overview and quick links.

#### GET /analytics/summary - System Analytics
```bash
curl http://localhost:8000/analytics/summary
```

Response:
```json
{
  "entities": {
    "clients": 2,
    "locations": 16,
    "trucks": 5,
    "routes": 5,
    "orders": 12
  },
  "financial": {
    "total_daily_loss": -388.15,
    "target_daily_loss": -388.15,
    "improvement_needed": 388.15
  },
  "capacity": {
    "total_truck_capacity": 240.0,
    "total_cargo_volume": 85.5,
    "utilization_percent": 35.6
  }
}
```

### Client Management

#### GET /clients - List All Clients
```bash
curl http://localhost:8000/clients
```

Response:
```json
[
  {
    "id": 1,
    "name": "Too-Big-To-Fail Company",
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

#### GET /clients/{client_id} - Get Client Details
```bash
curl http://localhost:8000/clients/1
```

#### POST /clients - Create Client
```bash
curl -X POST http://localhost:8000/clients \\
  -H "Content-Type: application/json" \\
  -d '{"name": "New Logistics Company"}'
```

#### PUT /clients/{client_id} - Update Client
```bash
curl -X PUT http://localhost:8000/clients/1 \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Updated Company Name"}'
```

#### DELETE /clients/{client_id} - Delete Client
```bash
curl -X DELETE http://localhost:8000/clients/1
```

### Truck Management

#### GET /trucks - List All Trucks
```bash
curl http://localhost:8000/trucks
```

Response:
```json
[
  {
    "id": 1,
    "type": "standard",
    "capacity": 48.0,
    "autonomy": 800.0,
    "used_capacity": 15.5,
    "available_capacity": 32.5,
    "utilization_percent": 32.3
  }
]
```

#### GET /trucks/{truck_id} - Get Truck Details
```bash
curl http://localhost:8000/trucks/1
```

#### POST /trucks - Create Truck
```bash
curl -X POST http://localhost:8000/trucks \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "refrigerated",
    "capacity": 45.0,
    "autonomy": 850.0
  }'
```

### Route Management

#### GET /routes - List All Routes
```bash
curl http://localhost:8000/routes
```

Response:
```json
[
  {
    "id": 1,
    "origin": {"lat": 33.7490, "lng": -84.3880},
    "destiny": {"lat": 32.0835, "lng": -81.0998},
    "profitability": -77.63,
    "truck_id": 1,
    "orders_count": 2,
    "distance_km": 496.0
  }
]
```

#### GET /routes/{route_id} - Get Route Details
```bash
curl http://localhost:8000/routes/1
```

#### POST /routes - Create Route
```bash
curl -X POST http://localhost:8000/routes \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 1,
    "location_destiny_id": 2,
    "profitability": 0.0,
    "truck_id": 1
  }'
```

### Order Management

#### GET /orders - List Orders
```bash
# All orders
curl http://localhost:8000/orders

# Filter by client
curl http://localhost:8000/orders?client_id=1

# Filter by route
curl http://localhost:8000/orders?route_id=1
```

Response:
```json
[
  {
    "id": 1,
    "origin": {"lat": 33.7500, "lng": -84.3900},
    "destiny": {"lat": 32.0900, "lng": -81.1000},
    "client": {"id": 1, "name": "Too-Big-To-Fail Company"},
    "route_id": 1,
    "contract_type": "binding",
    "total_volume": 8.0,
    "total_weight": 150.0,
    "distance_km": 495.2
  }
]
```

#### POST /orders - Create Order
```bash
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 1,
    "location_destiny_id": 2,
    "client_id": 1,
    "contract_type": "third_party"
  }'
```

### Location Management

#### GET /locations - List Locations
```bash
# All locations
curl http://localhost:8000/locations

# Only marked locations
curl http://localhost:8000/locations?marked_only=true
```

#### POST /locations - Create Location
```bash
curl -X POST http://localhost:8000/locations \\
  -H "Content-Type: application/json" \\
  -d '{
    "lat": 34.0522,
    "lng": -84.2911,
    "marked": true
  }'
```

### Cargo and Package Management

#### GET /cargo - List Cargo
```bash
# All cargo
curl http://localhost:8000/cargo

# By order
curl http://localhost:8000/cargo?order_id=1

# By truck
curl http://localhost:8000/cargo?truck_id=1
```

#### GET /packages - List Packages
```bash
curl http://localhost:8000/packages?cargo_id=1
```

#### POST /packages - Create Package
```bash
curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 5.0,
    "weight": 100.0,
    "type": "standard",
    "cargo_id": 1
  }'
```

## Usage Examples

### Complete Order Processing Workflow

#### 1. Create Client
```bash
curl -X POST http://localhost:8000/clients \\
  -H "Content-Type: application/json" \\
  -d '{"name": "ABC Shipping Co"}'
```

#### 2. Create Locations
```bash
# Pickup location
curl -X POST http://localhost:8000/locations \\
  -H "Content-Type: application/json" \\
  -d '{"lat": 33.7500, "lng": -84.3900}'

# Delivery location
curl -X POST http://localhost:8000/locations \\
  -H "Content-Type: application/json" \\
  -d '{"lat": 32.0900, "lng": -81.1000}'
```

#### 3. Create Order
```bash
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 17,
    "location_destiny_id": 18,
    "client_id": 3,
    "contract_type": "third_party"
  }'
```

#### 4. Add Cargo and Packages
```bash
# Create cargo
curl -X POST http://localhost:8000/cargo \\
  -H "Content-Type: application/json" \\
  -d '{"order_id": 13}'

# Add packages
curl -X POST http://localhost:8000/packages \\
  -H "Content-Type: application/json" \\
  -d '{
    "volume": 5.0,
    "weight": 100.0,
    "type": "standard",
    "cargo_id": 13
  }'
```

#### 5. Assign to Route
```bash
curl -X PUT http://localhost:8000/orders/13 \\
  -H "Content-Type: application/json" \\
  -d '{"route_id": 1}'
```

#### 6. Check Results
```bash
# Updated route profitability
curl http://localhost:8000/routes/1

# System analytics
curl http://localhost:8000/analytics/summary
```

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful GET requests
- `201 Created`: Successful POST requests  
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server errors

### Error Response Format
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Errors

#### Invalid Data
```bash
# This returns 400 Bad Request
curl -X POST http://localhost:8000/trucks \\
  -H "Content-Type: application/json" \\
  -d '{"capacity": -10}'  # Negative capacity invalid
```

#### Resource Not Found
```bash
# This returns 404 Not Found
curl http://localhost:8000/trucks/999
```

## SDK Examples

### Python SDK
```python
import requests

class DFMClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def create_order(self, origin_id, destiny_id, client_id):
        response = requests.post(f"{self.base_url}/orders", json={
            "location_origin_id": origin_id,
            "location_destiny_id": destiny_id,
            "client_id": client_id
        })
        return response.json()
    
    def get_analytics(self):
        response = requests.get(f"{self.base_url}/analytics/summary")
        return response.json()

# Usage
client = DFMClient()
analytics = client.get_analytics()
print(f"Daily P&L: ${analytics['financial']['total_daily_loss']}")
```

### JavaScript SDK
```javascript
class DFMClient {
    constructor(base_Url = 'http://localhost:8000') {
        this.base_Url = base_Url;
    }
    
    async create_Order(origin_Id, destiny_Id, client_Id) {
        const response = await fetch(`${this.base_Url}/orders`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                location_origin_id: origin_Id,
                location_destiny_id: destiny_Id,
                client_id: client_Id
            })
        });
        return response.json();
    }
    
    async get_Analytics() {
        const response = await fetch(`${this.base_Url}/analytics/summary`);
        return response.json();
    }
}
```

## Rate Limiting and Performance

### Performance Expectations
- Standard endpoints: <500ms response time
- Analytics endpoints: <1s response time
- Bulk operations: <5s for reasonable batch sizes

### Best Practices
- Use appropriate HTTP methods (GET for reads, POST for creates)
- Include proper Content-Type headers
- Handle errors gracefully with retry logic
- Cache frequently accessed data when appropriate
- Use query parameters for filtering large datasets

## Production Considerations

### Security
- Implement authentication and authorization
- Use HTTPS in production
- Validate and sanitize all inputs
- Implement rate limiting

### Monitoring
- Log all API requests and responses
- Monitor response times and error rates
- Set up health check endpoints
- Implement proper error tracking
"""
        
        file_path = self.output_dir / "api-documentation.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)