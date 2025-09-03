# schemas/schemas.py
"""
Pydantic schemas with business logic methods
These models serve as the single source of truth for:
1. API validation
2. Business logic operations  
3. Database ORM compatibility
"""

from pydantic import BaseModel
from typing import Optional, List, Set
from datetime import datetime
from enum import Enum
import math
from math import radians, cos, sin, asin, sqrt


# ============= ENUMS =============

class CargoType(str, Enum):
    STANDARD = "standard"
    FRAGILE = "fragile"
    HAZMAT = "hazmat"
    REFRIGERATED = "refrigerated"


# ============= MODELS WITH BUSINESS LOGIC =============

class Location(BaseModel):
    """Location model with geographic calculations"""
    id: Optional[int] = None
    lat: float
    lng: float
    marked: bool = False
    
    class Config:
        orm_mode = True
    
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
    
    @property
    def coordinates(self) -> tuple:
        """Return coordinates as tuple (lat, lng)"""
        return (self.lat, self.lng)
    
    def __str__(self) -> str:
        """String representation"""
        return f"Location({self.lat:.4f}, {self.lng:.4f})"


class Client(BaseModel):
    """Client model"""
    id: Optional[int] = None
    name: str
    created_at: datetime
    locations: List["Location"] = []
    orders: List["Order"] = []
    
    class Config:
        orm_mode = True


class Package(BaseModel):
    """Package model"""
    id: Optional[int] = None
    volume: float
    weight: float
    type: CargoType
    cargo_id: Optional[int] = None
    
    class Config:
        orm_mode = True


class Cargo(BaseModel):
    """Cargo model with calculation methods"""
    id: Optional[int] = None
    order_id: int
    truck_id: Optional[int] = None
    order: Optional["Order"] = None
    truck: Optional["Truck"] = None
    packages: List["Package"] = []
    
    class Config:
        orm_mode = True
    
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


class Order(BaseModel):
    """Order model with distance calculations"""
    id: Optional[int] = None
    location_origin_id: int
    location_destiny_id: int
    client_id: Optional[int] = None
    route_id: Optional[int] = None
    contract_type: Optional[str] = None
    
    client: Optional["Client"] = None
    route: Optional["Route"] = None
    cargo: List["Cargo"] = []
    location_origin: Optional["Location"] = None
    location_destiny: Optional["Location"] = None
    
    class Config:
        orm_mode = True
    
    def total_distance(self) -> float:
        """Calculate pickup to dropoff distance"""
        if self.location_origin and self.location_destiny:
            return self.location_origin.distance_to(self.location_destiny)
        return 0.0
    
    def total_volume(self) -> float:
        """Calculate total volume of all cargo in this order"""
        return sum(c.total_volume() for c in self.cargo)
    
    def total_weight(self) -> float:
        """Calculate total weight of all cargo in this order"""
        return sum(c.total_weight() for c in self.cargo)
    
    @property
    def is_matched(self) -> bool:
        """Check if order is matched to a route"""
        return self.route_id is not None


class Route(BaseModel):
    """Route model with optimization methods"""
    id: Optional[int] = None
    location_origin_id: int
    location_destiny_id: int
    profitability: float = 0.0
    truck_id: Optional[int] = None
    
    truck: Optional["Truck"] = None
    orders: List["Order"] = []
    location_origin: Optional["Location"] = None
    location_destiny: Optional["Location"] = None
    
    # Additional path waypoints (not in DB but useful for calculations)
    path: List["Location"] = []

    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in kilometers.
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371  # Radius of earth in kilometers.
        return c * r

    def is_within_km(self, location, km=1.0):
        """
        Checks if location (tuple: (lat, lon)) is within `km` of any point in the route.
        """
        for point in self.route_points:  # assuming route_points is a list of (lat, lon)
            if self.haversine(location[1], location[0], point[1], point[0]) <= km:
                return True
        return False
    
    def calculate_added_cost(self, order):
        """
        Calculate the cost of adding this order to the route.
        Can call deviation_time_for_stop, extra distance, etc.
        """
        pickup_time = self.deviation_time_for_stop(order.pickup_location)
        dropoff_time = self.deviation_time_for_stop(order.dropoff_location)
        # Add more calculations as needed (e.g., fuel, tolls)
        total_time = pickup_time + dropoff_time
        # Return a dict or a cost object
        return {
            "pickup_time": pickup_time,
            "dropoff_time": dropoff_time,
            "total_time": total_time,
            # ... other computed costs ...
        }
    
    def deviation_time_for_stop(self, location, avg_speed_kmh=30):
        """
        Returns deviation time in minutes for the stop at the given location.
        """
        if self.is_within_km(location, km=1.0):
            # Deviation is only the stop time
            return 15
        else:
            # Calculate detour (will not qualify, but for completeness)
            min_dist = min(
                self.haversine(location[1], location[0], point[1], point[0]) 
                for point in self.route_points
            )
            # Time = distance / speed * 60 for minutes, + 15 min stop
            return 15 + (min_dist / avg_speed_kmh) * 60
        

    
    class Config:
        orm_mode = True
    
    def base_distance(self) -> float:
        """Distance from origin to destination"""
        if self.location_origin and self.location_destiny:
            return self.location_origin.distance_to(self.location_destiny)
        return 0.0
    
    def total_distance(self) -> float:
        """Calculate total distance including all waypoints"""
        if len(self.path) < 2:
            return self.base_distance()
        
        total = 0.0
        for i in range(len(self.path) - 1):
            total += self.path[i].distance_to(self.path[i + 1])
        return total
    
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
    
    def can_serve_order(self, order: "Order") -> bool:
        """Check if this route can serve an order based on locations"""
        return (self.location_origin_id == order.location_origin_id and
                self.location_destiny_id == order.location_destiny_id)
    
    def calculate_profitability(self, cost_per_km: float, revenue_per_order: float) -> float:
        """Calculate route profitability"""
        distance_km = self.total_distance()
        cost = distance_km * cost_per_km
        revenue = len(self.orders) * revenue_per_order
        self.profitability = revenue - cost
        return self.profitability


class Truck(BaseModel):
    """Truck model with capacity management"""
    id: Optional[int] = None
    autonomy: float  # Range in km
    capacity: float  # Volume capacity in m³
    type: str
    
    routes: List["Route"] = []
    cargo_loads: List["Cargo"] = []
    
    class Config:
        orm_mode = True
    
    def available_capacity(self) -> float:
        """Calculate remaining capacity"""
        if self.capacity <= 0:
            return 0.0
        used = sum(cargo.total_volume() for cargo in self.cargo_loads)
        return max(0.0, self.capacity - used)
    
    def can_fit(self, volume: float) -> bool:
        """Check if truck can accommodate additional volume"""
        if volume < 0:
            return False
        return volume <= self.available_capacity()
    
    def can_fit_cargo(self, cargo: "Cargo") -> bool:
        """Check if truck can fit a specific cargo (volume and compatibility)"""
        if not cargo:
            return False
        
        # Check volume capacity
        if not self.can_fit(cargo.total_volume()):
            return False
        
        # Check cargo type compatibility
        if not self.is_compatible_with_cargo(cargo):
            return False
        
        # Check compatibility with existing cargo
        for existing_cargo in self.cargo_loads:
            if not cargo.is_compatible_with(existing_cargo):
                return False
        
        return True
    
    def can_reach(self, distance: float) -> bool:
        """Check if truck can cover the distance"""
        if distance < 0:
            return False
        return distance <= self.autonomy
    
    def utilization_percent(self) -> float:
        """Calculate capacity utilization percentage"""
        if self.capacity <= 0:
            return 0.0
        used = sum(cargo.total_volume() for cargo in self.cargo_loads)
        return min(100.0, (used / self.capacity) * 100)
    
    def is_compatible_with_cargo(self, cargo: "Cargo") -> bool:
        """Check if truck type is compatible with cargo type"""
        if not cargo or not cargo.packages:
            return True
        
        cargo_types = cargo.get_types()
        
        # Refrigerated trucks needed for refrigerated cargo
        if CargoType.REFRIGERATED in cargo_types and self.type != "refrigerated":
            return False
        
        # Hazmat certified trucks needed for hazmat cargo
        if CargoType.HAZMAT in cargo_types and self.type != "hazmat":
            return False
        
        return True
    
    def get_capacity_after_drop(self, route: "Route", drop_location: "Location") -> float:
        """Calculate remaining capacity after dropping cargo at specified location"""
        if not route or not drop_location:
            return self.available_capacity()
        
        # Find all cargo that gets dropped at this location
        dropped_volume = 0.0
        
        for cargo in self.cargo_loads:
            # Check if this cargo's order has destination at drop_location
            if (
                cargo.order and 
                cargo.order.location_destiny and 
                cargo.order.location_destiny.id == drop_location.id
            ):
                dropped_volume += cargo.total_volume()
        
        # Return current available capacity plus what gets dropped
        return min(self.capacity, self.available_capacity() + dropped_volume)
    
    def get_cargo_for_location(self, location: "Location") -> List["Cargo"]:
        """Get all cargo destined for a specific location"""
        if not location:
            return []
        
        cargo_for_location = []
        for cargo in self.cargo_loads:
            if (
                cargo.order and 
                cargo.order.location_destiny and 
                cargo.order.location_destiny.id == location.id
            ):
                cargo_for_location.append(cargo)
        
        return cargo_for_location
    
    def total_cargo_volume(self) -> float:
        """Calculate total volume of all cargo currently loaded"""
        return sum(cargo.total_volume() for cargo in self.cargo_loads)
    
    def total_cargo_weight(self) -> float:
        """Calculate total weight of all cargo currently loaded"""
        return sum(cargo.total_weight() for cargo in self.cargo_loads)
    
    def is_overloaded(self) -> bool:
        """Check if truck is over capacity"""
        return self.total_cargo_volume() > self.capacity



# ============= FORWARD REFERENCES UPDATE =============
# This is necessary to avoid circular import issues

Client.update_forward_refs()
Order.update_forward_refs()
Cargo.update_forward_refs()
Package.update_forward_refs()
Route.update_forward_refs()
Truck.update_forward_refs()
Location.update_forward_refs()

# update forward refs is deprecated in pydantic v2
# use model_rebuild() if upgrading to pydantic v2


# ============= HELPER FUNCTIONS =============

def create_order_from_dict(order_data: dict) -> Order:
    """
    Helper to create Order from dictionary format
    Used for API compatibility with legacy format
    """
    # This creates schema objects, not DB objects
    # For DB operations, use the database.py version
    
    origin = Location(
        lat=order_data['pick-up']['latitude'],
        lng=order_data['pick-up']['longitude']
    )
    
    destiny = Location(
        lat=order_data['drop-off']['latitude'],
        lng=order_data['drop-off']['longitude']
    )
    
    packages = []
    for pkg_data in order_data['cargo']['packages']:
        package = Package(
            volume=pkg_data[0],
            weight=pkg_data[1],
            type=CargoType(pkg_data[2])
        )
        packages.append(package)
    
    # Note: This creates schema objects for validation/calculation
    # Actual DB persistence needs proper IDs and session handling
    cargo = Cargo(
        order_id=0,  # Placeholder - will be set when saved to DB
        packages=packages
    )
    
    order = Order(
        location_origin_id=0,  # Placeholder
        location_destiny_id=0,  # Placeholder
        location_origin=origin,
        location_destiny=destiny,
        cargo=[cargo]
    )
    
    return order