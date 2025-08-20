#!/usr/bin/env python3
"""
Simple database initialization script that creates the contract data directly.
Run this after installing: pip install sqlmodel pandas
"""

import pandas as pd
from io import StringIO
import sqlite3
import os

# Contract data from Too-Big-To-Fail company
contract_data = """route,anchor_point,cargo_miles,total_miles,truck_cost,pallets,cargo_cost,empty_cargo_cost,markup,price_time,price_cargo,margin,stop_count,hours
1,Ringgold,101,202,342.16,20,257.62404,84.53,.50,513.24,386.4360543,.1294,2,4.0
2,Augusta,94.6,189.2,320.48,21,253.364312,67.11,.5,480.71,380.0464681,.1859,2,3.8
3,Savannah,248,496,840.15,22,695.839971,144.31,.50,1260.22,1043.759957,.2424,2,9.9
4,Albany,182,364,616.56,17,394.5984,221.96,.50,924.84,591.8976,-.040,2,7.3
5,Columbus,107,214,362.48,18,245.635591,116.85,.50,543.72,368.4533864,.0165,2,4.3"""

# Georgia city coordinates
CITY_COORDINATES = {
    "Atlanta": (33.7490, -84.3880),
    "Ringgold": (34.9162, -85.1080),
    "Augusta": (33.4735, -82.0105),
    "Savannah": (32.0835, -81.0998),
    "Albany": (31.5804, -84.1557),
    "Columbus": (32.4609, -84.9877)
}

def create_database():
    """Create SQLite database with contract data"""
    
    # Remove existing database
    if os.path.exists("logistics.db"):
        os.remove("logistics.db")
    
    # Connect to database
    conn = sqlite3.connect("logistics.db")
    cursor = conn.cursor()
    
    print("🗄️  Creating database tables...")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE location (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            marked BOOLEAN DEFAULT FALSE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE client (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE truck (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autonomy REAL NOT NULL,
            capacity REAL NOT NULL,
            type TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE route (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_origin_id INTEGER NOT NULL,
            location_destiny_id INTEGER NOT NULL,
            profitability REAL DEFAULT 0.0,
            truck_id INTEGER,
            FOREIGN KEY (location_origin_id) REFERENCES location (id),
            FOREIGN KEY (location_destiny_id) REFERENCES location (id),
            FOREIGN KEY (truck_id) REFERENCES truck (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE "order" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_origin_id INTEGER NOT NULL,
            location_destiny_id INTEGER NOT NULL,
            client_id INTEGER,
            route_id INTEGER,
            contract_type TEXT,
            FOREIGN KEY (location_origin_id) REFERENCES location (id),
            FOREIGN KEY (location_destiny_id) REFERENCES location (id),
            FOREIGN KEY (client_id) REFERENCES client (id),
            FOREIGN KEY (route_id) REFERENCES route (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE cargo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            truck_id INTEGER,
            FOREIGN KEY (order_id) REFERENCES "order" (id),
            FOREIGN KEY (truck_id) REFERENCES truck (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE package (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volume REAL NOT NULL,
            weight REAL NOT NULL,
            type TEXT DEFAULT 'standard',
            cargo_id INTEGER,
            FOREIGN KEY (cargo_id) REFERENCES cargo (id)
        )
    """)
    
    print("✅ Tables created successfully!")
    
    # Insert contract client
    cursor.execute("INSERT INTO client (name) VALUES (?)", ("Too-Big-To-Fail Company",))
    client_id = cursor.lastrowid
    print(f"📋 Created client: Too-Big-To-Fail Company (ID: {client_id})")
    
    # Insert locations
    atlanta_lat, atlanta_lng = CITY_COORDINATES["Atlanta"]
    cursor.execute("INSERT INTO location (lat, lng, marked) VALUES (?, ?, ?)", 
                   (atlanta_lat, atlanta_lng, True))
    atlanta_id = cursor.lastrowid
    print(f"📍 Created Atlanta origin: ({atlanta_lat}, {atlanta_lng})")
    
    destination_ids = {}
    for city, (lat, lng) in CITY_COORDINATES.items():
        if city != "Atlanta":
            cursor.execute("INSERT INTO location (lat, lng, marked) VALUES (?, ?, ?)", 
                          (lat, lng, True))
            destination_ids[city] = cursor.lastrowid
            print(f"📍 Created {city}: ({lat}, {lng})")
    
    # Insert trucks
    truck_ids = []
    for i in range(1, 6):
        cursor.execute("""
            INSERT INTO truck (autonomy, capacity, type) 
            VALUES (?, ?, ?)
        """, (800.0, 48.0, f"Specialized Contract Truck #{i}"))
        truck_ids.append(cursor.lastrowid)
        print(f"🚛 Created Truck #{i}")
    
    # Parse contract data and create routes
    df = pd.read_csv(StringIO(contract_data))
    
    # Daily losses from business requirements
    daily_losses = {
        1: -53.51,   # Ringgold
        2: -50.12,   # Augusta  
        3: -131.40,  # Savannah
        4: -96.43,   # Albany
        5: -56.69    # Columbus
    }
    
    route_ids = []
    total_loss = 0
    
    for idx, row in df.iterrows():
        route_num = int(row['route'])
        anchor_point = row['anchor_point']
        total_miles = row['total_miles']
        hours = row['hours']
        pallets = int(row['pallets'])
        
        destination_id = destination_ids.get(anchor_point)
        if not destination_id:
            print(f"⚠️  Destination {anchor_point} not found, skipping route {route_num}")
            continue
        
        current_profitability = daily_losses.get(route_num, 0.0)
        total_loss += current_profitability
        truck_id = truck_ids[idx] if idx < len(truck_ids) else None
        
        # Create route
        cursor.execute("""
            INSERT INTO route (location_origin_id, location_destiny_id, profitability, truck_id)
            VALUES (?, ?, ?, ?)
        """, (atlanta_id, destination_id, current_profitability, truck_id))
        route_id = cursor.lastrowid
        route_ids.append(route_id)
        
        print(f"🛣️  Created route {route_num}: Atlanta → {anchor_point} "
              f"({total_miles} miles, {hours}hrs, ${current_profitability:.2f}/day)")
        
        # Create contract order for this route
        cursor.execute("""
            INSERT INTO "order" (location_origin_id, location_destiny_id, client_id, route_id, contract_type)
            VALUES (?, ?, ?, ?, ?)
        """, (atlanta_id, destination_id, client_id, route_id, "4-year binding contract"))
        order_id = cursor.lastrowid
        
        # Create cargo for the order
        cursor.execute("""
            INSERT INTO cargo (order_id, truck_id)
            VALUES (?, ?)
        """, (order_id, truck_id))
        cargo_id = cursor.lastrowid
        
        # Create packages (pallets)
        for pallet_num in range(pallets):
            cursor.execute("""
                INSERT INTO package (volume, weight, type, cargo_id)
                VALUES (?, ?, ?, ?)
            """, (1.0, 500.0, "standard", cargo_id))
        
        print(f"📦 Created contract order with {pallets} pallets")
    
    print(f"\n💰 Total daily loss: ${total_loss:.2f}")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("\n✅ Database initialization completed successfully!")
    print("Database file: logistics.db")
    print("\nNext steps:")
    print("1. Install dependencies: pip install sqlmodel pandas fastapi")
    print("2. Run your DFM application")
    print("3. Use the DataIngestionService to add new orders")

def verify_data():
    """Quick verification of the created data"""
    if not os.path.exists("logistics.db"):
        print("❌ Database not found. Run create_database() first.")
        return
    
    conn = sqlite3.connect("logistics.db")
    cursor = conn.cursor()
    
    # Count records
    tables = ['client', 'location', 'truck', 'route', 'order', 'cargo', 'package']
    
    print("\n📊 Database Summary:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")
    
    # Show routes with profitability
    cursor.execute("""
        SELECT r.id, r.profitability, l1.lat as orig_lat, l1.lng as orig_lng, 
               l2.lat as dest_lat, l2.lng as dest_lng
        FROM route r
        JOIN location l1 ON r.location_origin_id = l1.id
        JOIN location l2 ON r.location_destiny_id = l2.id
    """)
    
    routes = cursor.fetchall()
    print(f"\n🛣️  Routes ({len(routes)}):")
    for route_id, profit, orig_lat, orig_lng, dest_lat, dest_lng in routes:
        print(f"  Route {route_id}: ${profit:.2f}/day")
    
    conn.close()

if __name__ == "__main__":
    create_database()
    verify_data()