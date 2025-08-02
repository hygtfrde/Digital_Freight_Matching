from sqlmodel import Session, select
from typing import List, Tuple, Optional, Dict
from .models import (
    Order, Route, Truck, Cargo, Package, CargoType,
    OrderCreate, RoutePoint
)


class CriteriaMatcher:
    MAX_DEVIATION_KM = 1.0
    PICKUP_DROPOFF_TIME = 0.25
    MAX_ROUTE_HOURS = 10.0
    BREAK_AFTER_HOURS = 4.0
    BREAK_DURATION = 0.5

    @staticmethod
    def is_location_near_route(lat: float, lon: float, route: Route) -> Tuple[bool, float]:
        """Check if a location is near a route, considering origin, destination, and route points"""
        min_distance = float('inf')

        # Check distance to origin
        origin_distance = route._calculate_distance(
            lat, lon, route.origin_latitude, route.origin_longitude
        )
        min_distance = min(min_distance, origin_distance)

        # Check distance to destination
        dest_distance = route._calculate_distance(
            lat, lon, route.destiny_latitude, route.destiny_longitude
        )
        min_distance = min(min_distance, dest_distance)

        # Check distance to all route points
        for point in route.route_points:
            point_distance = route._calculate_distance(
                lat, lon, point.latitude, point.longitude
            )
            min_distance = min(min_distance, point_distance)

        return min_distance <= CriteriaMatcher.MAX_DEVIATION_KM, min_distance

    @staticmethod
    def can_match_route(order: Order, route: Route, truck: Truck) -> Tuple[bool, str]:
        """Check if an order can be matched to a route with a specific truck"""
        # Check pickup location proximity
        pickup_near, pickup_dist = CriteriaMatcher.is_location_near_route(
            order.pickup_latitude, order.pickup_longitude, route
        )
        if not pickup_near:
            return False, f"Pickup too far from route: {pickup_dist:.2f} km"

        # Check dropoff location proximity
        dropoff_near, dropoff_dist = CriteriaMatcher.is_location_near_route(
            order.dropoff_latitude, order.dropoff_longitude, route
        )
        if not dropoff_near:
            return False, f"Dropoff too far from route: {dropoff_dist:.2f} km"

        # Calculate total volume needed for this order
        order_volume = sum(cargo.total_volume() for cargo in order.cargo)
        if not truck.can_fit(order_volume):
            return False, "Insufficient truck capacity"

        # Check time constraints
        new_time = route.total_time() + 2 * CriteriaMatcher.PICKUP_DROPOFF_TIME
        if new_time > CriteriaMatcher.MAX_ROUTE_HOURS:
            return False, f"Route would exceed {CriteriaMatcher.MAX_ROUTE_HOURS} hours"

        # Check cargo compatibility
        if CriteriaMatcher.has_incompatible_cargo(order.cargo, truck.cargo_loads):
            return False, "Incompatible cargo types"

        return True, "Match successful"

    @staticmethod
    def has_incompatible_cargo(new_cargo_list: List[Cargo], existing_cargo_list: List[Cargo]) -> bool:
        """Check for incompatible cargo types between new and existing cargo"""
        incompatible_pairs = [
            (CargoType.HAZMAT, CargoType.FRAGILE),
            (CargoType.HAZMAT, CargoType.REFRIGERATED)
        ]

        # Get all types from new cargo
        new_types = set()
        for cargo in new_cargo_list:
            new_types.update(cargo.get_types())

        # Get all types from existing cargo
        existing_types = set()
        for cargo in existing_cargo_list:
            existing_types.update(cargo.get_types())

        # Check for incompatible combinations
        for type1, type2 in incompatible_pairs:
            if (type1 in new_types and type2 in existing_types) or \
                    (type2 in new_types and type1 in existing_types):
                return True
        return False

    @staticmethod
    def calculate_route_profitability(route: Route, cost_per_mile: float, revenue_per_order: float) -> float:
        """Calculate profitability for a route"""
        distance_miles = route.total_distance() * 0.621371
        cost = distance_miles * cost_per_mile
        revenue = len(route.orders) * revenue_per_order
        return revenue - cost


class PricingService:
    def __init__(self, cost_per_mile: float, revenue_per_order: float = 50.0):
        self.cost_per_mile = cost_per_mile
        self.revenue_per_order = revenue_per_order

    def find_available_routes_with_trucks(self, session: Session) -> List[Tuple[Route, Truck]]:
        """Find all routes that have assigned trucks and are available for new orders"""
        statement = (
            select(Route, Truck)
            .join(Truck, Route.truck_id == Truck.id)
            .where(Route.truck_id.is_not(None))
        )
        results = session.exec(statement).all()
        return [(route, truck) for route, truck in results]

    def match_order(self, session: Session, order: Order) -> Optional[Tuple[Route, Truck]]:
        """Find the best route and truck match for an order"""
        available_routes = self.find_available_routes_with_trucks(session)

        best_match = None
        best_profit_increase = float('-inf')

        for route, truck in available_routes:
            can_match, reason = CriteriaMatcher.can_match_route(order, route, truck)

            if can_match:
                # Calculate profit increase
                current_profit = route.profitability
                potential_profit = CriteriaMatcher.calculate_route_profitability(
                    route, self.cost_per_mile, self.revenue_per_order
                )
                # Add revenue for the new order
                potential_profit += self.revenue_per_order
                profit_increase = potential_profit - current_profit

                if profit_increase > best_profit_increase:
                    best_profit_increase = profit_increase
                    best_match = (route, truck)

        return best_match

    def create_order_from_data(self, session: Session, order_data: dict) -> Order:
        """Create Order and related Cargo/Package objects from dict data"""
        # Create the main order
        order = Order(
            pickup_latitude=order_data['pick-up']['latitude'],
            pickup_longitude=order_data['pick-up']['longitude'],
            pickup_marked=order_data['pick-up'].get('marked', False),
            dropoff_latitude=order_data['drop-off']['latitude'],
            dropoff_longitude=order_data['drop-off']['longitude'],
            dropoff_marked=order_data['drop-off'].get('marked', False)
        )

        session.add(order)
        session.flush()  # Get the order ID without committing

        # Create cargo container
        cargo = Cargo(order_id=order.id)
        session.add(cargo)
        session.flush()  # Get the cargo ID

        # Create packages
        packages = []
        for pkg_data in order_data['cargo']['packages']:
            package = Package(
                volume=pkg_data[0],
                weight=pkg_data[1],
                type=CargoType(pkg_data[2]),
                cargo_id=cargo.id
            )
            packages.append(package)
            session.add(package)

        return order

    def assign_order_to_route(self, session: Session, order: Order, route: Route, truck: Truck) -> None:
        """Assign an order to a route and truck"""
        # Update order relationships
        order.route_id = route.id

        # Assign cargo to truck
        for cargo in order.cargo:
            cargo.truck_id = truck.id

        # Update route profitability
        route.profitability = CriteriaMatcher.calculate_route_profitability(
            route, self.cost_per_mile, self.revenue_per_order
        )

        session.add(order)
        session.add(route)

    def process_order(self, session: Session, order_data: dict) -> Dict[str, any]:
        """Process an order request and try to match it to existing routes"""
        try:
            # Create order from data
            order = self.create_order_from_data(session, order_data)

            # Try to match to existing route
            match = self.match_order(session, order)

            if match:
                route, truck = match
                self.assign_order_to_route(session, order, route, truck)

                session.commit()

                return {
                    "status": "matched",
                    "order_id": order.id,
                    "route_id": route.id,
                    "truck_id": truck.id,
                    "profitability": route.profitability
                }
            else:
                # No match found - order remains unassigned
                session.commit()

                return {
                    "status": "pending",
                    "order_id": order.id,
                    "reason": "No suitable route found"
                }

        except Exception as e:
            session.rollback()
            return {
                "status": "error",
                "reason": f"Failed to process order: {str(e)}"
            }

    def get_pending_orders(self, session: Session) -> List[Order]:
        """Get all orders that haven't been assigned to routes"""
        statement = select(Order).where(Order.route_id.is_(None))
        return list(session.exec(statement).all())

    def create_new_route_from_pending(self, session: Session, truck_id: int) -> Optional[Route]:
        """Create a new route from pending orders (basic implementation)"""
        pending_orders = self.get_pending_orders(session)

        if len(pending_orders) < 2:
            return None

        # Simple implementation: use first two pending orders
        # In practice, you'd want more sophisticated route optimization
        order1, order2 = pending_orders[0], pending_orders[1]

        # Create route using first order's pickup as origin, second order's dropoff as destination
        route = Route(
            origin_latitude=order1.pickup_latitude,
            origin_longitude=order1.pickup_longitude,
            destiny_latitude=order2.dropoff_latitude,
            destiny_longitude=order2.dropoff_longitude,
            truck_id=truck_id
        )

        session.add(route)
        session.flush()

        # Assign orders to the new route
        truck = session.get(Truck, truck_id)
        if truck:
            self.assign_order_to_route(session, order1, route, truck)
            self.assign_order_to_route(session, order2, route, truck)

            session.commit()
            return route

        session.rollback()
        return None

    def get_route_summary(self, session: Session, route_id: int) -> Optional[Dict]:
        """Get summary information for a route"""
        route = session.get(Route, route_id)
        if not route:
            return None

        return {
            "route_id": route.id,
            "truck_id": route.truck_id,
            "total_orders": len(route.orders),
            "total_distance_km": route.total_distance(),
            "estimated_time_hours": route.total_time(),
            "profitability": route.profitability,
            "origin": {
                "latitude": route.origin_latitude,
                "longitude": route.origin_longitude
            },
            "destination": {
                "latitude": route.destiny_latitude,
                "longitude": route.destiny_longitude
            }
        }