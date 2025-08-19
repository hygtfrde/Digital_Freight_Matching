"""
+-------------------------------------------------------+
|                 🚛 Freight Control Panel              |
+-------------------+------------------+----------------+
|   Trucks          |   Routes         |   Orders       |
|-------------------|------------------|----------------|
| [ List Trucks ]   | [ List Routes ]  | [ List Orders ]|
| [ Add Truck ]     | [ Add Route ]    | [ Add Order ]  |
| [ Edit Truck ]    | [ Edit Route ]   | [ Edit Order ] |
| [ Delete Truck ]  | [ Delete Route ] | [ Delete Order]|
| [ View Loads ]    | [ Assign Truck ] | [ Match Order ]|
+-------------------+------------------+----------------+
|   Clients         |   Locations      |   Packages     |
|-------------------|------------------|----------------|
| [ List Clients ]  | [ List Loc.  ]   | [ List Pkg.  ] |
| [ Add Client ]    | [ Add Loc.   ]   | [ Add Pkg.   ] |
| [ Edit Client ]   | [ Edit Loc.  ]   | [ Edit Pkg.  ] |
| [ Delete Client ] | [ Delete Loc. ]  | [ Delete Pkg.] |
| [ View Orders ]   | [ View Routes]   | [ Assign to  ] |
|                   |                  |   Cargo        |
+-------------------+------------------+----------------+
|   Cargo           |   Pricing/Match  |   Dashboard    |
|-------------------|------------------|----------------|
| [ List Cargo  ]   | [ Price Route ]  |  [Summary]     |
| [ Add Cargo   ]   | [ Match Order ]  |  [KPIs]        |
| [ Edit Cargo  ]   | [ Profitability] |  [Pending]     |
| [ Delete Cargo]   | [ New Route   ]  |  [Utilization] |
| [ Assign Pkg. ]   |                  |  [Alerts]      |
+-------------------------------------------------------+
"""


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dfm import (
    CargoType, Location, Package, Cargo, Order, Truck, Route, PricingService
)

app = FastAPI(title="Digital Freight Matching CRUD API")

# ---- Pydantic Schemas ----

class PackageSchema(BaseModel):
    volume: float
    weight: float
    type: CargoType

class LocationSchema(BaseModel):
    latitude: float
    longitude: float

class CargoSchema(BaseModel):
    packages: List[PackageSchema]

class OrderSchema(BaseModel):
    cargo: CargoSchema
    pickup: LocationSchema
    dropoff: LocationSchema

class TruckSchema(BaseModel):
    autonomy: float
    capacity: float
    type: str

class RouteSchema(BaseModel):
    origin: LocationSchema
    destiny: LocationSchema
    path: List[LocationSchema]

# ---- In-memory Stores ----
ORDERS: List[Order] = []
TRUCKS: List[Truck] = []
ROUTES: List[Route] = []

# ---- CRUD Endpoints ----

@app.get("/orders", response_model=List[OrderSchema])
def get_orders():
    # Convert Orders to schemas
    return [
        OrderSchema(
            cargo=CargoSchema(
                packages=[
                    PackageSchema(volume=p.volume, weight=p.weight, type=p.type)
                    for p in o.cargo.packages
                ]
            ),
            pickup=LocationSchema(latitude=o.pickup.latitude, longitude=o.pickup.longitude),
            dropoff=LocationSchema(latitude=o.dropoff.latitude, longitude=o.dropoff.longitude)
        )
        for o in ORDERS
    ]

@app.post("/orders", response_model=OrderSchema)
def create_order(order: OrderSchema):
    py_order = Order(
        cargo=Cargo([Package(p.volume, p.weight, p.type) for p in order.cargo.packages]),
        pickup=Location(order.pickup.latitude, order.pickup.longitude),
        dropoff=Location(order.dropoff.latitude, order.dropoff.longitude)
    )
    ORDERS.append(py_order)
    return order

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    if 0 <= order_id < len(ORDERS):
        ORDERS.pop(order_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Order not found")

# --- Similar endpoints for Truck and Route ---

@app.get("/trucks", response_model=List[TruckSchema])
def get_trucks():
    return [
        TruckSchema(autonomy=t.autonomy, capacity=t.capacity, type=t.type)
        for t in TRUCKS
    ]

@app.post("/trucks", response_model=TruckSchema)
def create_truck(truck: TruckSchema):
    py_truck = Truck(truck.autonomy, truck.capacity, truck.type)
    TRUCKS.append(py_truck)
    return truck

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int):
    if 0 <= truck_id < len(TRUCKS):
        TRUCKS.pop(truck_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Truck not found")

@app.get("/routes", response_model=List[RouteSchema])
def get_routes():
    return [
        RouteSchema(
            origin=LocationSchema(latitude=r.origin.latitude, longitude=r.origin.longitude),
            destiny=LocationSchema(latitude=r.destiny.latitude, longitude=r.destiny.longitude),
            path=[LocationSchema(latitude=l.latitude, longitude=l.longitude) for l in r.path]
        )
        for r in ROUTES
    ]

@app.post("/routes", response_model=RouteSchema)
def create_route(route: RouteSchema):
    py_route = Route(
        origin=Location(route.origin.latitude, route.origin.longitude),
        destiny=Location(route.destiny.latitude, route.destiny.longitude),
        path=[Location(l.latitude, l.longitude) for l in route.path]
    )
    ROUTES.append(py_route)
    return route

@app.delete("/routes/{route_id}")
def delete_route(route_id: int):
    if 0 <= route_id < len(ROUTES):
        ROUTES.pop(route_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Route not found")