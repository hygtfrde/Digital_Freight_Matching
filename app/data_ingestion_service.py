# data_ingestion.py
import logging
from typing import Dict, List, Optional

import pandas as pd
from sqlmodel import Session

from .database import (
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service to ingest CSV data into the SQLModel database"""

    def __init__(self, session: Session):
        self.session = session

    def ingest_orders_from_csv(self, csv_path: str, client_name: str = "Default Client") -> List[Order]:
        """
        Ingest orders from the Orders Examples CSV format.
        - pair pickup/dropoff points based on data structure
        - create a default client if none specified
        - handle missing package quantities gracefully
        """
        logger.info(f"Starting ingestion from {csv_path}")

        # Read CSV data
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from CSV")

        # Create or get client
        client = self._get_or_create_client(client_name)

        # Process pickup/dropoff pairs
        orders = []
        pickup_row = None

        for idx, row in df.iterrows():
            point_type = row.iloc[0]  # First column indicates point type

            if point_type == "Pick Up Point":
                pickup_row = row
            elif point_type == "Drop Off Point" and pickup_row is not None:
                order = self._create_order_from_pair(pickup_row, row, client.id)
                if order:
                    orders.append(order)
                pickup_row = None

        self.session.commit()
        logger.info(f"Successfully created {len(orders)} orders")
        return orders

    def ingest_truck_data_from_contract(self, csv_path: str) -> List[Truck]:
        """
        Extract truck information from the contract CSV.
        - parse the structured but non-standard CSV format
        - extract key truck specifications from the data
        - convert units appropriately (cubic feet to cubic meters, etc.)
        """
        logger.info(f"Ingesting truck data from {csv_path}")

        # Read the contract file - it has a complex structure
        df = pd.read_csv(csv_path, header=None)

        trucks = []

        # Extract truck information from the structured data
        # Based on the CSV structure
        try:
            # Find the truck information section
            truck_info = self._parse_truck_section(df)

            if truck_info:
                truck = Truck(
                    autonomy=truck_info.get('autonomy', 500.0),  # Default 500km if not specified
                    capacity=truck_info.get('capacity', 48.0),  # Convert cubic feet to cubic meters
                    type=truck_info.get('type', 'Standard Semi-Truck')
                )
                self.session.add(truck)
                trucks.append(truck)

        except Exception as e:
            logger.warning(f"Could not parse truck data: {e}")
            # Create a default truck based on typical semi-truck specs
            default_truck = self._create_default_truck()
            trucks.append(default_truck)

        self.session.commit()
        logger.info(f"Created {len(trucks)} trucks")
        return trucks

    def ingest_routes_from_price_calculator(self, csv_path: str) -> List[Route]:
        """
        Extract route information from the price calculator CSV.
        - extract route availability and distance data
        - create location entities for route endpoints
        """
        logger.info(f"Ingesting routes from {csv_path}")

        df = pd.read_csv(csv_path, header=None)
        routes = []

        try:
            # Extract pickup and dropoff locations from the top section
            pickup_location = self._extract_location_from_price_csv(df, "Pick Up Point")
            dropoff_location = self._extract_location_from_price_csv(df, "Drop Off Point")

            if pickup_location and dropoff_location:
                # Extract route data from the availability section
                route_data = self._parse_route_availability_section(df)

                for route_info in route_data:
                    route = Route(
                        location_origin_id=pickup_location.id,
                        location_destiny_id=dropoff_location.id,
                        profitability=route_info.get('price', 0.0)
                    )
                    self.session.add(route)
                    routes.append(route)

        except Exception as e:
            logger.warning(f"Could not parse route data: {e}")

        self.session.commit()
        logger.info(f"Created {len(routes)} routes")
        return routes

    def _get_or_create_client(self, client_name: str) -> Client:
        """Get existing client or create new one"""
        client = self.session.query(Client).filter(Client.name == client_name).first()
        if not client:
            client = Client(name=client_name)
            self.session.add(client)
            self.session.flush()
        return client

    def _create_order_from_pair(self, pickup_row: pd.Series, dropoff_row: pd.Series, client_id: int) -> Optional[Order]:
        """
        Create order from pickup/dropoff pair.
        - separate location creation from order creation
        - use existing create_location helper
        - handle missing package data
        """
        try:
            # Create locations
            pickup_loc = create_location(
                self.session,
                lat=pickup_row['Lat'],
                lng=pickup_row['Long']
            )

            dropoff_loc = create_location(
                self.session,
                lat=dropoff_row['Lat'],
                lng=dropoff_row['Long']
            )

            # Create order
            order = Order(
                location_origin_id=pickup_loc.id,
                location_destiny_id=dropoff_loc.id,
                client_id=client_id
            )
            self.session.add(order)
            self.session.flush()

            # Create cargo with packages if quantity is specified
            package_qty = pickup_row.get('Packages qty.', 0)
            if pd.notna(package_qty) and package_qty > 0:
                self._create_cargo_for_order(order.id, int(package_qty))

            return order

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None

    def _create_cargo_for_order(self, order_id: int, package_count: int):
        """
        Create cargo with default packages.
        - make assumptions for standard freight
        - can be updated once real package data is available
        - maintain referential integrity
        """
        cargo = Cargo(order_id=order_id)
        self.session.add(cargo)
        self.session.flush()

        # Create packages with reasonable defaults
        for _ in range(package_count):
            package = Package(
                volume=1.0,  # 1 cubic meter default
                weight=25.0,  # 25 kg default
                type=CargoType.STANDARD,
                cargo_id=cargo.id
            )
            self.session.add(package)

    def _parse_truck_section(self, df: pd.DataFrame) -> Dict:
        """Parse truck information from contract CSV structure"""
        truck_info = {}

        # Look for truck information in the structured data
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]):
                key = str(row.iloc[0]).lower()
                if 'total volume' in key and pd.notna(row.iloc[2]):
                    # Convert cubic feet to cubic meters (1 cubic foot = 0.0283168 cubic meters)
                    volume_cf = float(str(row.iloc[2]).replace(',', ''))
                    truck_info['capacity'] = volume_cf * 0.0283168
                elif 'max weight' in key and pd.notna(row.iloc[2]):
                    # Extract weight info for context (not directly used in capacity calc)
                    weight_lbs = float(str(row.iloc[2]).replace(',', ''))
                    truck_info['max_weight_kg'] = weight_lbs * 0.453592

        return truck_info

    def _create_default_truck(self) -> Truck:
        """Create truck with industry-standard specifications"""
        truck = Truck(
            autonomy=800.0,  # 800km range - typical for long-haul trucks
            capacity=48.0,  # ~48 cubic meters - standard semi-trailer
            type="Standard Semi-Truck"
        )
        self.session.add(truck)
        return truck

    def _extract_location_from_price_csv(self, df: pd.DataFrame, point_type: str) -> Optional[Location]:
        """Extract location data from price calculator CSV"""
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and point_type in str(row.iloc[0]):
                if pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]):
                    try:
                        lat = float(row.iloc[1])
                        lng = float(row.iloc[2])
                        return create_location(self.session, lat=lat, lng=lng)
                    except (ValueError, TypeError):
                        continue
        return None

    def _parse_route_availability_section(self, df: pd.DataFrame) -> List[Dict]:
        """Parse route availability data from the CSV"""
        routes = []

        # Look for route data rows
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).startswith('Route'):
                try:
                    available = str(row.iloc[1]).lower() == 'true'
                    price_str = str(row.iloc[2])
                    price = float(price_str) if price_str != '-' else 0.0

                    routes.append({
                        'available': available,
                        'price': price
                    })
                except (ValueError, TypeError):
                    continue

        return routes


def run_full_ingestion():
    """
    Complete data ingestion workflow.
    - ensure tables exist before inserting data
    - handle dependencies between entities properly
    - logging for debugging
    """
    logger.info("Starting complete data ingestion workflow")

    # Ensure tables exist
    create_tables()

    with Session(engine) as session:
        ingestion_service = DataIngestionService(session)

        try:
            # 1. Ingest orders first (creates locations and basic structure)
            orders = ingestion_service.ingest_orders_from_csv(
                'Eng. Labs 1  Digital Freight Matching 2025  Orders Examples.csv',
                client_name="Initial Client"
            )
            logger.info(f"Ingested {len(orders)} orders")

            # 2. Ingest truck data
            trucks = ingestion_service.ingest_truck_data_from_contract(
                'Eng. Labs 1  Digital Freight Matching 2025  TooBigToFail Contract.csv'
            )
            logger.info(f"Ingested {len(trucks)} trucks")

            # 3. Ingest routes
            routes = ingestion_service.ingest_routes_from_price_calculator(
                'Eng. Labs 1  Digital Freight Matching 2025  Price Order Calculator.csv'
            )
            logger.info(f"Ingested {len(routes)} routes")

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            session.rollback()
            raise

    logger.info("Data ingestion completed successfully")


if __name__ == "__main__":
    run_full_ingestion()
