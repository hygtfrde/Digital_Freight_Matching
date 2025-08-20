#!/usr/bin/env python3
"""
Safe Database Initialization Script for Digital Freight Matcher
Checks for existing data before seeding to prevent duplicates.
"""

import logging
import os
import sys
from io import StringIO

import pandas as pd
from sqlmodel import Session, select

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import (
    CargoType,
    Client,
    Location,
    Order,
    Package,
    Route,
    Truck,
    Cargo,
    create_location,
    create_tables,
    engine,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Contract data from Too-Big-To-Fail company
CONTRACT_DATA = """route,anchor_point,cargo_miles,total_miles,truck_cost,pallets,cargo_cost,empty_cargo_cost,markup,price_time,price_cargo,margin,stop_count,hours
1,Ringgold,101,202,342.16,20,257.62404,84.53,.50,513.24,386.4360543,.1294,2,4.0
2,Augusta,94.6,189.2,320.48,21,253.364312,67.11,.5,480.71,380.0464681,.1859,2,3.8
3,Savannah,248,496,840.15,22,695.839971,144.31,.50,1260.22,1043.759957,.2424,2,9.9
4,Albany,182,364,616.56,17,394.5984,221.96,.50,924.84,591.8976,-.040,2,7.3
5,Columbus,107,214,362.48,18,245.635591,116.85,.50,543.72,368.4533864,.0165,2,4.3"""

# Order Examples Data (from PDF)
ORDER_EXAMPLES_DATA = """point_type,lat,lng,packages_qty
Pick Up Point,33.7490,-84.3880,5
Drop Off Point,34.9162,-85.1080,
Pick Up Point,33.4735,-82.0105,3
Drop Off Point,32.0835,-81.0998,
Pick Up Point,31.5804,-84.1557,8
Drop Off Point,32.4609,-84.9877,
Pick Up Point,33.7490,-84.3880,2
Drop Off Point,33.4735,-82.0105,
Pick Up Point,32.0835,-81.0998,6
Drop Off Point,31.5804,-84.1557,"""

# Georgia city coordinates
CITY_COORDINATES = {
    "Atlanta": (33.7490, -84.3880),
    "Ringgold": (34.9162, -85.1080),
    "Augusta": (33.4735, -82.0105),
    "Savannah": (32.0835, -81.0998),
    "Albany": (31.5804, -84.1557),
    "Columbus": (32.4609, -84.9877)
}

# Current daily losses from business requirements
DAILY_LOSSES = {
    1: -53.51,   # Ringgold
    2: -50.12,   # Augusta  
    3: -131.40,  # Savannah
    4: -96.43,   # Albany
    5: -56.69    # Columbus
}

class SafeDataIngestion:
    """Safe database initialization service that checks for existing data"""
    
    def __init__(self, session: Session):
        self.session = session
        self.clients = {}
        self.locations = {}
        self.trucks = []
        self.routes = []
    
    def check_existing_data(self) -> dict:
        """Check what data already exists in the database"""
        existing = {
            'clients': self.session.exec(select(Client)).all(),
            'locations': self.session.exec(select(Location)).all(),
            'trucks': self.session.exec(select(Truck)).all(),
            'routes': self.session.exec(select(Route)).all(),
            'orders': self.session.exec(select(Order)).all(),
            'cargo': self.session.exec(select(Cargo)).all(),
            'packages': self.session.exec(select(Package)).all()
        }
        
        counts = {key: len(value) for key, value in existing.items()}
        logger.info(f"Existing data counts: {counts}")
        
        return existing, counts
    
    def is_database_initialized(self, counts: dict) -> bool:
        """Check if database appears to be already initialized with contract data"""
        # Contract data should have: 1 client, 6 locations, 5 trucks, 5 routes
        expected_minimums = {
            'clients': 1,
            'locations': 6,  # Atlanta + 5 destinations
            'trucks': 5,
            'routes': 5
        }
        
        for entity, min_count in expected_minimums.items():
            if counts.get(entity, 0) >= min_count:
                logger.info(f"Found {counts[entity]} {entity} (expected >= {min_count})")
            else:
                return False
        
        return True
    
    def find_contract_client(self) -> Client:
        """Find existing contract client or return None"""
        client = self.session.exec(
            select(Client).where(Client.name == "Too-Big-To-Fail Company")
        ).first()
        
        if client:
            logger.info(f"Found existing contract client: {client.name}")
            self.clients["contract"] = client
        
        return client
    
    def find_existing_locations(self) -> dict:
        """Find existing locations that match our city coordinates"""
        found_locations = {}
        
        for city, (lat, lng) in CITY_COORDINATES.items():
            # Look for locations within a small tolerance (0.001 degrees ≈ 100m)
            tolerance = 0.001
            location = self.session.exec(
                select(Location).where(
                    Location.lat.between(lat - tolerance, lat + tolerance),
                    Location.lng.between(lng - tolerance, lng + tolerance)
                )
            ).first()
            
            if location:
                found_locations[city] = location
                logger.info(f"Found existing location for {city}: ({location.lat}, {location.lng})")
        
        self.locations.update(found_locations)
        return found_locations
    
    def initialize_safely(self, force_reinit: bool = False):
        """Initialize database with safety checks to prevent duplicates"""
        logger.info("Starting safe database initialization...")
        
        try:
            # Check existing data
            existing_data, counts = self.check_existing_data()
            
            if not force_reinit and self.is_database_initialized(counts):
                logger.info("Database appears to be already initialized with contract data")
                logger.info("Skipping initialization to prevent duplicates")
                logger.info("Use force_reinit=True to reinitialize anyway")
                self._print_existing_summary(counts)
                return
            
            if force_reinit:
                logger.warning("Force reinitializing database (may create duplicates)")
            
            # Find existing entities to reuse
            contract_client = self.find_contract_client()
            existing_locations = self.find_existing_locations()
            
            # Initialize missing data
            if not contract_client:
                self._create_contract_client()
            
            self._ensure_all_locations()
            self._ensure_trucks()
            self._ensure_routes()
            self._ensure_contract_orders()
            self._create_example_orders_if_missing()
            
            # Commit all changes
            self.session.commit()
            
            logger.info("Safe database initialization completed successfully!")
            self._print_summary()
            
        except Exception as e:
            logger.error(f"Safe database initialization failed: {e}")
            self.session.rollback()
            raise
    
    def _create_contract_client(self):
        """Create the Too-Big-To-Fail contract client if it doesn't exist"""
        client = Client(name="Too-Big-To-Fail Company")
        self.session.add(client)
        self.session.flush()
        self.clients["contract"] = client
        logger.info(f"Created contract client: {client.name}")
    
    def _ensure_all_locations(self):
        """Ensure all required locations exist"""
        for city, (lat, lng) in CITY_COORDINATES.items():
            if city not in self.locations:
                location = create_location(self.session, lat=lat, lng=lng, marked=True)
                self.locations[city] = location
                logger.info(f"Created location {city}: ({lat}, {lng})")
            else:
                logger.info(f"Using existing location for {city}")
    
    def _ensure_trucks(self):
        """Ensure required trucks exist"""
        existing_trucks = self.session.exec(
            select(Truck).where(Truck.type.like("Specialized Contract Truck%"))
        ).all()
        
        if len(existing_trucks) >= 5:
            logger.info(f"Found {len(existing_trucks)} existing contract trucks")
            self.trucks = existing_trucks[:5]
            return
        
        # Create missing trucks
        needed = 5 - len(existing_trucks)
        start_num = len(existing_trucks) + 1
        
        for i in range(start_num, start_num + needed):
            truck = Truck(
                autonomy=800.0,
                capacity=48.0,
                type=f"Specialized Contract Truck #{i}"
            )
            self.session.add(truck)
            self.trucks.append(truck)
            logger.info(f"Created truck #{i}")
        
        self.trucks = existing_trucks + self.trucks
        self.session.flush()
    
    def _ensure_routes(self):
        """Ensure required routes exist"""
        atlanta = self.locations["Atlanta"]
        
        # Check for existing routes from Atlanta
        existing_routes = self.session.exec(
            select(Route).where(Route.location_origin_id == atlanta.id)
        ).all()
        
        if len(existing_routes) >= 5:
            logger.info(f"Found {len(existing_routes)} existing routes from Atlanta")
            self.routes = existing_routes[:5]
            return
        
        # Create missing routes
        df = pd.read_csv(StringIO(CONTRACT_DATA))
        
        for idx, row in df.iterrows():
            route_num = int(row['route'])
            anchor_point = row['anchor_point']
            
            destination = self.locations.get(anchor_point)
            if not destination:
                logger.warning(f"Destination {anchor_point} not found, skipping route {route_num}")
                continue
            
            # Check if this specific route already exists
            existing_route = self.session.exec(
                select(Route).where(
                    Route.location_origin_id == atlanta.id,
                    Route.location_destiny_id == destination.id
                )
            ).first()
            
            if existing_route:
                logger.info(f"Route {route_num} already exists: Atlanta -> {anchor_point}")
                self.routes.append(existing_route)
                continue
            
            # Create new route
            current_profitability = DAILY_LOSSES.get(route_num, 0.0)
            truck = self.trucks[idx] if idx < len(self.trucks) else None
            
            route = Route(
                location_origin_id=atlanta.id,
                location_destiny_id=destination.id,
                profitability=current_profitability,
                truck_id=truck.id if truck else None
            )
            self.session.add(route)
            self.routes.append(route)
            
            logger.info(f"Created route {route_num}: Atlanta -> {anchor_point} "
                       f"(${current_profitability:.2f}/day)")
        
        self.session.flush()
    
    def _ensure_contract_orders(self):
        """Ensure contract orders exist for each route"""
        contract_client = self.clients.get("contract")
        if not contract_client:
            logger.warning("No contract client found, skipping contract orders")
            return
        
        df = pd.read_csv(StringIO(CONTRACT_DATA))
        
        for idx, (route, row) in enumerate(zip(self.routes, df.iterrows())):
            _, data = row
            pallets = int(data['pallets'])
            
            # Check if contract order already exists for this route
            existing_order = self.session.exec(
                select(Order).where(
                    Order.route_id == route.id,
                    Order.client_id == contract_client.id,
                    Order.contract_type == "4-year binding contract"
                )
            ).first()
            
            if existing_order:
                logger.info(f"Contract order already exists for route {idx+1}")
                continue
            
            # Create contract order
            order = Order(
                location_origin_id=route.location_origin_id,
                location_destiny_id=route.location_destiny_id,
                client_id=contract_client.id,
                route_id=route.id,
                contract_type="4-year binding contract"
            )
            self.session.add(order)
            self.session.flush()
            
            # Create cargo for the order
            cargo = Cargo(order_id=order.id, truck_id=route.truck_id)
            self.session.add(cargo)
            self.session.flush()
            
            # Create packages based on pallet count
            for pallet_num in range(pallets):
                package = Package(
                    volume=1.0,  # 1 cubic meter per pallet
                    weight=500.0,  # 500kg per pallet
                    type=CargoType.STANDARD,
                    cargo_id=cargo.id
                )
                self.session.add(package)
            
            logger.info(f"Created contract order for route {idx+1}: {pallets} pallets")
    
    def _create_example_orders_if_missing(self):
        """Create example orders if they don't exist"""
        # Check if example client exists
        example_client = self.session.exec(
            select(Client).where(Client.name == "Example Client")
        ).first()
        
        if example_client:
            # Check if example orders exist
            existing_example_orders = self.session.exec(
                select(Order).where(
                    Order.client_id == example_client.id,
                    Order.contract_type.is_(None)
                )
            ).all()
            
            if existing_example_orders:
                logger.info(f"Found {len(existing_example_orders)} existing example orders")
                return
        else:
            # Create example client
            example_client = Client(name="Example Client")
            self.session.add(example_client)
            self.session.flush()
            self.clients["example"] = example_client
        
        # Create example orders from order examples data
        df = pd.read_csv(StringIO(ORDER_EXAMPLES_DATA))
        
        pickup_row = None
        order_count = 0
        
        for idx, row in df.iterrows():
            point_type = row['point_type']
            
            if point_type == "Pick Up Point":
                pickup_row = row
            elif point_type == "Drop Off Point" and pickup_row is not None:
                # Create pickup and dropoff locations
                pickup_loc = create_location(
                    self.session,
                    lat=pickup_row['lat'],
                    lng=pickup_row['lng']
                )
                
                dropoff_loc = create_location(
                    self.session,
                    lat=row['lat'],
                    lng=row['lng']
                )
                
                # Create order
                order = Order(
                    location_origin_id=pickup_loc.id,
                    location_destiny_id=dropoff_loc.id,
                    client_id=example_client.id
                )
                self.session.add(order)
                self.session.flush()
                
                # Create cargo with packages if quantity specified
                package_qty = pickup_row.get('packages_qty', 0)
                if pd.notna(package_qty) and package_qty > 0:
                    cargo = Cargo(order_id=order.id)
                    self.session.add(cargo)
                    self.session.flush()
                    
                    # Create packages
                    for _ in range(int(package_qty)):
                        package = Package(
                            volume=1.0,  # 1 cubic meter default
                            weight=25.0,  # 25 kg default
                            type=CargoType.STANDARD,
                            cargo_id=cargo.id
                        )
                        self.session.add(package)
                
                order_count += 1
                pickup_row = None
        
        logger.info(f"Created {order_count} example orders")
    
    def _print_existing_summary(self, counts: dict):
        """Print summary of existing data"""
        logger.info("\n" + "="*60)
        logger.info("EXISTING DATABASE SUMMARY")
        logger.info("="*60)
        for entity, count in counts.items():
            logger.info(f"{entity.capitalize()}: {count}")
        logger.info("="*60)
        logger.info("Database already contains data - initialization skipped")
    
    def _print_summary(self):
        """Print summary of created/updated data"""
        total_loss = sum(DAILY_LOSSES.values())
        
        logger.info("\n" + "="*60)
        logger.info("SAFE DATABASE INITIALIZATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Clients: {len(self.clients)}")
        logger.info(f"Locations: {len(self.locations)}")
        logger.info(f"Trucks: {len(self.trucks)}")
        logger.info(f"Routes: {len(self.routes)}")
        logger.info(f"Current total daily loss: ${total_loss:.2f}")
        logger.info("="*60)
        logger.info("Ready for Digital Freight Matching operations!")


def main(force_reinit: bool = False):
    """Main initialization function"""
    logger.info("Creating database tables...")
    create_tables()
    
    with Session(engine) as session:
        ingestion_service = SafeDataIngestion(session)
        ingestion_service.initialize_safely(force_reinit=force_reinit)


if __name__ == "__main__":
    # Check for force flag
    force = "--force" in sys.argv or "-f" in sys.argv
    if force:
        logger.warning("Force reinitializing database (may create duplicates)")
    
    main(force_reinit=force)