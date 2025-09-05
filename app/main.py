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

@app.post("/trucks")
def create_truck(truck_data: dict, session: Session = Depends(get_session)):
    """Create a new truck"""
    try:
        new_truck = Truck(
            type=truck_data.get("type"),
            capacity=truck_data.get("capacity"),
            autonomy=truck_data.get("autonomy")
        )
        session.add(new_truck)
        session.commit()
        session.refresh(new_truck)
        
        return {"id": new_truck.id, "status": "created", "message": "Truck created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create truck: {str(e)}")

@app.put("/trucks/{truck_id}")
def update_truck(truck_id: int, truck_data: dict, session: Session = Depends(get_session)):
    """Update a truck"""
    truck = session.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    try:
        if "type" in truck_data:
            truck.type = truck_data["type"]
        if "capacity" in truck_data:
            truck.capacity = truck_data["capacity"]
        if "autonomy" in truck_data:
            truck.autonomy = truck_data["autonomy"]
        
        session.add(truck)
        session.commit()
        session.refresh(truck)
        
        return {"id": truck.id, "status": "updated", "message": "Truck updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update truck: {str(e)}")

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int, session: Session = Depends(get_session)):
    """Delete a truck"""
    truck = session.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    try:
        session.delete(truck)
        session.commit()
        return {"status": "deleted", "message": "Truck deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete truck: {str(e)}")

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

@app.post("/routes")
def create_route(route_data: dict, session: Session = Depends(get_session)):
    """Create a new route"""
    try:
        new_route = Route(
            location_origin_id=route_data.get("location_origin_id"),
            location_destiny_id=route_data.get("location_destiny_id"),
            profitability=route_data.get("profitability", 0.0),
            truck_id=route_data.get("truck_id")
        )
        session.add(new_route)
        session.commit()
        session.refresh(new_route)
        
        return {"id": new_route.id, "status": "created", "message": "Route created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create route: {str(e)}")

@app.put("/routes/{route_id}")
def update_route(route_id: int, route_data: dict, session: Session = Depends(get_session)):
    """Update a route"""
    route = session.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    try:
        if "location_origin_id" in route_data:
            route.location_origin_id = route_data["location_origin_id"]
        if "location_destiny_id" in route_data:
            route.location_destiny_id = route_data["location_destiny_id"]
        if "profitability" in route_data:
            route.profitability = route_data["profitability"]
        if "truck_id" in route_data:
            route.truck_id = route_data["truck_id"]
        
        session.add(route)
        session.commit()
        session.refresh(route)
        
        return {"id": route.id, "status": "updated", "message": "Route updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update route: {str(e)}")

@app.delete("/routes/{route_id}")
def delete_route(route_id: int, session: Session = Depends(get_session)):
    """Delete a route"""
    route = session.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    try:
        session.delete(route)
        session.commit()
        return {"status": "deleted", "message": "Route deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete route: {str(e)}")

# Client CRUD endpoints
@app.post("/clients")
def create_client(client_data: dict, session: Session = Depends(get_session)):
    """Create a new client"""
    try:
        new_client = Client(name=client_data.get("name"))
        session.add(new_client)
        session.commit()
        session.refresh(new_client)
        
        return {"id": new_client.id, "status": "created", "message": "Client created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create client: {str(e)}")

@app.put("/clients/{client_id}")
def update_client(client_id: int, client_data: dict, session: Session = Depends(get_session)):
    """Update a client"""
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        if "name" in client_data:
            client.name = client_data["name"]
        
        session.add(client)
        session.commit()
        session.refresh(client)
        
        return {"id": client.id, "status": "updated", "message": "Client updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update client: {str(e)}")

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    """Delete a client"""
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        session.delete(client)
        session.commit()
        return {"status": "deleted", "message": "Client deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete client: {str(e)}")

# Location CRUD endpoints
@app.post("/locations")
def create_location(location_data: dict, session: Session = Depends(get_session)):
    """Create a new location"""
    try:
        new_location = Location(
            lat=location_data.get("lat"),
            lng=location_data.get("lng"),
            marked=location_data.get("marked", False)
        )
        session.add(new_location)
        session.commit()
        session.refresh(new_location)
        
        return {"id": new_location.id, "status": "created", "message": "Location created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create location: {str(e)}")

@app.put("/locations/{location_id}")
def update_location(location_id: int, location_data: dict, session: Session = Depends(get_session)):
    """Update a location"""
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    try:
        if "lat" in location_data:
            location.lat = location_data["lat"]
        if "lng" in location_data:
            location.lng = location_data["lng"]
        if "marked" in location_data:
            location.marked = location_data["marked"]
        
        session.add(location)
        session.commit()
        session.refresh(location)
        
        return {"id": location.id, "status": "updated", "message": "Location updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update location: {str(e)}")

@app.delete("/locations/{location_id}")
def delete_location(location_id: int, session: Session = Depends(get_session)):
    """Delete a location"""
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    try:
        session.delete(location)
        session.commit()
        return {"status": "deleted", "message": "Location deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete location: {str(e)}")

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

# Order CRUD endpoints  
@app.post("/orders")
def create_order(order_data: dict, session: Session = Depends(get_session)):
    """Create a new order"""
    try:
        new_order = Order(
            location_origin_id=order_data.get("location_origin_id"),
            location_destiny_id=order_data.get("location_destiny_id"),
            client_id=order_data.get("client_id"),
            route_id=order_data.get("route_id"),
            contract_type=order_data.get("contract_type")
        )
        session.add(new_order)
        session.commit()
        session.refresh(new_order)
        
        return {"id": new_order.id, "status": "created", "message": "Order created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")

@app.put("/orders/{order_id}")
def update_order(order_id: int, order_data: dict, session: Session = Depends(get_session)):
    """Update an order"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        if "location_origin_id" in order_data:
            order.location_origin_id = order_data["location_origin_id"]
        if "location_destiny_id" in order_data:
            order.location_destiny_id = order_data["location_destiny_id"]
        if "client_id" in order_data:
            order.client_id = order_data["client_id"]
        if "route_id" in order_data:
            order.route_id = order_data["route_id"]
        if "contract_type" in order_data:
            order.contract_type = order_data["contract_type"]
        
        session.add(order)
        session.commit()
        session.refresh(order)
        
        return {"id": order.id, "status": "updated", "message": "Order updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update order: {str(e)}")

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, session: Session = Depends(get_session)):
    """Delete an order"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        session.delete(order)
        session.commit()
        return {"status": "deleted", "message": "Order deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete order: {str(e)}")

# Package endpoints
@app.get("/packages")
def get_packages(cargo_id: Optional[int] = None, session: Session = Depends(get_session)):
    """Get packages, optionally filtered by cargo"""
    query = select(Package)
    
    if cargo_id:
        query = query.where(Package.cargo_id == cargo_id)
    
    packages = session.exec(query).all()
    result = []
    
    for package in packages:
        result.append({
            "id": package.id,
            "volume": package.volume,
            "weight": package.weight,
            "type": package.type.value if package.type else None,
            "cargo_id": package.cargo_id
        })
    
    return result

@app.get("/packages/{package_id}")
def get_package_details(package_id: int, session: Session = Depends(get_session)):
    """Get detailed package information"""
    package = session.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    return {
        "id": package.id,
        "volume": package.volume,
        "weight": package.weight,
        "type": package.type.value if package.type else None,
        "cargo_id": package.cargo_id
    }

@app.post("/packages")
def create_package(package_data: dict, session: Session = Depends(get_session)):
    """Create a new package"""
    try:
        # Handle cargo_type conversion if needed
        cargo_type = package_data.get("type")
        if isinstance(cargo_type, str):
            try:
                cargo_type = CargoType(cargo_type)
            except ValueError:
                cargo_type = CargoType.GENERAL
        
        new_package = Package(
            volume=package_data.get("volume"),
            weight=package_data.get("weight"),
            type=cargo_type,
            cargo_id=package_data.get("cargo_id")
        )
        session.add(new_package)
        session.commit()
        session.refresh(new_package)
        
        return {"id": new_package.id, "status": "created", "message": "Package created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create package: {str(e)}")

@app.put("/packages/{package_id}")
def update_package(package_id: int, package_data: dict, session: Session = Depends(get_session)):
    """Update a package"""
    package = session.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    try:
        if "volume" in package_data:
            package.volume = package_data["volume"]
        if "weight" in package_data:
            package.weight = package_data["weight"]
        if "type" in package_data:
            cargo_type = package_data["type"]
            if isinstance(cargo_type, str):
                try:
                    cargo_type = CargoType(cargo_type)
                except ValueError:
                    cargo_type = CargoType.GENERAL
            package.type = cargo_type
        if "cargo_id" in package_data:
            package.cargo_id = package_data["cargo_id"]
        
        session.add(package)
        session.commit()
        session.refresh(package)
        
        return {"id": package.id, "status": "updated", "message": "Package updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update package: {str(e)}")

@app.delete("/packages/{package_id}")
def delete_package(package_id: int, session: Session = Depends(get_session)):
    """Delete a package"""
    package = session.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    try:
        session.delete(package)
        session.commit()
        return {"status": "deleted", "message": "Package deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete package: {str(e)}")

# Cargo endpoints
@app.get("/cargo")
def get_cargo(order_id: Optional[int] = None, truck_id: Optional[int] = None, session: Session = Depends(get_session)):
    """Get cargo, optionally filtered by order or truck"""
    query = select(Cargo)
    
    if order_id:
        query = query.where(Cargo.order_id == order_id)
    if truck_id:
        query = query.where(Cargo.truck_id == truck_id)
    
    cargo_loads = session.exec(query).all()
    result = []
    
    for cargo in cargo_loads:
        # Get associated packages
        packages = session.exec(select(Package).where(Package.cargo_id == cargo.id)).all()
        
        result.append({
            "id": cargo.id,
            "order_id": cargo.order_id,
            "truck_id": cargo.truck_id,
            "total_volume": cargo.total_volume(),
            "total_weight": cargo.total_weight(),
            "packages_count": len(packages)
        })
    
    return result

@app.get("/cargo/{cargo_id}")
def get_cargo_details(cargo_id: int, session: Session = Depends(get_session)):
    """Get detailed cargo information"""
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    # Get associated packages
    packages = session.exec(select(Package).where(Package.cargo_id == cargo_id)).all()
    
    return {
        "id": cargo.id,
        "order_id": cargo.order_id,
        "truck_id": cargo.truck_id,
        "total_volume": cargo.total_volume(),
        "total_weight": cargo.total_weight(),
        "packages": [{"id": p.id, "volume": p.volume, "weight": p.weight, "type": p.type.value if p.type else None} for p in packages]
    }

@app.post("/cargo")
def create_cargo(cargo_data: dict, session: Session = Depends(get_session)):
    """Create a new cargo"""
    try:
        new_cargo = Cargo(
            order_id=cargo_data.get("order_id"),
            truck_id=cargo_data.get("truck_id")
        )
        session.add(new_cargo)
        session.commit()
        session.refresh(new_cargo)
        
        return {"id": new_cargo.id, "status": "created", "message": "Cargo created successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create cargo: {str(e)}")

@app.put("/cargo/{cargo_id}")
def update_cargo(cargo_id: int, cargo_data: dict, session: Session = Depends(get_session)):
    """Update a cargo"""
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    try:
        if "order_id" in cargo_data:
            cargo.order_id = cargo_data["order_id"]
        if "truck_id" in cargo_data:
            cargo.truck_id = cargo_data["truck_id"]
        
        session.add(cargo)
        session.commit()
        session.refresh(cargo)
        
        return {"id": cargo.id, "status": "updated", "message": "Cargo updated successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update cargo: {str(e)}")

@app.delete("/cargo/{cargo_id}")
def delete_cargo(cargo_id: int, session: Session = Depends(get_session)):
    """Delete a cargo"""
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    
    try:
        session.delete(cargo)
        session.commit()
        return {"status": "deleted", "message": "Cargo deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete cargo: {str(e)}")

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