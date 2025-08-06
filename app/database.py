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
    client_locations: List["Client"] = Relationship(back_populates="locations")
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
    locations: List[Location] = Relationship(back_populates="client_locations")
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


class Route(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Location references
    location_origin_id: int = Field(foreign_key="location.id")
    location_destiny_id: int = Field(foreign_key="location.id")

    profitability: float = Field(default=0.0)

    # Foreign keys
    truck_id: Optional[int] = Field(default=None, foreign_key="truck.id")

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

    def can_serve_order(self, order: Order) -> bool:
        """Check if this route can serve an order based on locations"""
        return (self.location_origin_id == order.location_origin_id and
                self.location_destiny_id == order.location_destiny_id)


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
engine = create_engine(DATABASE_URL, echo=True)


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