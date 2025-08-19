from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ENUMS
class CargoType(str, Enum):
    STANDARD = "standard"
    FRAGILE = "fragile"
    HAZMAT = "hazmat"
    REFRIGERATED = "refrigerated"

class Location(BaseModel):
    id: Optional[int]
    lat: float
    lng: float
    marked: bool = False

    class Config:
        orm_mode = True

class Client(BaseModel):
    id: Optional[int]
    name: str
    created_at: datetime
    locations: List["Location"] = []
    orders: List["Order"] = []

    class Config:
        orm_mode = True

class Package(BaseModel):
    id: Optional[int]
    volume: float
    weight: float
    type: CargoType
    cargo_id: Optional[int]

    class Config:
        orm_mode = True

class Cargo(BaseModel):
    id: Optional[int]
    order_id: int
    truck_id: Optional[int]
    order: Optional["Order"]
    truck: Optional["Truck"]
    packages: List["Package"] = []

    class Config:
        orm_mode = True

class Order(BaseModel):
    id: Optional[int]
    location_origin_id: int
    location_destiny_id: int
    client_id: Optional[int]
    route_id: Optional[int]
    contract_type: Optional[str] = None
    client: Optional["Client"]
    route: Optional["Route"]
    cargo: List["Cargo"] = []
    location_origin: Optional["Location"]
    location_destiny: Optional["Location"]

    class Config:
        orm_mode = True

class Route(BaseModel):
    id: Optional[int]
    location_origin_id: int
    location_destiny_id: int
    profitability: float = 0.0
    truck_id: Optional[int]
    truck: Optional["Truck"]
    orders: List["Order"] = []
    location_origin: Optional["Location"]
    location_destiny: Optional["Location"]

    class Config:
        orm_mode = True

class Truck(BaseModel):
    id: Optional[int]
    autonomy: float
    capacity: float
    type: str
    routes: List["Route"] = []
    cargo_loads: List["Cargo"] = []

    class Config:
        orm_mode = True

# For forward references
# this is necessary to avoid circular imports
Client.update_forward_refs()
Order.update_forward_refs()
Cargo.update_forward_refs()
Package.update_forward_refs()
Route.update_forward_refs()
Truck.update_forward_refs()
Location.update_forward_refs()