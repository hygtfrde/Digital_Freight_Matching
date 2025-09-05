from fastapi import FastAPI, HTTPException, Depends
from typing import List
from sqlmodel import Session, select
from app.database import (
    engine, create_tables, get_session,
    CargoType, Location, Package, Cargo, Order, Truck, Route, Client
)
from schemas.schemas import (
    CargoType as SchemaCargoType,
    Location as SchemaLocation,
    Package as SchemaPackage,
    Cargo as SchemaCargo,
    Order as SchemaOrder,
    Truck as SchemaTruck,
    Route as SchemaRoute,
    Client as SchemaClient,
)

app = FastAPI(title="Digital Freight Matching CRUD API")

# ---- CRUD Endpoints ----

# --------- ORDERS ---------
@app.get("/orders", response_model=List[SchemaOrder])
def get_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    return orders

@app.get("/orders/{order_id}", response_model=SchemaOrder)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/orders", response_model=SchemaOrder)
def create_order(order: SchemaOrder, session: Session = Depends(get_session)):
    db_order = Order.from_orm(order)
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order

@app.put("/orders/{order_id}", response_model=SchemaOrder)
def update_order(order_id: int, order: SchemaOrder, session: Session = Depends(get_session)):
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_data = order.dict(exclude_unset=True)
    for key, value in order_data.items():
        setattr(db_order, key, value)
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, session: Session = Depends(get_session)):
    db_order = session.get(Order, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    session.delete(db_order)
    session.commit()
    return {"status": "deleted"}

# --------- TRUCKS ---------
@app.get("/trucks", response_model=List[SchemaTruck])
def get_trucks(session: Session = Depends(get_session)):
    trucks = session.exec(select(Truck)).all()
    return trucks

@app.get("/trucks/{truck_id}", response_model=SchemaTruck)
def get_truck(truck_id: int, session: Session = Depends(get_session)):
    truck = session.get(Truck, truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@app.post("/trucks", response_model=SchemaTruck)
def create_truck(truck: SchemaTruck, session: Session = Depends(get_session)):
    db_truck = Truck.from_orm(truck)
    session.add(db_truck)
    session.commit()
    session.refresh(db_truck)
    return db_truck

@app.put("/trucks/{truck_id}", response_model=SchemaTruck)
def update_truck(truck_id: int, truck: SchemaTruck, session: Session = Depends(get_session)):
    db_truck = session.get(Truck, truck_id)
    if not db_truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    truck_data = truck.dict(exclude_unset=True)
    for key, value in truck_data.items():
        setattr(db_truck, key, value)
    session.add(db_truck)
    session.commit()
    session.refresh(db_truck)
    return db_truck

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int, session: Session = Depends(get_session)):
    db_truck = session.get(Truck, truck_id)
    if not db_truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    session.delete(db_truck)
    session.commit()
    return {"status": "deleted"}

# --------- ROUTES ---------
@app.get("/routes", response_model=List[SchemaRoute])
def get_routes(session: Session = Depends(get_session)):
    routes = session.exec(select(Route)).all()
    return routes

@app.get("/routes/{route_id}", response_model=SchemaRoute)
def get_route(route_id: int, session: Session = Depends(get_session)):
    route = session.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@app.post("/routes", response_model=SchemaRoute)
def create_route(route: SchemaRoute, session: Session = Depends(get_session)):
    db_route = Route.from_orm(route)
    session.add(db_route)
    session.commit()
    session.refresh(db_route)
    return db_route

@app.put("/routes/{route_id}", response_model=SchemaRoute)
def update_route(route_id: int, route: SchemaRoute, session: Session = Depends(get_session)):
    db_route = session.get(Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    route_data = route.dict(exclude_unset=True)
    for key, value in route_data.items():
        setattr(db_route, key, value)
    session.add(db_route)
    session.commit()
    session.refresh(db_route)
    return db_route

@app.delete("/routes/{route_id}")
def delete_route(route_id: int, session: Session = Depends(get_session)):
    db_route = session.get(Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    session.delete(db_route)
    session.commit()
    return {"status": "deleted"}

# --------- LOCATIONS ---------
@app.get("/locations", response_model=List[SchemaLocation])
def get_locations(session: Session = Depends(get_session)):
    locations = session.exec(select(Location)).all()
    return locations

@app.get("/locations/{location_id}", response_model=SchemaLocation)
def get_location(location_id: int, session: Session = Depends(get_session)):
    location = session.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@app.post("/locations", response_model=SchemaLocation)
def create_location(location: SchemaLocation, session: Session = Depends(get_session)):
    db_location = Location.from_orm(location)
    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return db_location

@app.put("/locations/{location_id}", response_model=SchemaLocation)
def update_location(location_id: int, location: SchemaLocation, session: Session = Depends(get_session)):
    db_location = session.get(Location, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    location_data = location.dict(exclude_unset=True)
    for key, value in location_data.items():
        setattr(db_location, key, value)
    session.add(db_location)
    session.commit()
    session.refresh(db_location)
    return db_location

@app.delete("/locations/{location_id}")
def delete_location(location_id: int, session: Session = Depends(get_session)):
    db_location = session.get(Location, location_id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    session.delete(db_location)
    session.commit()
    return {"status": "deleted"}

# --------- CLIENTS ---------
@app.get("/clients", response_model=List[SchemaClient])
def get_clients(session: Session = Depends(get_session)):
    clients = session.exec(select(Client)).all()
    return clients

@app.get("/clients/{client_id}", response_model=SchemaClient)
def get_client(client_id: int, session: Session = Depends(get_session)):
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.post("/clients", response_model=SchemaClient)
def create_client(client: SchemaClient, session: Session = Depends(get_session)):
    db_client = Client.from_orm(client)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

@app.put("/clients/{client_id}", response_model=SchemaClient)
def update_client(client_id: int, client: SchemaClient, session: Session = Depends(get_session)):
    db_client = session.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    client_data = client.dict(exclude_unset=True)
    for key, value in client_data.items():
        setattr(db_client, key, value)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    db_client = session.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    session.delete(db_client)
    session.commit()
    return {"status": "deleted"}

# --------- PACKAGES ---------
@app.get("/packages", response_model=List[SchemaPackage])
def get_packages(session: Session = Depends(get_session)):
    packages = session.exec(select(Package)).all()
    return packages

@app.get("/packages/{package_id}", response_model=SchemaPackage)
def get_package(package_id: int, session: Session = Depends(get_session)):
    package = session.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package

@app.post("/packages", response_model=SchemaPackage)
def create_package(package: SchemaPackage, session: Session = Depends(get_session)):
    db_package = Package.from_orm(package)
    session.add(db_package)
    session.commit()
    session.refresh(db_package)
    return db_package

@app.put("/packages/{package_id}", response_model=SchemaPackage)
def update_package(package_id: int, package: SchemaPackage, session: Session = Depends(get_session)):
    db_package = session.get(Package, package_id)
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")
    package_data = package.dict(exclude_unset=True)
    for key, value in package_data.items():
        setattr(db_package, key, value)
    session.add(db_package)
    session.commit()
    session.refresh(db_package)
    return db_package

@app.delete("/packages/{package_id}")
def delete_package(package_id: int, session: Session = Depends(get_session)):
    db_package = session.get(Package, package_id)
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")
    session.delete(db_package)
    session.commit()
    return {"status": "deleted"}

# --------- CARGO ---------
@app.get("/cargo", response_model=List[SchemaCargo])
def get_cargo_loads(session: Session = Depends(get_session)):
    cargo_loads = session.exec(select(Cargo)).all()
    return cargo_loads

@app.get("/cargo/{cargo_id}", response_model=SchemaCargo)
def get_cargo(cargo_id: int, session: Session = Depends(get_session)):
    cargo = session.get(Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    return cargo

@app.post("/cargo", response_model=SchemaCargo)
def create_cargo(cargo: SchemaCargo, session: Session = Depends(get_session)):
    db_cargo = Cargo.from_orm(cargo)
    session.add(db_cargo)
    session.commit()
    session.refresh(db_cargo)
    return db_cargo

@app.put("/cargo/{cargo_id}", response_model=SchemaCargo)
def update_cargo(cargo_id: int, cargo: SchemaCargo, session: Session = Depends(get_session)):
    db_cargo = session.get(Cargo, cargo_id)
    if not db_cargo:
        raise HTTPException(status_code=404, detail="Cargo not found")
    cargo_data = cargo.dict(exclude_unset=True)
    for key, value in cargo_data.items():
        setattr(db_cargo, key, value)
    session.add(db_cargo)
    session.commit()
    session.refresh(db_cargo)
    return db_cargo

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