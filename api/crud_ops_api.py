from fastapi import FastAPI, HTTPException, Depends
from typing import List
from sqlmodel import Session, select
from logistics_database2 import (
    engine, get_session,
    CargoType, Location, Package, Cargo, Order, Truck, Route
)
from schemas.schemas import (
    CargoType as SchemaCargoType,
    Location as SchemaLocation,
    Package as SchemaPackage,
    Cargo as SchemaCargo,
    Order as SchemaOrder,
    Truck as SchemaTruck,
    Route as SchemaRoute,
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