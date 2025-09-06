from fastapi import FastAPI, HTTPException, Depends
from typing import List
from sqlmodel import Session, select
from app.database import (
    engine, create_tables, get_session,
    CargoType, Location, Package, Cargo, Order, Truck, Route, Client
)

# Use simplified response schemas to avoid cyclic references
from api.response_schemas import (
    LocationResponse, ClientResponse, TruckResponse, RouteResponse,
    OrderResponse, PackageResponse, CargoResponse,
    LocationInput, ClientInput, TruckInput, RouteInput,
    OrderInput, PackageInput, CargoInput
)

app = FastAPI(title="Digital Freight Matching CRUD API")

# ---- CRUD Endpoints ----

# --------- ORDERS ---------
@app.get("/orders", response_model=List[OrderResponse])
def get_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    return [OrderResponse(
        id=order.id,
        location_origin_id=order.location_origin_id,
        location_destiny_id=order.location_destiny_id,
        client_id=order.client_id,
        route_id=order.route_id,
        contract_type=order.contract_type
    ) for order in orders]

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        id=order.id,
        location_origin_id=order.location_origin_id,
        location_destiny_id=order.location_destiny_id,
        client_id=order.client_id,
        route_id=order.route_id,
        contract_type=order.contract_type
    )

@app.post("/orders", response_model=OrderResponse)
def create_order(order_data: OrderInput, session: Session = Depends(get_session)):
    # Create new order using only basic fields
    db_order = Order(
        location_origin_id=order_data.location_origin_id,
        location_destiny_id=order_data.location_destiny_id,
        client_id=order_data.client_id,
        contract_type=order_data.contract_type
    )
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return OrderResponse(
        id=db_order.id,
        location_origin_id=db_order.location_origin_id,
        location_destiny_id=db_order.location_destiny_id,
        client_id=db_order.client_id,
        route_id=db_order.route_id,
        contract_type=db_order.contract_type
    )

@app.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order_data: OrderInput, session: Session = Depends(get_session)):
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update only basic fields to avoid relationship issues
    if order_data.location_origin_id:
        db_order.location_origin_id = order_data.location_origin_id
    if order_data.location_destiny_id:
        db_order.location_destiny_id = order_data.location_destiny_id
    if order_data.client_id is not None:
        db_order.client_id = order_data.client_id
    if order_data.contract_type is not None:
        db_order.contract_type = order_data.contract_type

    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return OrderResponse(
        id=db_order.id,
        location_origin_id=db_order.location_origin_id,
        location_destiny_id=db_order.location_destiny_id,
        client_id=db_order.client_id,
        route_id=db_order.route_id,
        contract_type=db_order.contract_type
    )

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, session: Session = Depends(get_session)):
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    session.delete(db_order)
    session.commit()
    return {"status": "deleted"}

# --------- TRUCKS ---------
@app.get("/trucks", response_model=List[TruckResponse])
def get_trucks(session: Session = Depends(get_session)):
    trucks = session.exec(select(Truck)).all()
    return [TruckResponse(
        id=truck.id,
        autonomy=truck.autonomy,
        capacity=truck.capacity,
        type=truck.type
    ) for truck in trucks]

@app.get("/trucks/{truck_id}", response_model=TruckResponse)
def get_truck(truck_id: int, session: Session = Depends(get_session)):
    truck = session.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return TruckResponse(
        id=truck.id,
        autonomy=truck.autonomy,
        capacity=truck.capacity,
        type=truck.type
    )

@app.post("/trucks", response_model=TruckResponse)
def create_truck(truck_data: TruckInput, session: Session = Depends(get_session)):
    db_truck = Truck(
        type=truck_data.type,
        capacity=truck_data.capacity,
        autonomy=truck_data.autonomy
    )
    session.add(db_truck)
    session.commit()
    session.refresh(db_truck)
    return TruckResponse(
        id=db_truck.id,
        autonomy=db_truck.autonomy,
        capacity=db_truck.capacity,
        type=db_truck.type
    )

@app.put("/trucks/{truck_id}", response_model=TruckResponse)
def update_truck(truck_id: int, truck_data: TruckInput, session: Session = Depends(get_session)):
    db_truck = session.get(Truck, truck_id)
    if not db_truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    if truck_data.type:
        db_truck.type = truck_data.type
    if truck_data.capacity:
        db_truck.capacity = truck_data.capacity
    if truck_data.autonomy:
        db_truck.autonomy = truck_data.autonomy

    session.add(db_truck)
    session.commit()
    session.refresh(db_truck)
    return TruckResponse(
        id=db_truck.id,
        autonomy=db_truck.autonomy,
        capacity=db_truck.capacity,
        type=db_truck.type
    )

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int, session: Session = Depends(get_session)):
    db_truck = session.get(Truck, truck_id)
    if not db_truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    session.delete(db_truck)
    session.commit()
    return {"status": "deleted"}

# --------- ROUTES ---------
@app.get("/routes", response_model=List[RouteResponse])
def get_routes(session: Session = Depends(get_session)):
    routes = session.exec(select(Route)).all()
    return [RouteResponse(
        id=route.id,
        location_origin_id=route.location_origin_id,
        location_destiny_id=route.location_destiny_id,
        profitability=route.profitability,
        truck_id=route.truck_id
    ) for route in routes]

@app.get("/routes/{route_id}", response_model=RouteResponse)
def get_route(route_id: int, session: Session = Depends(get_session)):
    route = session.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return RouteResponse(
        id=route.id,
        location_origin_id=route.location_origin_id,
        location_destiny_id=route.location_destiny_id,
        profitability=route.profitability,
        truck_id=route.truck_id
    )

@app.post("/routes", response_model=RouteResponse)
def create_route(route_data: RouteInput, session: Session = Depends(get_session)):
    db_route = Route(
        location_origin_id=route_data.location_origin_id,
        location_destiny_id=route_data.location_destiny_id,
        profitability=route_data.profitability or 0.0,
        truck_id=route_data.truck_id
    )
    session.add(db_route)
    session.commit()
    session.refresh(db_route)
    return RouteResponse(
        id=db_route.id,
        location_origin_id=db_route.location_origin_id,
        location_destiny_id=db_route.location_destiny_id,
        profitability=db_route.profitability,
        truck_id=db_route.truck_id
    )

@app.put("/routes/{route_id}", response_model=RouteResponse)
def update_route(route_id: int, route_data: RouteInput, session: Session = Depends(get_session)):
    db_route = session.get(Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")

    if route_data.location_origin_id:
        db_route.location_origin_id = route_data.location_origin_id
    if route_data.location_destiny_id:
        db_route.location_destiny_id = route_data.location_destiny_id
    if route_data.profitability is not None:
        db_route.profitability = route_data.profitability
    if route_data.truck_id is not None:
        db_route.truck_id = route_data.truck_id

    session.add(db_route)
    session.commit()
    session.refresh(db_route)
    return RouteResponse(
        id=db_route.id,
        location_origin_id=db_route.location_origin_id,
        location_destiny_id=db_route.location_destiny_id,
        profitability=db_route.profitability,
        truck_id=db_route.truck_id
    )

@app.delete("/routes/{route_id}")
def delete_route(route_id: int, session: Session = Depends(get_session)):
    db_route = session.get(Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    session.delete(db_route)
    session.commit()
    return {"status": "deleted"}

# --------- LOCATIONS ---------
@app.get("/locations", response_model=List[LocationResponse])
def get_locations(session: Session = Depends(get_session)):
    locations = session.exec(select(Location)).all()
    return [LocationResponse(
        id=location.id,
        lat=location.lat,
        lng=location.lng,
        marked=location.marked
    ) for location in locations]

@app.get("/locations/{location_id}", response_model=LocationResponse)
def get_location(location_id: int, session: Session = Depends(get_session)):
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationResponse(
        id=location.id,
        lat=location.lat,
        lng=location.lng,
        marked=location.marked
    )

@app.post("/locations", response_model=LocationResponse)
def create_location(location_data: LocationInput, session: Session = Depends(get_session)):
    db_location = Location(
        lat=location_data.lat,
        lng=location_data.lng,
        marked=location_data.marked or False
    )
    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return LocationResponse(
        id=db_location.id,
        lat=db_location.lat,
        lng=db_location.lng,
        marked=db_location.marked
    )

@app.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, location_data: LocationInput, session: Session = Depends(get_session)):
    db_location = session.get(Location, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

    if location_data.lat is not None:
        db_location.lat = location_data.lat
    if location_data.lng is not None:
        db_location.lng = location_data.lng
    if location_data.marked is not None:
        db_location.marked = location_data.marked

    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return LocationResponse(
        id=db_location.id,
        lat=db_location.lat,
        lng=db_location.lng,
        marked=db_location.marked
    )

@app.delete("/locations/{location_id}")
def delete_location(location_id: int, session: Session = Depends(get_session)):
    db_location = session.get(Location, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    session.delete(db_location)
    session.commit()
    return {"status": "deleted"}

# --------- CLIENTS ---------
@app.get("/clients", response_model=List[ClientResponse])
def get_clients(session: Session = Depends(get_session)):
    clients = session.exec(select(Client)).all()
    return [ClientResponse(
        id=client.id,
        name=client.name,
        created_at=client.created_at
    ) for client in clients]

@app.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientResponse(
        id=client.id,
        name=client.name,
        created_at=client.created_at
    )

@app.post("/clients", response_model=ClientResponse)
def create_client(client_data: ClientInput, session: Session = Depends(get_session)):
    db_client = Client(
        name=client_data.name,
        created_at=client_data.created_at
    )
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return ClientResponse(
        id=db_client.id,
        name=db_client.name,
        created_at=db_client.created_at
    )

@app.put("/clients/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, client_data: ClientInput, session: Session = Depends(get_session)):
    db_client = session.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client_data.name:
        db_client.name = client_data.name
    if client_data.created_at:
        db_client.created_at = client_data.created_at

    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return ClientResponse(
        id=db_client.id,
        name=db_client.name,
        created_at=db_client.created_at
    )

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    db_client = session.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    session.delete(db_client)
    session.commit()
    return {"status": "deleted"}

# --------- PACKAGES ---------
@app.get("/packages", response_model=List[PackageResponse])
def get_packages(session: Session = Depends(get_session)):
    packages = session.exec(select(Package)).all()
    return [PackageResponse(
        id=package.id,
        volume=package.volume,
        weight=package.weight,
        type=package.type,
        cargo_id=package.cargo_id
    ) for package in packages]

@app.get("/packages/{package_id}", response_model=PackageResponse)
def get_package(package_id: int, session: Session = Depends(get_session)):
    package = session.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return PackageResponse(
        id=package.id,
        volume=package.volume,
        weight=package.weight,
        type=package.type,
        cargo_id=package.cargo_id
    )

@app.post("/packages", response_model=PackageResponse)
def create_package(package_data: PackageInput, session: Session = Depends(get_session)):
    db_package = Package(
        volume=package_data.volume,
        weight=package_data.weight,
        type=package_data.type,
        cargo_id=package_data.cargo_id
    )
    session.add(db_package)
    session.commit()
    session.refresh(db_package)
    return PackageResponse(
        id=db_package.id,
        volume=db_package.volume,
        weight=db_package.weight,
        type=db_package.type,
        cargo_id=db_package.cargo_id
    )

@app.put("/packages/{package_id}", response_model=PackageResponse)
def update_package(package_id: int, package_data: PackageInput, session: Session = Depends(get_session)):
    db_package = session.get(Package, package_id)
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")

    if package_data.volume is not None:
        db_package.volume = package_data.volume
    if package_data.weight is not None:
        db_package.weight = package_data.weight
    if package_data.type is not None:
        db_package.type = package_data.type
    if package_data.cargo_id is not None:
        db_package.cargo_id = package_data.cargo_id

    session.add(db_package)
    session.commit()
    session.refresh(db_package)
    return PackageResponse(
        id=db_package.id,
        volume=db_package.volume,
        weight=db_package.weight,
        type=db_package.type,
        cargo_id=db_package.cargo_id
    )

@app.delete("/packages/{package_id}")
def delete_package(package_id: int, session: Session = Depends(get_session)):
    db_package = session.get(Package, package_id)
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")
    session.delete(db_package)
    session.commit()
    return {"status": "deleted"}

# --------- CARGO ---------
@app.get("/cargo", response_model=List[CargoResponse])
def get_cargo_loads(session: Session = Depends(get_session)):
    cargo_loads = session.exec(select(Cargo)).all()
    return [CargoResponse(
        id=cargo.id,
        order_id=cargo.order_id,
        truck_id=cargo.truck_id
    ) for cargo in cargo_loads]

@app.get("/cargo/{cargo_id}", response_model=CargoResponse)
def get_cargo(cargo_id: int, session: Session = Depends(get_session)):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    return CargoResponse(
        id=cargo.id,
        order_id=cargo.order_id,
        truck_id=cargo.truck_id
    )

@app.post("/cargo", response_model=CargoResponse)
def create_cargo(cargo_data: CargoInput, session: Session = Depends(get_session)):
    db_cargo = Cargo(
        order_id=cargo_data.order_id,
        truck_id=cargo_data.truck_id
    )
    session.add(db_cargo)
    session.commit()
    session.refresh(db_cargo)
    return CargoResponse(
        id=db_cargo.id,
        order_id=db_cargo.order_id,
        truck_id=db_cargo.truck_id
    )

@app.put("/cargo/{cargo_id}", response_model=CargoResponse)
def update_cargo(cargo_id: int, cargo_data: CargoInput, session: Session = Depends(get_session)):
    db_cargo = session.get(Cargo, cargo_id)
    if not db_cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")

    if cargo_data.order_id:
        db_cargo.order_id = cargo_data.order_id
    if cargo_data.truck_id is not None:
        db_cargo.truck_id = cargo_data.truck_id

    session.add(db_cargo)
    session.commit()
    session.refresh(db_cargo)
    return CargoResponse(
        id=db_cargo.id,
        order_id=db_cargo.order_id,
        truck_id=db_cargo.truck_id
    )

@app.delete("/cargo/{cargo_id}")
def delete_cargo(cargo_id: int, session: Session = Depends(get_session)):
    db_cargo = session.get(Cargo, cargo_id)
    if not db_cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    session.delete(db_cargo)
    session.commit()
    return {"status": "deleted"}


# --------- HEALTH CHECK ---------
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Digital Freight Matching CRUD API is running"}

# --------- SUMMARY ENDPOINT ---------
@app.get("/summary")
def get_summary(session: Session = Depends(get_session)):
    """Get summary counts of all entities"""
    return {
        "clients": len(session.exec(select(Client)).all()),
        "locations": len(session.exec(select(Location)).all()),
        "trucks": len(session.exec(select(Truck)).all()),
        "routes": len(session.exec(select(Route)).all()),
        "orders": len(session.exec(select(Order)).all()),
        "cargo_loads": len(session.exec(select(Cargo)).all()),
        "packages": len(session.exec(select(Package)).all()),
    }
