#!/usr/bin/env python3
"""
Unit tests for DatabaseManager
Tests database operations, initialization, and status checking functionality.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from sqlmodel import Session, create_engine, SQLModel, select

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
)
from db_manager import DatabaseManager, SystemStatus


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class"""
    
    def setUp(self):
        """Set up test database for each test"""
        # Create temporary in-memory database for testing
        self.test_engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(self.test_engine)
        self.session = Session(self.test_engine)
        self.db_manager = DatabaseManager(self.session)
    
    def tearDown(self):
        """Clean up after each test"""
        self.session.close()
    
    def test_check_existing_data_empty_database(self):
        """Test checking data in empty database"""
        existing_data, counts = self.db_manager.check_existing_data()
        
        # Should have all entity types with zero counts
        expected_entities = ['clients', 'locations', 'trucks', 'routes', 'orders', 'cargo', 'packages']
        for entity in expected_entities:
            self.assertIn(entity, counts)
            self.assertEqual(counts[entity], 0)
    
    def test_check_existing_data_with_data(self):
        """Test checking data in populated database"""
        # Add some test data
        client = Client(name="Test Client")
        self.session.add(client)
        
        location = Location(lat=33.7490, lng=-84.3880, marked=True)
        self.session.add(location)
        
        truck = Truck(autonomy=800.0, capacity=48.0, type="Test Truck")
        self.session.add(truck)
        
        self.session.commit()
        
        existing_data, counts = self.db_manager.check_existing_data()
        
        self.assertEqual(counts['clients'], 1)
        self.assertEqual(counts['locations'], 1)
        self.assertEqual(counts['trucks'], 1)
        self.assertEqual(counts['routes'], 0)
    
    def test_is_database_initialized_false(self):
        """Test database initialization check with insufficient data"""
        existing_data, counts = self.db_manager.check_existing_data()
        is_initialized = self.db_manager._is_database_initialized(counts)
        self.assertFalse(is_initialized)
    
    def test_is_database_initialized_true(self):
        """Test database initialization check with sufficient data"""
        # Create minimum required data
        # 1 client
        client = Client(name="Too-Big-To-Fail Company")
        self.session.add(client)
        
        # 6 locations (Atlanta + 5 destinations)
        locations = []
        for i, (city, (lat, lng)) in enumerate([
            ("Atlanta", (33.7490, -84.3880)),
            ("Ringgold", (34.9162, -85.1080)),
            ("Augusta", (33.4735, -82.0105)),
            ("Savannah", (32.0835, -81.0998)),
            ("Albany", (31.5804, -84.1557)),
            ("Columbus", (32.4609, -84.9877))
        ]):
            location = Location(lat=lat, lng=lng, marked=True)
            self.session.add(location)
            locations.append(location)
        
        # 5 trucks
        trucks = []
        for i in range(5):
            truck = Truck(autonomy=800.0, capacity=48.0, type=f"Test Truck #{i+1}")
            self.session.add(truck)
            trucks.append(truck)
        
        self.session.flush()  # Ensure locations have IDs
        
        # 5 routes
        for i in range(5):
            route = Route(
                location_origin_id=locations[0].id,
                location_destiny_id=locations[i+1].id,
                profitability=-50.0,
                truck_id=trucks[i].id
            )
            self.session.add(route)
        
        self.session.commit()
        
        existing_data, counts = self.db_manager.check_existing_data()
        is_initialized = self.db_manager._is_database_initialized(counts)
        self.assertTrue(is_initialized)
    
    def test_find_contract_client_exists(self):
        """Test finding existing contract client"""
        # Create contract client
        client = Client(name="Too-Big-To-Fail Company")
        self.session.add(client)
        self.session.commit()
        
        found_client = self.db_manager._find_contract_client()
        self.assertIsNotNone(found_client)
        self.assertEqual(found_client.name, "Too-Big-To-Fail Company")
        self.assertIn("contract", self.db_manager.clients)
    
    def test_find_contract_client_not_exists(self):
        """Test finding contract client when it doesn't exist"""
        found_client = self.db_manager._find_contract_client()
        self.assertIsNone(found_client)
        self.assertNotIn("contract", self.db_manager.clients)
    
    def test_find_existing_locations(self):
        """Test finding existing locations by coordinates"""
        # Create Atlanta location
        atlanta_lat, atlanta_lng = 33.7490, -84.3880
        location = Location(lat=atlanta_lat, lng=atlanta_lng, marked=True)
        self.session.add(location)
        self.session.commit()
        
        found_locations = self.db_manager._find_existing_locations()
        
        self.assertIn("Atlanta", found_locations)
        self.assertEqual(found_locations["Atlanta"].lat, atlanta_lat)
        self.assertEqual(found_locations["Atlanta"].lng, atlanta_lng)
    
    def test_create_contract_client(self):
        """Test creating contract client"""
        self.db_manager._create_contract_client()
        
        # Check client was created
        client = self.session.exec(select(Client).where(Client.name == "Too-Big-To-Fail Company")).first()
        self.assertIsNotNone(client)
        self.assertIn("contract", self.db_manager.clients)
        self.assertEqual(self.db_manager.clients["contract"].name, "Too-Big-To-Fail Company")
    
    def test_ensure_all_locations(self):
        """Test ensuring all required locations exist"""
        self.db_manager._ensure_all_locations()
        
        # Check all cities were created
        expected_cities = ["Atlanta", "Ringgold", "Augusta", "Savannah", "Albany", "Columbus"]
        for city in expected_cities:
            self.assertIn(city, self.db_manager.locations)
        
        # Verify locations in database
        locations = self.session.exec(select(Location)).all()
        self.assertEqual(len(locations), 6)
    
    def test_ensure_trucks(self):
        """Test ensuring required trucks exist"""
        self.db_manager._ensure_trucks()
        
        # Check trucks were created
        self.assertEqual(len(self.db_manager.trucks), 5)
        
        # Verify trucks in database
        trucks = self.session.exec(select(Truck)).all()
        self.assertEqual(len(trucks), 5)
        
        for i, truck in enumerate(trucks):
            self.assertEqual(truck.type, f"Specialized Contract Truck #{i+1}")
            self.assertEqual(truck.autonomy, 800.0)
            self.assertEqual(truck.capacity, 48.0)
    
    def test_ensure_trucks_with_existing(self):
        """Test ensuring trucks when some already exist"""
        # Create 2 existing trucks
        for i in range(2):
            truck = Truck(
                autonomy=800.0,
                capacity=48.0,
                type=f"Specialized Contract Truck #{i+1}"
            )
            self.session.add(truck)
        self.session.commit()
        
        self.db_manager._ensure_trucks()
        
        # Should have 5 total trucks (2 existing + 3 new)
        trucks = self.session.exec(select(Truck)).all()
        self.assertEqual(len(trucks), 5)
        self.assertEqual(len(self.db_manager.trucks), 5)
    
    def test_verify_integrity_clean_database(self):
        """Test integrity verification on clean database"""
        counts = self.db_manager.verify_integrity()
        
        # Should return counts without errors
        self.assertIsInstance(counts, dict)
        self.assertIn('clients', counts)
    
    def test_verify_integrity_with_orphaned_records(self):
        """Test integrity verification with orphaned records"""
        # Create order with non-existent client
        location = Location(lat=33.7490, lng=-84.3880)
        self.session.add(location)
        self.session.flush()
        
        order = Order(
            location_origin_id=location.id,
            location_destiny_id=location.id,
            client_id=999  # Non-existent client
        )
        self.session.add(order)
        self.session.commit()
        
        # Should not raise exception but log warnings
        with self.assertLogs(level='WARNING') as log:
            counts = self.db_manager.verify_integrity()
            self.assertTrue(any("non-existent client" in message for message in log.output))
    
    def test_get_system_status(self):
        """Test getting comprehensive system status"""
        # Add some test data
        client = Client(name="Test Client")
        self.session.add(client)
        
        location1 = Location(lat=33.7490, lng=-84.3880)
        location2 = Location(lat=34.9162, lng=-85.1080)
        self.session.add_all([location1, location2])
        
        truck = Truck(autonomy=800.0, capacity=100.0, type="Test Truck")
        self.session.add(truck)
        
        self.session.flush()  # Ensure locations have IDs
        
        route = Route(
            location_origin_id=location1.id,
            location_destiny_id=location2.id,
            profitability=-50.0,
            truck_id=truck.id
        )
        self.session.add(route)
        
        # Contract order
        contract_order = Order(
            location_origin_id=location1.id,
            location_destiny_id=location2.id,
            client_id=client.id,
            route_id=route.id,
            contract_type="4-year binding contract"
        )
        self.session.add(contract_order)
        
        # Pending order (no route assigned)
        pending_order = Order(
            location_origin_id=location1.id,
            location_destiny_id=location2.id,
            client_id=client.id
        )
        self.session.add(pending_order)
        
        self.session.flush()  # Ensure orders have IDs
        
        # Add cargo and packages
        cargo = Cargo(order_id=contract_order.id, truck_id=truck.id)
        self.session.add(cargo)
        self.session.flush()
        
        package = Package(volume=10.0, weight=500.0, type=CargoType.STANDARD, cargo_id=cargo.id)
        self.session.add(package)
        
        self.session.commit()
        
        status = self.db_manager.get_system_status()
        
        self.assertIsInstance(status, SystemStatus)
        self.assertEqual(status.clients, 1)
        self.assertEqual(status.total_routes, 1)
        self.assertEqual(status.trucks, 1)
        self.assertEqual(status.orders, 2)
        self.assertEqual(status.active_contracts, 1)
        self.assertEqual(status.pending_orders, 1)
        self.assertEqual(status.daily_profit_loss, -50.0)
        self.assertEqual(status.truck_utilization, 10.0)  # 10/100 * 100
    
    def test_initialize_database_empty(self):
        """Test initializing empty database"""
        success = self.db_manager.initialize_database()
        
        self.assertTrue(success)
        
        # Verify data was created
        existing_data, counts = self.db_manager.check_existing_data()
        self.assertGreaterEqual(counts['clients'], 1)
        self.assertGreaterEqual(counts['locations'], 6)
        self.assertGreaterEqual(counts['trucks'], 5)
        self.assertGreaterEqual(counts['routes'], 5)
    
    def test_initialize_database_already_initialized(self):
        """Test initializing database that's already initialized"""
        # First initialization
        self.db_manager.initialize_database()
        
        # Second initialization should be skipped
        success = self.db_manager.initialize_database()
        self.assertFalse(success)
    
    def test_initialize_database_force_reinit(self):
        """Test force reinitializing database"""
        # First initialization
        self.db_manager.initialize_database()
        
        # Force reinitialize should proceed
        success = self.db_manager.initialize_database(force_reinit=True)
        self.assertTrue(success)
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_reset_database_confirmed(self, mock_remove, mock_exists):
        """Test resetting database with confirmation"""
        mock_exists.return_value = True
        
        success = self.db_manager.reset_database(confirm=True)
        
        self.assertTrue(success)
        mock_remove.assert_called_once_with("logistics.db")
    
    def test_reset_database_not_confirmed(self):
        """Test resetting database without confirmation"""
        success = self.db_manager.reset_database(confirm=False)
        self.assertFalse(success)


class TestSystemStatus(unittest.TestCase):
    """Test cases for SystemStatus class"""
    
    def test_system_status_initialization(self):
        """Test SystemStatus initialization"""
        status = SystemStatus()
        
        self.assertEqual(status.total_routes, 0)
        self.assertEqual(status.daily_profit_loss, 0.0)
        self.assertEqual(status.pending_orders, 0)
        self.assertEqual(status.truck_utilization, 0.0)
        self.assertEqual(status.active_contracts, 0)
        self.assertIsInstance(status.last_updated, type(status.last_updated))


class TestDatabaseManagerIntegration(unittest.TestCase):
    """Integration tests for DatabaseManager"""
    
    def setUp(self):
        """Set up test database for integration tests"""
        self.test_engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(self.test_engine)
        self.session = Session(self.test_engine)
        self.db_manager = DatabaseManager(self.session)
    
    def tearDown(self):
        """Clean up after each test"""
        self.session.close()
    
    def test_full_initialization_workflow(self):
        """Test complete initialization workflow"""
        # Initialize database
        success = self.db_manager.initialize_database()
        self.assertTrue(success)
        
        # Verify integrity
        counts = self.db_manager.verify_integrity()
        self.assertGreaterEqual(counts['clients'], 1)
        
        # Get system status
        status = self.db_manager.get_system_status()
        self.assertIsInstance(status, SystemStatus)
        self.assertGreater(status.total_routes, 0)
        
        # Check that contract client exists
        contract_client = self.db_manager._find_contract_client()
        self.assertIsNotNone(contract_client)
        
        # Verify all locations exist
        self.db_manager._find_existing_locations()
        expected_cities = ["Atlanta", "Ringgold", "Augusta", "Savannah", "Albany", "Columbus"]
        for city in expected_cities:
            self.assertIn(city, self.db_manager.locations)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)