#!/usr/bin/env python3
"""
Initialize database with contract data from Too-Big-To-Fail company.
This script creates the initial routes, trucks, and locations based on the 4-year binding contract.
"""

import pandas as pd
from io import StringIO
from sqlmodel import Session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import (
    Location, Client, Route, Truck, Order, Cargo, Package, CargoType,
    engine, create_tables, create_location
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Contract data from Too-Big-To-Fail company
contract_data = """route,anchor_point,cargo_miles,total_miles,truck_cost,pallets,cargo_cost,empty_cargo_cost,markup,price_time,price_cargo,margin,stop_count,hours
1,Ringgold,101,202,342.16,20,257.62404,84.53,.50,513.24,386.4360543,.1294,2,4.0
2,Augusta,94.6,189.2,320.48,21,253.364312,67.11,.5,480.71,380.0464681,.1859,2,3.8
3,Savannah,248,496,840.15,22,695.839971,144.31,.50,1260.22,1043.759957,.2424,2,9.9
4,Albany,182,364,616.56,17,394.5984,221.96,.50,924.84,591.8976,-.040,2,7.3
5,Columbus,107,214,362.48,18,245.635591,116.85,.50,543.72,368.4533864,.0165,2,4.3"""

# Georgia city coordinates (approximate)
CITY_COORDINATES = {
    "Atlanta": (33.7490, -84.3880),  # Origin point
    "Ringgold": (34.9162, -85.1080),
    "Augusta": (33.4735, -82.0105),
    "Savannah": (32.0835, -81.0998),
    "Albany": (31.5804, -84.1557),
    "Columbus": (32.4609, -84.9877)
}


def create_contract_client(session: Session) -> Client:
    """Create the Too-Big-To-Fail contract client"""
    client = Client(name="Too-Big-To-Fail Company")
    session.add(client)
    session.flush()
    logger.info(f"Created contract client: {client.name}")
    return client


def create_atlanta_origin(session: Session) -> Location:
    """Create Atlanta as the origin location for all routes"""
    atlanta_lat, atlanta_lng = CITY_COORDINATES["Atlanta"]
    atlanta = create_location(session, lat=atlanta_lat, lng=atlanta_lng, marked=True)
    logger.info(f"Created Atlanta origin location: {atlanta.lat}, {atlanta.lng}")
    return atlanta


def create_destination_locations(session: Session) -> dict:
    """Create destination locations for all contract routes"""
    destinations = {}
    
    for city, (lat, lng) in CITY_COORDINATES.items():
        if city != "Atlanta":  # Skip origin
            location = create_location(session, lat=lat, lng=lng, marked=True)
            destinations[city] = location
            logger.info(f"Created destination {city}: {lat}, {lng}")
    
    return destinations


def create_contract_trucks(session: Session, num_trucks: int = 5) -> list:
    """Create the 5 specialized trucks mentioned in business requirements"""
    trucks = []
    
    for i in range(1, num_trucks + 1):
        truck = Truck(
            autonomy=800.0,  # 800km range - sufficient for Georgia routes
            capacity=48.0,   # ~48 cubic meters - standard semi-trailer
            type=f"Specialized Contract Truck #{i}"
        )
        session.add(truck)
        trucks.append(truck)
        logger.info(f"Created truck #{i}")
    
    session.flush()
    return trucks


def create_contract_routes(session: Session, atlanta: Location, destinations: dict, trucks: list) -> list:
    """Create the 5 contract routes with their current profitability"""
    
    # Parse contract data
    df = pd.read_csv(StringIO(contract_data))
    routes = []
    
    for idx, row in df.iterrows():
        route_num = int(row['route'])
        anchor_point = row['anchor_point']
        total_miles = row['total_miles']
        margin = row['margin']
        hours = row['hours']
        pallets = row['pallets']
        
        # Get destination location
        destination = destinations.get(anchor_point)
        if not destination:
            logger.warning(f"Destination {anchor_point} not found, skipping route {route_num}")
            continue
        
        # Calculate current profitability (negative based on business requirements)
        # Convert margin to daily loss - these are the current losses mentioned in bus-reqs.md
        daily_losses = {
            1: -53.51,   # Ringgold
            2: -50.12,   # Augusta  
            3: -131.40,  # Savannah
            4: -96.43,   # Albany
            5: -56.69    # Columbus
        }
        
        current_profitability = daily_losses.get(route_num, 0.0)
        
        # Create route
        route = Route(
            location_origin_id=atlanta.id,
            location_destiny_id=destination.id,
            profitability=current_profitability,
            truck_id=trucks[idx].id if idx < len(trucks) else None
        )
        session.add(route)
        routes.append(route)
        
        logger.info(f"Created route {route_num}: Atlanta -> {anchor_point} "
                   f"({total_miles} miles, {hours}hrs, ${current_profitability:.2f} daily)")
    
    session.flush()
    return routes


def create_contract_orders(session: Session, client: Client, routes: list) -> list:
    """Create the existing contract orders for each route"""
    orders = []
    
    # Parse contract data again for order details
    df = pd.read_csv(StringIO(contract_data))
    
    for idx, (route, row) in enumerate(zip(routes, df.iterrows())):
        _, data = row
        pallets = int(data['pallets'])
        
        # Create order for this route
        order = Order(
            location_origin_id=route.location_origin_id,
            location_destiny_id=route.location_destiny_id,
            client_id=client.id,
            route_id=route.id,
            contract_type="4-year binding contract"
        )
        session.add(order)
        session.flush()
        
        # Create cargo for the order
        cargo = Cargo(order_id=order.id, truck_id=route.truck_id)
        session.add(cargo)
        session.flush()
        
        # Create packages based on pallet count
        # Assume each pallet = 1 cubic meter, 500kg
        for pallet_num in range(pallets):
            package = Package(
                volume=1.0,  # 1 cubic meter per pallet
                weight=500.0,  # 500kg per pallet
                type=CargoType.STANDARD,
                cargo_id=cargo.id
            )
            session.add(package)
        
        orders.append(order)
        logger.info(f"Created contract order for route {idx+1}: {pallets} pallets")
    
    return orders


def initialize_contract_database():
    """Main function to initialize the database with contract data"""
    logger.info("Initializing database with Too-Big-To-Fail contract data...")
    
    # Create tables
    create_tables()
    
    with Session(engine) as session:
        try:
            # 1. Create contract client
            client = create_contract_client(session)
            
            # 2. Create locations
            atlanta = create_atlanta_origin(session)
            destinations = create_destination_locations(session)
            
            # 3. Create trucks
            trucks = create_contract_trucks(session)
            
            # 4. Create routes
            routes = create_contract_routes(session, atlanta, destinations, trucks)
            
            # 5. Create contract orders
            orders = create_contract_orders(session, client, routes)
            
            # Commit all changes
            session.commit()
            
            logger.info("✅ Database initialization completed successfully!")
            logger.info(f"Created: {len(trucks)} trucks, {len(routes)} routes, {len(orders)} contract orders")
            logger.info("Current daily loss: $-388.15 total across all routes")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    initialize_contract_database()