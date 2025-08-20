#!/usr/bin/env python3
"""
Unified Database Initialization Script for Digital Freight Matcher
Extracts data from the Google Sheets PDF and initializes the database with all starter data.
"""

import logging
import os
import sys
from io import StringIO

import pandas as pd
from sqlmodel import Session

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

# ============================================================================
# DATA FROM PDF SHEETS
# ============================================================================

# Too-Big-To-Fail Contract Data (from PDF)
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

# Price Order Calculator Data (from PDF)
PRICE_CALCULATOR_DATA = """route_name,available,price,distance_km
Route 1,True,150.00,325
Route 2,True,180.50,304
Route 3,False,0.00,798
Route 4,True,220.75,586
Route 5,True,165.25,344"""

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

class UnifiedDataIngestion:
    """Unified service to initialize database with all starter data"""
    
    def __init__(self, session: Session):
        self.session = session
        self.clients = {}
        self.locations = {}
        self.trucks = []
        self.routes = []
    
    def initialize_all_data(self):
        """Initialize database with all starter data from PDF sheets"""
        logger.info("Starting unified database initialization...")
        
        try:
            # 1. Create contract client
            self._create_contract_client()
            
            # 2. Create locations from coordinates
            self._create_locations()
            
            # 3. Create trucks from contract data
            self._create_trucks()
            
            # 4. Create routes from contract data
            self._create_routes()
            
            # 5. Create contract orders
            self._create_contract_orders()
            
            # 6. Create example orders from order examples
            self._create_example_orders()
            
            # 7. Update routes with price calculator data
            self._update_routes_with_pricing()
            
            # Commit all changes
            self.session.commit()
            
            logger.info("Database initialization completed successfully!")
            self._print_summary()
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.session.rollback()
            raise
    
    def _create_contract_client(self):
        """Create the Too-Big-To-Fail contract client"""
        client = Client(name="Too-Big-To-Fail Company")
        self.session.add(client)
        self.session.flush()
        self.clients["contract"] = client
        logger.info(f"Created contract client: {client.name}")
    
    def _create_locations(self):
        """Create all locations from city coordinates"""
        for city, (lat, lng) in CITY_COORDINATES.items():
            location = create_location(self.session, lat=lat, lng=lng, marked=True)
            self.locations[city] = location
            logger.info(f"Created location {city}: ({lat}, {lng})")
    
    def _create_trucks(self):
        """Create trucks based on contract specifications"""
        # Parse contract data to get truck count
        df = pd.read_csv(StringIO(CONTRACT_DATA))
        num_routes = len(df)
        
        for i in range(1, num_routes + 1):
            truck = Truck(
                autonomy=800.0,  # 800km range - sufficient for Georgia routes
                capacity=48.0,   # ~48 cubic meters - standard semi-trailer
                type=f"Specialized Contract Truck #{i}"
            )
            self.session.add(truck)
            self.trucks.append(truck)
            logger.info(f"Created truck #{i}")
        
        self.session.flush()
    
    def _create_routes(self):
        """Create routes from contract data"""
        df = pd.read_csv(StringIO(CONTRACT_DATA))
        atlanta = self.locations["Atlanta"]
        
        for idx, row in df.iterrows():
            route_num = int(row['route'])
            anchor_point = row['anchor_point']
            total_miles = row['total_miles']
            hours = row['hours']
            
            destination = self.locations.get(anchor_point)
            if not destination:
                logger.warning(f"Destination {anchor_point} not found, skipping route {route_num}")
                continue
            
            # Get current profitability (daily loss)
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
                       f"({total_miles} miles, {hours}hrs, ${current_profitability:.2f}/day)")
        
        self.session.flush()
    
    def _create_contract_orders(self):
        """Create contract orders for each route"""
        df = pd.read_csv(StringIO(CONTRACT_DATA))
        contract_client = self.clients["contract"]
        
        for idx, (route, row) in enumerate(zip(self.routes, df.iterrows())):
            _, data = row
            pallets = int(data['pallets'])
            
            # Create order for this route
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
    
    def _create_example_orders(self):
        """Create example orders from order examples data"""
        # Create example client
        example_client = Client(name="Example Client")
        self.session.add(example_client)
        self.session.flush()
        self.clients["example"] = example_client
        
        # Parse order examples data
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
    
    def _update_routes_with_pricing(self):
        """Update routes with pricing data from price calculator"""
        df = pd.read_csv(StringIO(PRICE_CALCULATOR_DATA))
        
        for idx, row in df.iterrows():
            if idx < len(self.routes):
                route = self.routes[idx]
                available = row['available']
                price = row['price']
                
                # Update profitability if route is available and has positive price
                if available and price > 0:
                    # This represents potential additional revenue
                    # Keep the current loss but note the potential
                    logger.info(f"Route {idx+1} has potential additional revenue: ${price:.2f}")
        
        logger.info("Updated routes with pricing data")
    
    def _print_summary(self):
        """Print summary of created data"""
        total_loss = sum(DAILY_LOSSES.values())
        
        logger.info("\n" + "="*60)
        logger.info("DATABASE INITIALIZATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Clients: {len(self.clients)}")
        logger.info(f"Locations: {len(self.locations)}")
        logger.info(f"Trucks: {len(self.trucks)}")
        logger.info(f"Routes: {len(self.routes)}")
        logger.info(f"Current total daily loss: ${total_loss:.2f}")
        logger.info("="*60)
        logger.info("Ready for Digital Freight Matching operations!")
        logger.info("Next steps:")
        logger.info("1. Run 'python verify_database.py' to verify data")
        logger.info("2. Start the DFM application")
        logger.info("3. Begin matching new orders to existing routes")


def main():
    """Main initialization function"""
    logger.info("Creating database tables...")
    create_tables()
    
    with Session(engine) as session:
        ingestion_service = UnifiedDataIngestion(session)
        ingestion_service.initialize_all_data()


if __name__ == "__main__":
    main()