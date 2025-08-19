"""
========== DIGITAL FREIGHT MATCHING SYSTEM ==========

Business logic module using unified schemas from schemas.py
Maintains all original matching and pricing logic

User Input → Validation → Business Logic (DFM) → Database → Feedback
     ↑                                                        │
     └────────────────────────────────────────────────────────┘

+---------+     +---------+     +--------+     +-----------+
|  Client |-----| C_Order |-----| Cargo  |-----| Package   |
+---------+     +---------+     +--------+     +-----------+
      |             |             |               |
      |             |             |               |
      |        pickup/dropoff     |           type|
      |         Location          |               |
      |             |             |               |
      |             |             |               |
      +--------+    |             |               |
               |    |             |               |
           +--------+             |               |
           | Location|------------+               |
           +--------+                             |
                                                 \|/
                                           +--------------+
                                           |  CargoType   |
                                           +--------------+

+---------+     +-------+     +----------+     +-----------+
|  Truck  |-----| Route |-----| T_Order  |     | Location  |
+---------+     +-------+     +----------+     +-----------+

+-------------------+
|  PricingService   |
+-------------------+
| - routes          |
| - trucks          |
| - pending_orders  |
+-------------------+

"""

from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta

# Import unified schemas instead of defining redundant dataclasses
from schemas.schemas import (
    CargoType,
    Location,
    Package,
    Cargo,
    Order,
    Client,
    Truck,
    Route
)


class CriteriaMatcher:
    """
    Static class containing all matching criteria and business rules
    Unchanged logic, now using schema models
    """
    
    # Configuration constants (unchanged)
    MAX_DEVIATION_KM = 1.0
    PICKUP_DROPOFF_TIME = 0.25
    MAX_ROUTE_HOURS = 10.0
    BREAK_AFTER_HOURS = 4.0
    BREAK_DURATION = 0.5
    
    @staticmethod
    def is_location_near_route(location: Location, route_points: List[Location]) -> Tuple[bool, float]:
        """
        Check if a location is near any point on the route
        Original logic preserved
        """
        min_distance = float('inf')
        for point in route_points:
            distance = location.distance_to(point)
            if distance < min_distance:
                min_distance = distance
        return min_distance <= CriteriaMatcher.MAX_DEVIATION_KM, min_distance
    
    @staticmethod
    def can_match_route(order: Order, route: Route, truck: Truck) -> Tuple[bool, str]:
        """
        Determine if an order can be matched to a route
        Adapted to use schema's location_origin/location_destiny instead of pickup/dropoff
        """
        # Use route.path if available, otherwise construct from origin/destiny
        if route.path:
            route_points = route.path
        else:
            route_points = []
            if route.location_origin:
                route_points.append(route.location_origin)
            if route.location_destiny:
                route_points.append(route.location_destiny)
        
        if not route_points:
            return False, "Route has no defined path"
        
        # Check pickup location (now location_origin)
        if order.location_origin:
            pickup_near, pickup_dist = CriteriaMatcher.is_location_near_route(
                order.location_origin, route_points
            )
            if not pickup_near:
                return False, f"Pickup too far from route: {pickup_dist:.2f} km"
        else:
            return False, "Order has no pickup location"
        
        # Check dropoff location (now location_destiny)
        if order.location_destiny:
            dropoff_near, dropoff_dist = CriteriaMatcher.is_location_near_route(
                order.location_destiny, route_points
            )
            if not dropoff_near:
                return False, f"Dropoff too far from route: {dropoff_dist:.2f} km"
        else:
            return False, "Order has no dropoff location"
        
        # Check truck capacity using schema's methods
        order_volume = order.total_volume()
        if not truck.can_fit(order_volume):
            return False, "Insufficient truck capacity"
        
        # Check route time constraints
        new_time = route.total_time() + 2 * CriteriaMatcher.PICKUP_DROPOFF_TIME
        if new_time > CriteriaMatcher.MAX_ROUTE_HOURS:
            return False, f"Route would exceed {CriteriaMatcher.MAX_ROUTE_HOURS} hours"
        
        # Check cargo compatibility using schema's methods
        if order.cargo:
            for new_cargo in order.cargo:
                # Check against existing cargo in truck
                for existing_cargo in truck.cargo_loads:
                    if not new_cargo.is_compatible_with(existing_cargo):
                        return False, "Incompatible cargo types"
        
        return True, "Match successful"
    
    @staticmethod
    def has_incompatible_cargo(new_cargo: Cargo, existing_cargo: List[Cargo]) -> bool:
        """
        Check cargo compatibility
        Now uses the is_compatible_with method from schema
        """
        for cargo in existing_cargo:
            if not new_cargo.is_compatible_with(cargo):
                return True
        return False
    
    @staticmethod
    def calculate_route_profitability(route: Route, cost_per_mile: float, revenue_per_order: float) -> float:
        """
        Calculate route profitability
        Converts km to miles for consistency with original logic
        """
        distance_miles = route.total_distance() * 0.621371
        cost = distance_miles * cost_per_mile
        revenue = len(route.orders) * revenue_per_order
        return revenue - cost


class PricingService:
    """
    Service for managing order matching and route optimization
    Core logic preserved, adapted to use schema models
    """
    
    def __init__(self, routes: List[Route], trucks: List[Truck], cost_per_mile: float):
        """
        Initialize pricing service with routes and trucks
        """
        self.routes = routes
        self.trucks = trucks
        self.cost_per_mile = cost_per_mile
        self.pending_orders: List[Order] = []
    
    def match_order(self, order: Order) -> Optional[Tuple[Route, Truck]]:
        """
        Find the best route and truck for an order
        Original matching logic preserved
        """
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
        """
        Create a copy of route with the new order added
        Adapted to use schema's Location model
        """
        # Create new route with updated orders
        new_route = Route(
            location_origin_id=route.location_origin_id,
            location_destiny_id=route.location_destiny_id,
            location_origin=route.location_origin,
            location_destiny=route.location_destiny,
            orders=route.orders + [order],
            path=route.path.copy() if route.path else [],
            profitability=route.profitability,
            truck_id=route.truck_id
        )
        
        # Add order's locations to path if not already there
        if order.location_origin and new_route.path:
            # Simple insertion logic - can be optimized
            if order.location_origin not in new_route.path:
                # Insert pickup before last point (destination)
                if len(new_route.path) > 1:
                    new_route.path.insert(-1, order.location_origin)
                else:
                    new_route.path.append(order.location_origin)
        
        if order.location_destiny and new_route.path:
            if order.location_destiny not in new_route.path:
                # Add dropoff before final destination
                if len(new_route.path) > 1:
                    new_route.path.insert(-1, order.location_destiny)
                else:
                    new_route.path.append(order.location_destiny)
        
        return new_route
    
    def process_order(self, order_data: dict) -> Dict[str, any]:
        """
        Process an order from dictionary format
        Uses schema's create_order_from_dict helper
        """
        # Import the helper function from schemas
        from schemas.schemas import create_order_from_dict
        
        order = create_order_from_dict(order_data)
        match = self.match_order(order)
        
        if match:
            route, truck = match
            route.orders.append(order)
            
            # Add cargo to truck
            for cargo in order.cargo:
                truck.cargo_loads.append(cargo)
            
            # Update route profitability
            route.profitability = CriteriaMatcher.calculate_route_profitability(
                route, self.cost_per_mile, 50.0
            )
            
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
        """
        Attempt to create a new route from pending orders
        Original logic preserved with minor adaptation
        """
        if len(self.pending_orders) < 2:
            return None
        
        # Group pending orders by origin-destination pairs
        route_groups = {}
        for order in self.pending_orders:
            if order.location_origin and order.location_destiny:
                # Use coordinates as key since IDs might not be set
                key = (
                    order.location_origin.coordinates,
                    order.location_destiny.coordinates
                )
                if key not in route_groups:
                    route_groups[key] = []
                route_groups[key].append(order)
        
        # Find the group with most orders
        best_group = None
        max_orders = 0
        
        for key, orders in route_groups.items():
            if len(orders) > max_orders:
                max_orders = len(orders)
                best_group = orders
        
        if best_group and len(best_group) >= 2:
            # Create new route from the best group
            first_order = best_group[0]
            
            # Build path from all orders
            path = [first_order.location_origin]
            for order in best_group:
                if order.location_origin not in path:
                    path.append(order.location_origin)
                if order.location_destiny not in path:
                    path.append(order.location_destiny)
            
            if first_order.location_destiny not in path:
                path.append(first_order.location_destiny)
            
            new_route = Route(
                location_origin_id=first_order.location_origin_id,
                location_destiny_id=first_order.location_destiny_id,
                location_origin=first_order.location_origin,
                location_destiny=first_order.location_destiny,
                orders=best_group,
                path=path
            )
            
            # Calculate initial profitability
            new_route.profitability = CriteriaMatcher.calculate_route_profitability(
                new_route, self.cost_per_mile, 50.0
            )
            
            # Remove these orders from pending
            for order in best_group:
                self.pending_orders.remove(order)
            
            return new_route
        
        return None


# ============= HELPER FUNCTIONS =============

def pretty_print_order(order: Order, indent: int = 0) -> None:
    """
    Pretty print an order
    Adapted to use schema's structure
    """
    ind = " " * indent
    print(f"{ind}Order:")
    
    if order.location_origin:
        print(f"{ind}  Pickup: Location(lat={order.location_origin.lat}, lng={order.location_origin.lng})")
    
    if order.location_destiny:
        print(f"{ind}  Dropoff: Location(lat={order.location_destiny.lat}, lng={order.location_destiny.lng})")
    
    if order.cargo:
        print(f"{ind}  Cargo:")
        for cargo in order.cargo:
            for pkg in cargo.packages:
                print(f"{ind}    Package:")
                print(f"{ind}      Volume: {pkg.volume}")
                print(f"{ind}      Weight: {pkg.weight}")
                print(f"{ind}      Type: {pkg.type.value}")
    
    if order.client:
        print(f"{ind}  Client: {order.client.name if hasattr(order.client, 'name') else order.client}")
    
    if order.contract_type:
        print(f"{ind}  Contract type: {order.contract_type}")


def dfm_demo():
    """
    Demo function showing the system in action
    Updated to use schema models
    """
    # Example locations using schema
    loc1 = Location(lat=37.7749, lng=-122.4194)  # San Francisco
    loc2 = Location(lat=34.0522, lng=-118.2437)  # Los Angeles
    loc3 = Location(lat=36.1699, lng=-115.1398)  # Las Vegas
    
    # Example trucks using schema
    trucks = [
        Truck(autonomy=600.0, capacity=100.0, type="standard"),
        Truck(autonomy=800.0, capacity=150.0, type="refrigerated"),
    ]
    
    # Example routes using schema
    routes = [
        Route(
            location_origin_id=0,  # Placeholder
            location_destiny_id=0,  # Placeholder
            location_origin=loc1,
            location_destiny=loc2,
            path=[loc1, loc3, loc2]
        ),
        Route(
            location_origin_id=0,  # Placeholder
            location_destiny_id=0,  # Placeholder
            location_origin=loc2,
            location_destiny=loc3,
            path=[loc2, loc3]
        ),
    ]
    
    # Pricing service setup
    cost_per_mile = 1.5
    pricing_service = PricingService(routes=routes, trucks=trucks, cost_per_mile=cost_per_mile)
    
    # Example order data (dictionary format for compatibility)
    orders_data = [
        {
            'cargo': {
                'packages': [
                    (10.0, 5.0, 'standard'),
                    (5.0, 2.5, 'fragile')
                ]
            },
            'pick-up': {'latitude': 37.7749, 'longitude': -122.4194},
            'drop-off': {'latitude': 34.0522, 'longitude': -118.2437}
        },
        {
            'cargo': {
                'packages': [
                    (20.0, 8.0, 'refrigerated')
                ]
            },
            'pick-up': {'latitude': 36.1699, 'longitude': -115.1398},
            'drop-off': {'latitude': 34.0522, 'longitude': -118.2437}
        },
        {
            'cargo': {
                'packages': [
                    (12.0, 6.0, 'hazmat')
                ]
            },
            'pick-up': {'latitude': 34.0522, 'longitude': -118.2437},
            'drop-off': {'latitude': 36.1699, 'longitude': -115.1398}
        }
    ]
    
    # Process orders
    print("Processing orders...")
    for idx, order_data in enumerate(orders_data):
        result = pricing_service.process_order(order_data)
        print(f"Order {idx+1} result: {result}")
    
    # Show pending orders
    print("\nPending orders:")
    for pending in pricing_service.pending_orders:
        pretty_print_order(pending)
    
    # Try to create route from pending
    print("\nAttempting to create route from pending orders...")
    new_route = pricing_service.create_new_route_from_pending()
    if new_route:
        print(f"Created new route with {len(new_route.orders)} orders")
        print(f"Route profitability: ${new_route.profitability:.2f}")
    else:
        print("Could not create new route (need at least 2 pending orders with same origin/destination)")


if __name__ == "__main__":
    dfm_demo()