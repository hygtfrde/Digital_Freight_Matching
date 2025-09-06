# database.py
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from typing import List, Optional, Set
from datetime import datetime
from enum import Enum
import math
import os


# Enums
class CargoType(str, Enum):
    STANDARD = "standard"
    FRAGILE = "fragile"
    HAZMAT = "hazmat"
    REFRIGERATED = "refrigerated"


# Database Models
class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lat: float = Field(description="Latitude coordinate")
    lng: float = Field(description="Longitude coordinate")
    marked: bool = Field(default=False, description="Whether location is marked/flagged")

    # Relationships
    origin_routes: List["Route"] = Relationship(
        back_populates="location_origin",
        sa_relationship_kwargs={"foreign_keys": "[Route.location_origin_id]"}
    )
    destiny_routes: List["Route"] = Relationship(
        back_populates="location_destiny",
        sa_relationship_kwargs={"foreign_keys": "[Route.location_destiny_id]"}
    )

    def distance_to(self, other: "Location") -> float:
        """Calculate distance to another location using Haversine formula"""
        R = 6371  # Earth radius in km
        lat1, lng1 = math.radians(self.lat), math.radians(self.lng)
        lat2, lng2 = math.radians(other.lat), math.radians(other.lng)
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="client")


class Package(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    volume: float
    weight: float
    type: CargoType = Field(default=CargoType.STANDARD)

    # Foreign key
    cargo_id: Optional[int] = Field(default=None, foreign_key="cargo.id")

    # Relationship
    cargo: Optional["Cargo"] = Relationship(back_populates="packages")


class Cargo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    order_id: int = Field(foreign_key="order.id")
    truck_id: Optional[int] = Field(default=None, foreign_key="truck.id")

    # Relationships
    order: "Order" = Relationship(back_populates="cargo")
    truck: Optional["Truck"] = Relationship(back_populates="cargo_loads")
    packages: List[Package] = Relationship(back_populates="cargo")

    def total_volume(self) -> float:
        """Calculate total volume of all packages in this cargo"""
        return sum(p.volume for p in self.packages)

    def total_weight(self) -> float:
        """Calculate total weight of all packages in this cargo"""
        return sum(p.weight for p in self.packages)

    def get_types(self) -> Set[CargoType]:
        """Get unique cargo types in this shipment"""
        return {p.type for p in self.packages}
    
    def is_compatible_with(self, other_cargo: "Cargo") -> bool:
        """Check if this cargo is compatible with another cargo"""
        incompatible_pairs = [
            (CargoType.HAZMAT, CargoType.FRAGILE),
            (CargoType.HAZMAT, CargoType.REFRIGERATED)
        ]
        
        my_types = self.get_types()
        other_types = other_cargo.get_types()
        
        for type1, type2 in incompatible_pairs:
            if (type1 in my_types and type2 in other_types) or \
               (type2 in my_types and type1 in other_types):
                return False
        return True


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Location references - using the new Location entity
    location_origin_id: int = Field(foreign_key="location.id")
    location_destiny_id: int = Field(foreign_key="location.id")

    # Client and route references
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    route_id: Optional[int] = Field(default=None, foreign_key="route.id")

    contract_type: Optional[str] = Field(default=None, description="Type of service contract")

    # Relationships
    client: Optional[Client] = Relationship(back_populates="orders")
    route: Optional["Route"] = Relationship(back_populates="orders")
    cargo: List[Cargo] = Relationship(back_populates="order")

    # Location relationships
    location_origin: Location = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Order.location_origin_id]"}
    )
    location_destiny: Location = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Order.location_destiny_id]"}
    )

    def total_distance(self) -> float:
        """Calculate pickup to dropoff distance"""
        return self.location_origin.distance_to(self.location_destiny)
    
    def total_volume(self) -> float:
        """Calculate total volume of all cargo in this order"""
        return sum(c.total_volume() for c in self.cargo)
    
    def total_weight(self) -> float:
        """Calculate total weight of all cargo in this order"""
        return sum(c.total_weight() for c in self.cargo)


class Route(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Location references
    location_origin_id: int = Field(foreign_key="location.id")
    location_destiny_id: int = Field(foreign_key="location.id")

    profitability: float = Field(default=0.0)

    # Foreign keys
    truck_id: Optional[int] = Field(default=None, foreign_key="truck.id")
    
    def __init__(self, **data):
        # Extract path before calling super().__init__
        path = data.pop('path', [])
        super().__init__(**data)
        # Set path using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'path', path)

    # Relationships
    truck: Optional["Truck"] = Relationship(back_populates="routes")
    orders: List[Order] = Relationship(back_populates="route")

    # Location relationships
    location_origin: Location = Relationship(
        back_populates="origin_routes",
        sa_relationship_kwargs={"foreign_keys": "[Route.location_origin_id]"}
    )
    location_destiny: Location = Relationship(
        back_populates="destiny_routes",
        sa_relationship_kwargs={"foreign_keys": "[Route.location_destiny_id]"}
    )

    def base_distance(self) -> float:
        """Distance from origin to destination"""
        return self.location_origin.distance_to(self.location_destiny)
    
    def total_distance(self) -> float:
        """Calculate total distance including all waypoints"""
        if hasattr(self, 'path') and self.path and len(self.path) >= 2:
            total = 0.0
            for i in range(len(self.path) - 1):
                total += self.path[i].distance_to(self.path[i + 1])
            return total
        return self.base_distance()
    
    def total_time(self, base_speed_kmh: float = 80.0) -> float:
        """
        Calculate total route time in hours
        Includes driving time and stop time
        """
        distance = self.total_distance()
        drive_time = distance / base_speed_kmh
        
        # Add 15 minutes (0.25 hours) per order for loading/unloading
        stop_time = len(self.orders) * 2 * 0.25
        
        return drive_time + stop_time

    def can_serve_order(self, order: Order) -> bool:
        """Check if this route can serve an order based on locations"""
        return (self.location_origin_id == order.location_origin_id and
                self.location_destiny_id == order.location_destiny_id)
    
    def set_path(self, waypoints: List["Location"]):
        """Set the path waypoints for this route (not stored in DB)"""
        self.path = waypoints
    
    def is_within_km(self, location_coords, km: float = 1.0) -> bool:
        """
        Check if a location (lat, lng tuple) is within km distance of the route
        Checks against origin, destination, and any path waypoints
        """
        if isinstance(location_coords, tuple):
            test_location = Location(lat=location_coords[0], lng=location_coords[1])
        else:
            test_location = location_coords
        
        # Check distance to origin
        if self.location_origin.distance_to(test_location) <= km:
            return True
        
        # Check distance to destination  
        if self.location_destiny.distance_to(test_location) <= km:
            return True
        
        # Check distance to path waypoints if they exist
        # Check if route has a path attribute (for testing)
        if hasattr(self, 'path') and self.path:
            for waypoint in self.path:
                if waypoint.distance_to(test_location) <= km:
                    return True
        
        return False
    
    def deviation_time_for_stop(self, location_coords, avg_speed_kmh: float = 80.0) -> float:
        """
        Calculate additional time (in minutes) required to make a stop at the given location
        Returns 15 minutes if within 1km of route, otherwise calculates detour time
        """
        if self.is_within_km(location_coords, km=1.0):
            return 15.0  # Just stop time, no detour needed
        
        # Calculate detour distance and time
        if isinstance(location_coords, tuple):
            stop_location = Location(lat=location_coords[0], lng=location_coords[1])
        else:
            stop_location = location_coords
        
        # Simplified calculation: distance from origin to stop + stop to destination - direct distance
        detour_distance = (
            self.location_origin.distance_to(stop_location) + 
            stop_location.distance_to(self.location_destiny) - 
            self.base_distance()
        )
        
        # Convert to time (hours to minutes) and add stop time
        detour_time_minutes = (detour_distance / avg_speed_kmh) * 60
        return detour_time_minutes + 15.0  # Add 15 minutes for the stop itself
    
    def calculate_added_cost(self, order: Order) -> dict:
        """
        Calculate the additional cost/time of adding an order to this route
        Returns dict with pickup_time, dropoff_time, total_time, and any errors
        """
        try:
            # Check if order has required locations
            if not order.location_origin or not order.location_destiny:
                return {
                    "pickup_time": 0.0,
                    "dropoff_time": 0.0, 
                    "total_time": 0.0,
                    "error": "Order missing origin or destination location"
                }
            
            # Calculate time for pickup stop
            pickup_coords = (order.location_origin.lat, order.location_origin.lng)
            pickup_time = self.deviation_time_for_stop(pickup_coords)
            
            # Calculate time for dropoff stop  
            dropoff_coords = (order.location_destiny.lat, order.location_destiny.lng)
            dropoff_time = self.deviation_time_for_stop(dropoff_coords)
            
            # Total additional time
            total_time = pickup_time + dropoff_time
            
            # Return only numeric values when successful
            return {
                "pickup_time": pickup_time,
                "dropoff_time": dropoff_time, 
                "total_time": total_time
            }
            
        except Exception as e:
            return {
                "pickup_time": 0.0,
                "dropoff_time": 0.0,
                "total_time": 0.0,
                "error": f"Calculation error: {str(e)}"
            }


class Truck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    autonomy: float = Field(description="Range in km")
    capacity: float = Field(description="Volume capacity")
    type: str

    # Relationships
    routes: List[Route] = Relationship(back_populates="truck")
    cargo_loads: List[Cargo] = Relationship(back_populates="truck")

    def available_capacity(self) -> float:
        """Calculate remaining capacity"""
        used = sum(cargo.total_volume() for cargo in self.cargo_loads)
        return self.capacity - used

    def can_fit(self, volume: float) -> bool:
        """Check if truck can accommodate additional volume"""
        return volume <= self.available_capacity()

    def can_reach(self, distance: float) -> bool:
        """Check if truck can cover the distance"""
        return distance <= self.autonomy


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./logistics.db")
engine = create_engine(DATABASE_URL, echo=False)


def create_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session for FastAPI dependency injection"""
    with Session(engine) as session:
        yield session


# Helper functions for data creation
def create_location(session: Session, lat: float, lng: float, marked: bool = False) -> Location:
    """Create a location entity"""
    location = Location(lat=lat, lng=lng, marked=marked)
    session.add(location)
    session.flush()
    return location


def create_order_from_dict(session: Session, order_data: dict, client_id: Optional[int] = None) -> Order:
    """Convert your existing dict format to database models"""

    # Create or find locations
    origin_loc = create_location(
        session,
        lat=order_data['pick-up']['latitude'],
        lng=order_data['pick-up']['longitude']
    )

    destiny_loc = create_location(
        session,
        lat=order_data['drop-off']['latitude'],
        lng=order_data['drop-off']['longitude']
    )

    # Create order
    order = Order(
        location_origin_id=origin_loc.id,
        location_destiny_id=destiny_loc.id,
        client_id=client_id
    )
    session.add(order)
    session.flush()

    # Create cargo
    cargo = Cargo(order_id=order.id)
    session.add(cargo)
    session.flush()

    # Create packages
    for pkg_data in order_data['cargo']['packages']:
        package = Package(
            volume=pkg_data[0],
            weight=pkg_data[1],
            type=CargoType(pkg_data[2]),
            cargo_id=cargo.id
        )
        session.add(package)

    session.commit()
    return order
