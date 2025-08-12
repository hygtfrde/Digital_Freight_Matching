# CLAUDE GENERATED

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
import math
from enum import Enum

class CargoType(Enum):
    STANDARD = "standard"
    FRAGILE = "fragile"
    HAZMAT = "hazmat"
    REFRIGERATED = "refrigerated"

@dataclass
class Location:
    latitude: float
    longitude: float
    marked: bool = False
    
    def distance_to(self, other: 'Location') -> float:
        R = 6371
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

@dataclass
class Package:
    volume: float
    weight: float
    type: CargoType

@dataclass
class Cargo:
    packages: List[Package]
    
    def total_volume(self) -> float:
        return sum(p.volume for p in self.packages)
    
    def total_weight(self) -> float:
        return sum(p.weight for p in self.packages)
    
    def get_types(self) -> set:
        return {p.type for p in self.packages}

@dataclass
class Order:
    cargo: Cargo
    pickup: Location
    dropoff: Location
    client: Optional['Client'] = None
    contract_type: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Order':
        packages = []
        for p in data['cargo']['packages']:
            packages.append(Package(
                volume=p[0],
                weight=p[1],
                type=CargoType(p[2])
            ))
        cargo = Cargo(packages=packages)
        pickup = Location(**data['pick-up'])
        dropoff = Location(**data['drop-off'])
        return cls(cargo=cargo, pickup=pickup, dropoff=dropoff)

@dataclass
class Client:
    locations: List[Location]

@dataclass
class Truck:
    autonomy: float
    capacity: float
    type: str
    cargo: List[Cargo] = None
    
    def __post_init__(self):
        if self.cargo is None:
            self.cargo = []
    
    def available_capacity(self) -> float:
        used = sum(c.total_volume() for c in self.cargo)
        return self.capacity - used
    
    def can_fit(self, cargo: Cargo) -> bool:
        return cargo.total_volume() <= self.available_capacity()

@dataclass
class Route:
    origin: Location
    destiny: Location
    orders: List[Order] = None
    profitability: float = 0.0
    path: List[Location] = None
    
    def __post_init__(self):
        if self.orders is None:
            self.orders = []
        if self.path is None:
            self.path = []
    
    def total_distance(self) -> float:
        if len(self.path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(self.path) - 1):
            total += self.path[i].distance_to(self.path[i + 1])
        return total
    
    def total_time(self, base_speed_mph: float = 50) -> float:
        distance = self.total_distance()
        drive_time = (distance * 0.621371) / base_speed_mph
        # does this work if there's no break?
        stop_time = len(self.orders) * 2 * 0.25
        return drive_time + stop_time

class CriteriaMatcher:
    MAX_DEVIATION_KM = 1.0
    PICKUP_DROPOFF_TIME = 0.25
    MAX_ROUTE_HOURS = 10.0
    BREAK_AFTER_HOURS = 4.0
    BREAK_DURATION = 0.5
    
    @staticmethod
    def is_location_near_route(location: Location, route_points: List[Location]) -> Tuple[bool, float]:
        min_distance = float('inf')
        for point in route_points:
            distance = location.distance_to(point)
            if distance < min_distance:
                min_distance = distance
        return min_distance <= CriteriaMatcher.MAX_DEVIATION_KM, min_distance
    
    @staticmethod
    def can_match_route(order: Order, route: Route, truck: Truck) -> Tuple[bool, str]:
        pickup_near, pickup_dist = CriteriaMatcher.is_location_near_route(order.pickup, route.path)
        if not pickup_near:
            return False, f"Pickup too far from route: {pickup_dist:.2f} km"
        
        dropoff_near, dropoff_dist = CriteriaMatcher.is_location_near_route(order.dropoff, route.path)
        if not dropoff_near:
            return False, f"Dropoff too far from route: {dropoff_dist:.2f} km"
        
        if not truck.can_fit(order.cargo):
            return False, "Insufficient truck capacity"
        
        new_time = route.total_time() + 2 * CriteriaMatcher.PICKUP_DROPOFF_TIME
        if new_time > CriteriaMatcher.MAX_ROUTE_HOURS:
            return False, f"Route would exceed {CriteriaMatcher.MAX_ROUTE_HOURS} hours"
        
        if CriteriaMatcher.has_incompatible_cargo(order.cargo, truck.cargo):
            return False, "Incompatible cargo types"
        
        return True, "Match successful"
    
    @staticmethod
    def has_incompatible_cargo(new_cargo: Cargo, existing_cargo: List[Cargo]) -> bool:
        incompatible_pairs = [
            (CargoType.HAZMAT, CargoType.FRAGILE),
            (CargoType.HAZMAT, CargoType.REFRIGERATED)
        ]
        
        new_types = new_cargo.get_types()
        existing_types = set()
        for cargo in existing_cargo:
            existing_types.update(cargo.get_types())
        
        for type1, type2 in incompatible_pairs:
            if (type1 in new_types and type2 in existing_types) or \
               (type2 in new_types and type1 in existing_types):
                return True
        return False
    
    @staticmethod
    def calculate_route_profitability(route: Route, cost_per_mile: float, revenue_per_order: float) -> float:
        distance_miles = route.total_distance() * 0.621371
        cost = distance_miles * cost_per_mile
        revenue = len(route.orders) * revenue_per_order
        return revenue - cost

class PricingService:
    def __init__(self, routes: List[Route], trucks: List[Truck], cost_per_mile: float):
        self.routes = routes
        self.trucks = trucks
        self.cost_per_mile = cost_per_mile
        self.pending_orders = []
    
    def match_order(self, order: Order) -> Optional[Tuple[Route, Truck]]:
        best_match = None
        best_profit_increase = float('-inf')
        
        for i, route in enumerate(self.routes):
            if i < len(self.trucks):
                truck = self.trucks[i]
                can_match, _ = CriteriaMatcher.can_match_route(order, route, truck)
                if can_match:
                    current_profit = route.profitability
                    test_route = self._add_order_to_route(route, order)
                    new_profit = CriteriaMatcher.calculate_route_profitability(
                        test_route, self.cost_per_mile, 50.0
                    )
                    profit_increase = new_profit - current_profit
                    
                    if profit_increase > best_profit_increase:
                        best_profit_increase = profit_increase
                        best_match = (route, truck)
        
        return best_match
    
    def _add_order_to_route(self, route: Route, order: Order) -> Route:
        new_route = Route(
            origin=route.origin,
            destiny=route.destiny,
            orders=route.orders + [order],
            path=route.path.copy()
        )
        return new_route
    
    def process_order(self, order_data: dict) -> Dict[str, any]:
        order = Order.from_dict(order_data)
        match = self.match_order(order)
        
        if match:
            route, truck = match
            route.orders.append(order)
            truck.cargo.append(order.cargo)
            return {
                "status": "matched",
                "route": self.routes.index(route) + 1,
                "truck": self.trucks.index(truck) + 1
            }
        else:
            self.pending_orders.append(order)
            return {
                "status": "pending",
                "reason": "No suitable route found"
            }
    
    def create_new_route_from_pending(self) -> Optional[Route]:
        if len(self.pending_orders) < 2:
            return None
        
        return None