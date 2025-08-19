from typing import List, Dict, Tuple, Optional
from dfm import (
    CargoType, Location, Package, Cargo, Order, Client,
    Truck, Route, PricingService
)


def demo():
    # Example locations
    loc1 = Location(latitude=37.7749, longitude=-122.4194)  # San Francisco
    loc2 = Location(latitude=34.0522, longitude=-118.2437)  # Los Angeles
    loc3 = Location(latitude=36.1699, longitude=-115.1398)  # Las Vegas

    # Example trucks
    trucks = [
        Truck(autonomy=600.0, capacity=100.0, type="standard"),
        Truck(autonomy=800.0, capacity=150.0, type="refrigerated"),
    ]

    # Example routes
    routes = [
        Route(origin=loc1, destiny=loc2, path=[loc1, loc3, loc2]),
        Route(origin=loc2, destiny=loc3, path=[loc2, loc3]),
    ]

    # Pricing service setup
    cost_per_mile = 1.5
    pricing_service = PricingService(routes=routes, trucks=trucks, cost_per_mile=cost_per_mile)

    # Example order data (simulate dictionary input, e.g., from API)
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
    for idx, order_data in enumerate(orders_data):
        result = pricing_service.process_order(order_data)
        print(f"Order {idx+1} result: {result}")

    # Show pending orders
    print("\nPending orders:")
    for pending in pricing_service.pending_orders:
        pretty_print_order(pending)

if __name__ == "__main__":
    # Uncomment to run the demo
    # demo()