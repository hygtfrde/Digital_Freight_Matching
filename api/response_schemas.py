"""
Response schemas for API endpoints to avoid cyclic reference issues
These schemas only include essential fields without deep relationships
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CargoType(str, Enum):
    STANDARD = "standard"
    FRAGILE = "fragile"
    HAZMAT = "hazmat"
    REFRIGERATED = "refrigerated"


# Simple response schemas without cyclic relationships
class LocationResponse(BaseModel):
    id: Optional[int] = None
    lat: float
    lng: float
    marked: bool = False
    
    class Config:
        from_attributes = True


class ClientResponse(BaseModel):
    id: Optional[int] = None
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TruckResponse(BaseModel):
    id: Optional[int] = None
    autonomy: float
    capacity: float
    type: str
    
    class Config:
        from_attributes = True


class RouteResponse(BaseModel):
    id: Optional[int] = None
    location_origin_id: int
    location_destiny_id: int
    profitability: float = 0.0
    truck_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: Optional[int] = None
    location_origin_id: int
    location_destiny_id: int
    client_id: Optional[int] = None
    route_id: Optional[int] = None
    contract_type: Optional[str] = None
    
    class Config:
        from_attributes = True


class PackageResponse(BaseModel):
    id: Optional[int] = None
    volume: float
    weight: float
    type: CargoType
    cargo_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class CargoResponse(BaseModel):
    id: Optional[int] = None
    order_id: int
    truck_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Input schemas for creating/updating (can reuse original schemas)
from schemas.schemas import (
    Location as LocationInput,
    Client as ClientInput,
    Package as PackageInput,
    Cargo as CargoInput,
    Order as OrderInput,
    Truck as TruckInput,
    Route as RouteInput,
)