#!/usr/bin/env python3
"""
Digital Freight Matcher API Server
FastAPI application for the freight matching system
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import List, Optional
import uvicorn
import sys
import os

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.database import (
        Client,
        Location,
        Order,
        Route,
        Truck,
        Cargo,
        Package,
        CargoType,
        get_session,
        create_tables,
        engine
    )
except ImportError:
    # Fallback for direct execution
    from database import (
        Client,
        Location,
        Order,
        Route,
        Truck,
        Cargo,
        Package,
        CargoType,
        get_session,
        create_tables,
        engine
    )

# Create FastAPI app
app = FastAPI(
    title="Digital Freight Matcher API",
    description="API for matching freight orders to optimize truck routes and profitability",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    create_tables()
    # Safe initialization - only seeds data if not already present
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from safe_db_init import SafeDataIngestion
        
        with Session(engine) as session:
            ingestion = SafeDataIngestion(session)
            ingestion.initialize_safely()
    except Exception as e:
        print(f"Warning: Could not run safe initialization: {e}")
        # Continue anyway - tables are created

# Root endpoint with welcome message
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head>
            <title>Digital Freight Matcher</title>
        </head>
        <body>
            <h1>Digital Freight Matcher API</h1>
            <p>Welcome to the Digital Freight Matcher system!</p>
            <p><strong>Current Status:</strong> 5 routes losing $388.15/day total</p>
            <p><strong>Goal:</strong> Fill unused truck capacity with 3rd party orders</p>
            <h2>Quick Links:</h2>
            <ul>
                <li><a href="/docs">API Documentation (Swagger UI)</a></li>
                <li><a href="/redoc">Alternative API Docs (ReDoc)</a></li>
                <li><a href="/clients">View Clients</a></li>
                <li><a href="/routes">View Routes</a></li>
                <li><a href="/trucks">View Trucks</a></li>
                <li><a href="/orders">View Orders</a></li>
            </ul>
            <h2>Business Context:</h2>
            <p>Your company (Infinity and Beyond) has a 4-year binding contract with Too-Big-To-Fail Company.</p>
            <p>The contract routes are currently unprofitable, but you can add 3rd party orders to the same routes to improve profitability.</p>
        </body>
    </html>
    """

# Client endpoints
@app.get("/clients", response_model=List[dict])
def get_clients(session: Session = Depends(get_session)):
    """Get all clients"""
    clients = session.exec(select(Client)).all()
    return [{"id": c.id, "name": c.name, "created_at": c.created_at} for c in clients]

@app.get("/clients/{client_id}")
def get_client(client_id: int, session: Session = Depends(get_session)):
    """Get specific client with their orders"""
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    orders = session.exec(select(Order).where(Order.client_id == client_id)).all()
    return {
        "id": client.id,
        "name": client.name,
        "created_at": client.created_at,
        "orders_count": len(orders),
        "orders": [{"id": o.id, "route_id": o.route_id} for o in orders]
    }

# Location endpoints
@app.get("/locations")
def get_locations(marked_only: bool = False, session: Session = Depends(get_session)):
    """Get all locations, optionally filter to marked locations only"""
    query = select(Location)
    if marked_only:
        query = query.where(Location.marked == True)
    
    locations = session.exec(query).all()
    return [{"id": l.id, "lat": l.lat, "lng": l.lng, "marked": l.marked} for l in locations]

# Truck endpoints
@app.get("/trucks")
def get_trucks(session: Session = Depends(get_session)):
    """Get all trucks with capacity information"""
    trucks = session.exec(select(Truck)).all()
    result = []
    
    for truck in trucks:
        # Calculate utilization
        cargo_loads = session.exec(select(Cargo).where(Cargo.truck_id == truck.id)).all()
        used_capacity = sum(cargo.total_volume() for cargo in cargo_loads)
        available_capacity = truck.capacity - used_capacity
        utilization = (used_capacity / truck.capacity * 100) if truck.capacity > 0 else 0
        
        result.append({
            "id": truck.id,
            "type": truck.type,
            "capacity": truck.capacity,
            "autonomy": truck.autonomy,
            "used_capacity": used_capacity,
            "available_capacity": available_capacity,
            "utilization_percent": round(utilization, 1)
        })
    
    return result

@app.get("/trucks/{truck_id}")
def get_truck_details(truck_id: int, session: Session = Depends(get_session)):
    """Get detailed truck information including assigned routes and cargo"""
    truck = session.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    routes = session.exec(select(Route).where(Route.truck_id == truck_id)).all()
    cargo_loads = session.exec(select(Cargo).where(Cargo.truck_id == truck_id)).all()
    
    return {
        "id": truck.id,
        "type": truck.type,
        "capacity": truck.capacity,
        "autonomy": truck.autonomy,
        "routes": [{"id": r.id, "profitability": r.profitability} for r in routes],
        "cargo_loads": [{"id": c.id, "order_id": c.order_id, "volume": c.total_volume(), "weight": c.total_weight()} for c in cargo_loads]
    }

# Route endpoints
@app.get("/routes")
def get_routes(session: Session = Depends(get_session)):
    """Get all routes with profitability and location information"""
    routes = session.exec(select(Route)).all()
    result = []
    
    for route in routes:
        origin = session.get(Location, route.location_origin_id)
        destiny = session.get(Location, route.location_destiny_id)
        orders = session.exec(select(Order).where(Order.route_id == route.id)).all()
        
        result.append({
            "id": route.id,
            "origin": {"lat": origin.lat, "lng": origin.lng} if origin else None,
            "destiny": {"lat": destiny.lat, "lng": destiny.lng} if destiny else None,
            "profitability": route.profitability,
            "truck_id": route.truck_id,
            "orders_count": len(orders),
            "distance_km": round(route.base_distance(), 1) if origin and destiny else None
        })
    
    return result

@app.get("/routes/{route_id}")
def get_route_details(route_id: int, session: Session = Depends(get_session)):
    """Get detailed route information"""
    route = session.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    origin = session.get(Location, route.location_origin_id)
    destiny = session.get(Location, route.location_destiny_id)
    orders = session.exec(select(Order).where(Order.route_id == route_id)).all()
    truck = session.get(Truck, route.truck_id) if route.truck_id else None
    
    return {
        "id": route.id,
        "origin": {"id": origin.id, "lat": origin.lat, "lng": origin.lng} if origin else None,
        "destiny": {"id": destiny.id, "lat": destiny.lat, "lng": destiny.lng} if destiny else None,
        "profitability": route.profitability,
        "distance_km": round(route.base_distance(), 1) if origin and destiny else None,
        "truck": {"id": truck.id, "type": truck.type, "capacity": truck.capacity} if truck else None,
        "orders": [{"id": o.id, "client_id": o.client_id, "contract_type": o.contract_type} for o in orders]
    }

# Order endpoints
@app.get("/orders")
def get_orders(client_id: Optional[int] = None, route_id: Optional[int] = None, session: Session = Depends(get_session)):
    """Get orders, optionally filtered by client or route"""
    query = select(Order)
    
    if client_id:
        query = query.where(Order.client_id == client_id)
    if route_id:
        query = query.where(Order.route_id == route_id)
    
    orders = session.exec(query).all()
    result = []
    
    for order in orders:
        origin = session.get(Location, order.location_origin_id)
        destiny = session.get(Location, order.location_destiny_id)
        client = session.get(Client, order.client_id) if order.client_id else None
        cargo_loads = session.exec(select(Cargo).where(Cargo.order_id == order.id)).all()
        
        total_volume = sum(cargo.total_volume() for cargo in cargo_loads)
        total_weight = sum(cargo.total_weight() for cargo in cargo_loads)
        
        result.append({
            "id": order.id,
            "origin": {"lat": origin.lat, "lng": origin.lng} if origin else None,
            "destiny": {"lat": destiny.lat, "lng": destiny.lng} if destiny else None,
            "client": {"id": client.id, "name": client.name} if client else None,
            "route_id": order.route_id,
            "contract_type": order.contract_type,
            "total_volume": total_volume,
            "total_weight": total_weight,
            "distance_km": round(order.total_distance(), 1) if origin and destiny else None
        })
    
    return result

# Analytics endpoints
@app.get("/analytics/summary")
def get_analytics_summary(session: Session = Depends(get_session)):
    """Get overall system analytics"""
    clients = session.exec(select(Client)).all()
    locations = session.exec(select(Location)).all()
    trucks = session.exec(select(Truck)).all()
    routes = session.exec(select(Route)).all()
    orders = session.exec(select(Order)).all()
    packages = session.exec(select(Package)).all()
    
    # Calculate financial metrics
    total_daily_loss = sum(route.profitability for route in routes)
    
    # Calculate capacity metrics
    total_truck_capacity = sum(truck.capacity for truck in trucks)
    total_cargo_volume = sum(pkg.volume for pkg in packages)
    utilization = (total_cargo_volume / total_truck_capacity * 100) if total_truck_capacity > 0 else 0
    
    # Contract vs example orders
    contract_orders = [o for o in orders if o.contract_type]
    example_orders = [o for o in orders if not o.contract_type]
    
    return {
        "entities": {
            "clients": len(clients),
            "locations": len(locations),
            "trucks": len(trucks),
            "routes": len(routes),
            "orders": len(orders),
            "packages": len(packages)
        },
        "financial": {
            "total_daily_loss": round(total_daily_loss, 2),
            "target_daily_loss": -388.15,
            "loss_matches_target": abs(total_daily_loss - (-388.15)) < 1.0
        },
        "capacity": {
            "total_truck_capacity": total_truck_capacity,
            "used_capacity": total_cargo_volume,
            "available_capacity": total_truck_capacity - total_cargo_volume,
            "utilization_percent": round(utilization, 1)
        },
        "orders": {
            "contract_orders": len(contract_orders),
            "example_orders": len(example_orders),
            "total_orders": len(orders)
        }
    }

@app.get("/analytics/routes")
def get_route_analytics(session: Session = Depends(get_session)):
    """Get detailed route analytics"""
    routes = session.exec(select(Route)).all()
    result = []
    
    for i, route in enumerate(routes, 1):
        origin = session.get(Location, route.location_origin_id)
        destiny = session.get(Location, route.location_destiny_id)
        orders = session.exec(select(Order).where(Order.route_id == route.id)).all()
        truck = session.get(Truck, route.truck_id) if route.truck_id else None
        
        # Calculate cargo metrics for this route
        total_volume = 0
        total_weight = 0
        for order in orders:
            cargo_loads = session.exec(select(Cargo).where(Cargo.order_id == order.id)).all()
            total_volume += sum(cargo.total_volume() for cargo in cargo_loads)
            total_weight += sum(cargo.total_weight() for cargo in cargo_loads)
        
        result.append({
            "route_number": i,
            "id": route.id,
            "profitability": route.profitability,
            "distance_km": round(route.base_distance(), 1) if origin and destiny else None,
            "truck_capacity": truck.capacity if truck else None,
            "used_capacity": total_volume,
            "available_capacity": (truck.capacity - total_volume) if truck else None,
            "utilization_percent": round((total_volume / truck.capacity * 100), 1) if truck and truck.capacity > 0 else 0,
            "orders_count": len(orders),
            "destination": f"({destiny.lat:.4f}, {destiny.lng:.4f})" if destiny else None
        })
    
    return result

# Health endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)