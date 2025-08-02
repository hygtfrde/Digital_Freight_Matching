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
class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="client")


class Truck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    autonomy: float = Field(description="Range in km")
    capacity: float = Field(description="Volume capacity")
    type: str

    # Relationships
    routes: List["Route"] = Relationship(back_populates="truck")
    cargo_loads: List["Cargo"] = Relationship(back_populates="truck")

    def available_capacity(self) -> float:
        used = sum(cargo.total_volume() for cargo in self.cargo_loads)
        return self.capacity - used

    def can_fit(self, volume: float) -> bool:
        return volume <= self.available_capacity()


class Route(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Origin and destination coordinates
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float

    profitability: float = 0.0

    # Foreign keys
    truck_id: Optional[int] = Field(default=None, foreign_key="truck.id")

    # Relationships
    truck: Optional[Truck] = Relationship(back_populates="routes")
    orders: List["Order"] = Relationship(back_populates="route")

    def distance_between_points(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance using Haversine formula"""
        R = 6371  # Earth radius in km
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def base_distance(self) -> float:
        """Distance from origin to destination"""
        return self.distance_between_points(self.origin_lat, self.origin_lon, self.dest_lat, self.dest_lon)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Pickup and dropoff coordinates
    pickup_lat: float
    pickup_lon: float
    dropoff_lat: float
    dropoff_lon: float

    # Foreign keys
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    route_id: Optional[int] = Field(default=None, foreign_key="route.id")

    # Relationships
    client: Optional[Client] = Relationship(back_populates="orders")
    route: Optional[Route] = Relationship(back_populates="orders")
    cargo: List["Cargo"] = Relationship(back_populates="order")


class Cargo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    order_id: int = Field(foreign_key="order.id")
    truck_id: Optional[int] = Field(default=None, foreign_key="truck.id")

    # Relationships
    order: Order = Relationship(back_populates="cargo")
    truck: Optional[Truck] = Relationship(back_populates="cargo_loads")
    packages: List["Package"] = Relationship(back_populates="cargo")

    def total_volume(self) -> float:
        return sum(p.volume for p in self.packages)

    def total_weight(self) -> float:
        return sum(p.weight for p in self.packages)

    def get_types(self) -> Set[CargoType]:
        return {p.type for p in self.packages}


class Package(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    volume: float
    weight: float
    type: CargoType = Field(default=CargoType.STANDARD)

    # Foreign key
    cargo_id: int = Field(foreign_key="cargo.id")

    # Relationship
    cargo: Cargo = Relationship(back_populates="packages")


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


# Helper function to create order from your existing dict format
def create_order_from_dict(session: Session, order_data: dict) -> Order:
    """Convert your existing dict format to database models"""
    # Create order
    order = Order(
        pickup_lat=order_data['pick-up']['latitude'],
        pickup_lon=order_data['pick-up']['longitude'],
        dropoff_lat=order_data['drop-off']['latitude'],
        dropoff_lon=order_data['drop-off']['longitude']
    )
    session.add(order)
    session.flush()  # Get order ID

    # Create cargo
    cargo = Cargo(order_id=order.id)
    session.add(cargo)
    session.flush()  # Get cargo ID

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