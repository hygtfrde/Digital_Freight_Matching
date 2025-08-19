from fastapi import FastAPI, HTTPException
from typing import List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from schemas.schemas import (
    CargoType, Location, Package, Cargo, Order, Truck, Route
)

app = FastAPI(title="Digital Freight Matching CRUD API")

# ---- In-memory Stores ----
ORDERS: List[Order] = []
TRUCKS: List[Truck] = []
ROUTES: List[Route] = []

# ---- CRUD Endpoints ----

@app.get("/orders", response_model=List[Order])
def get_orders():
    return ORDERS

@app.post("/orders", response_model=Order)
def create_order(order: Order):
    ORDERS.append(order)
    return order

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    if 0 <= order_id < len(ORDERS):
        ORDERS.pop(order_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Order not found")

@app.get("/trucks", response_model=List[Truck])
def get_trucks():
    return TRUCKS

@app.post("/trucks", response_model=Truck)
def create_truck(truck: Truck):
    TRUCKS.append(truck)
    return truck

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int):
    if 0 <= truck_id < len(TRUCKS):
        TRUCKS.pop(truck_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Truck not found")

@app.get("/routes", response_model=List[Route])
def get_routes():
    return ROUTES

@app.post("/routes", response_model=Route)
def create_route(route: Route):
    ROUTES.append(route)
    return route

@app.delete("/routes/{route_id}")
def delete_route(route_id: int):
    if 0 <= route_id < len(ROUTES):
        ROUTES.pop(route_id)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Route not found")