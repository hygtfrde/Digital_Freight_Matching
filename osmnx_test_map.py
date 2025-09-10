#!/usr/bin/env python3
"""
OSMNX Test Map with Hardcoded Database Values

This test file demonstrates:
1. Loading hardcoded location data (simulating database values)
2. Creating a street map using OSMNX
3. Displaying the map with route visualization
4. Closing the map when ESC key is pressed
"""

import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
import random
from schemas.schemas import Location, Route, Truck, Order, Cargo, Package, CargoType

def get_hardcoded_locations():
    """Hardcoded location data simulating database values"""
    locations = {
        'atlanta': Location(id=1, lat=33.7490, lng=-84.3880, marked=True),
        'augusta': Location(id=2, lat=33.4735, lng=-82.0105, marked=True),
        'savannah': Location(id=3, lat=32.0835, lng=-81.0998, marked=True),
        'columbus': Location(id=4, lat=32.4609, lng=-84.9877, marked=True),
        'albany': Location(id=5, lat=31.5804, lng=-84.1557, marked=True),
        'macon': Location(id=6, lat=32.8407, lng=-83.6324, marked=True),
        'ringgold': Location(id=7, lat=34.9161, lng=-85.1094, marked=True),
        
        # Additional pickup/dropoff locations
        'atlanta_north': Location(id=8, lat=33.7600, lng=-84.3900, marked=False),
        'atlanta_warehouse': Location(id=9, lat=33.7400, lng=-84.3800, marked=False),
        'augusta_depot': Location(id=10, lat=33.4800, lng=-82.0000, marked=False),
        'savannah_port': Location(id=11, lat=32.0900, lng=-81.0900, marked=False),
        'macon_center': Location(id=12, lat=32.8500, lng=-83.6400, marked=False),
    }
    return locations

def get_hardcoded_routes():
    """Hardcoded route data simulating database values"""
    locations = get_hardcoded_locations()
    
    routes = [
        {
            'id': 1,
            'name': 'Atlanta-Augusta Express',
            'origin': locations['atlanta'],
            'destination': locations['augusta'],
            'color': 'red',
            'truck_capacity': 48.0,
            'current_load': 32.5,
        },
        {
            'id': 2,
            'name': 'Atlanta-Savannah Coastal',
            'origin': locations['atlanta'],
            'destination': locations['savannah'],
            'color': 'blue',
            'truck_capacity': 36.0,
            'current_load': 18.2,
        },
        {
            'id': 3,
            'name': 'Macon-Columbus Circuit',
            'origin': locations['macon'],
            'destination': locations['columbus'],
            'color': 'green',
            'truck_capacity': 42.0,
            'current_load': 25.8,
        },
        {
            'id': 4,
            'name': 'Ringgold-Albany Long Haul',
            'origin': locations['ringgold'],
            'destination': locations['albany'],
            'color': 'purple',
            'truck_capacity': 52.0,
            'current_load': 41.3,
        }
    ]
    return routes

def get_hardcoded_orders():
    """Hardcoded order data simulating database values"""
    locations = get_hardcoded_locations()
    
    orders = [
        {
            'id': 1,
            'pickup': locations['atlanta_warehouse'],
            'dropoff': locations['augusta_depot'],
            'cargo_volume': 8.5,
            'cargo_type': CargoType.STANDARD,
            'status': 'pending',
        },
        {
            'id': 2,
            'pickup': locations['atlanta_north'],
            'dropoff': locations['savannah_port'],
            'cargo_volume': 12.3,
            'cargo_type': CargoType.REFRIGERATED,
            'status': 'assigned',
        },
        {
            'id': 3,
            'pickup': locations['macon_center'],
            'dropoff': locations['columbus'],
            'cargo_volume': 6.7,
            'cargo_type': CargoType.FRAGILE,
            'status': 'pending',
        },
        {
            'id': 4,
            'pickup': locations['atlanta'],
            'dropoff': locations['augusta'],
            'cargo_volume': 15.2,
            'cargo_type': CargoType.HAZMAT,
            'status': 'in_transit',
        }
    ]
    return orders

def setup_map_display():
    """Setup matplotlib for interactive display with ESC key handler"""
    plt.ion()  # Turn on interactive mode
    
    def on_key_press(event):
        """Handle key press events"""
        if event.key == 'escape':
            print("ESC pressed - closing map...")
            plt.close('all')
            plt.ioff()
    
    return on_key_press

def create_osmnx_map():
    """Create and display OSMNX map with hardcoded data"""
    print("🗺️  Creating OSMNX Map with Hardcoded Data")
    print("=" * 50)
    
    locations = get_hardcoded_locations()
    routes = get_hardcoded_routes()
    orders = get_hardcoded_orders()
    
    # Calculate map bounds
    all_lats = [loc.lat for loc in locations.values()]
    all_lngs = [loc.lng for loc in locations.values()]
    
    north = max(all_lats) + 0.3
    south = min(all_lats) - 0.3
    east = max(all_lngs) + 0.3
    west = min(all_lngs) - 0.3
    
    print(f"Map bounds: {south:.2f}°S to {north:.2f}°N, {west:.2f}°W to {east:.2f}°E")
    
    try:
        # Download road network
        print("Downloading road network...")
        G = ox.graph_from_bbox(north, south, east, west, network_type='drive')
        print(f"Network loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
        
        # Setup interactive display
        key_handler = setup_map_display()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 12))
        fig.canvas.mpl_connect('key_press_event', key_handler)
        
        # Plot road network
        ox.plot_graph(G, ax=ax, node_size=0, edge_linewidth=0.3, 
                     edge_color='lightgray', show=False, close=False)
        
        # Plot major city locations (marked=True)
        major_cities = {name: loc for name, loc in locations.items() if loc.marked}
        for name, location in major_cities.items():
            ax.scatter(location.lng, location.lat, c='red', s=150, 
                      zorder=10, marker='s', edgecolors='darkred', linewidths=2)
            ax.annotate(name.replace('_', ' ').title(), 
                       (location.lng, location.lat),
                       xytext=(8, 8), textcoords='offset points',
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               edgecolor='darkred', alpha=0.9))
        
        # Plot pickup/dropoff locations (marked=False)
        pickup_dropoff = {name: loc for name, loc in locations.items() if not loc.marked}
        for name, location in pickup_dropoff.items():
            ax.scatter(location.lng, location.lat, c='orange', s=80, 
                      zorder=8, marker='o', edgecolors='darkorange', linewidths=1)
            ax.annotate(name.replace('_', ' ').title(), 
                       (location.lng, location.lat),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, style='italic',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='lightyellow', 
                               edgecolor='orange', alpha=0.8))
        
        # Plot routes
        for route in routes:
            origin = route['origin']
            dest = route['destination']
            
            # Draw route line
            ax.plot([origin.lng, dest.lng], [origin.lat, dest.lat],
                   color=route['color'], linewidth=4, alpha=0.7, zorder=5)
            
            # Calculate utilization
            utilization = (route['current_load'] / route['truck_capacity']) * 100
            
            # Add route info
            mid_lng = (origin.lng + dest.lng) / 2
            mid_lat = (origin.lat + dest.lat) / 2
            
            route_text = f"{route['name']}\n{utilization:.1f}% Full"
            ax.annotate(route_text, (mid_lng, mid_lat),
                       fontsize=10, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor=route['color'], alpha=0.3,
                               edgecolor=route['color']))
        
        # Plot orders with different markers based on status
        status_colors = {
            'pending': 'yellow',
            'assigned': 'lightblue', 
            'in_transit': 'lightgreen'
        }
        
        status_markers = {
            'pending': '^',
            'assigned': 'D',
            'in_transit': 'v'
        }
        
        for order in orders:
            pickup = order['pickup']
            dropoff = order['dropoff']
            status = order['status']
            
            # Draw order line
            ax.plot([pickup.lng, dropoff.lng], [pickup.lat, dropoff.lat],
                   color=status_colors[status], linewidth=2, linestyle='--', 
                   alpha=0.6, zorder=3)
            
            # Pickup marker
            ax.scatter(pickup.lng, pickup.lat, 
                      c=status_colors[status], s=100,
                      marker=status_markers[status], 
                      zorder=7, edgecolors='black', linewidths=1)
            
            # Dropoff marker  
            ax.scatter(dropoff.lng, dropoff.lat,
                      c=status_colors[status], s=100,
                      marker=status_markers[status],
                      zorder=7, edgecolors='black', linewidths=1)
        
        # Add proximity circles (1km radius) around major cities
        for name, location in major_cities.items():
            # Convert 1km to degrees (approximate)
            km_to_deg = 1.0 / 111.0  # Rough conversion
            circle = Circle((location.lng, location.lat), km_to_deg,
                           fill=False, color='red', linestyle=':', 
                           alpha=0.5, linewidth=2, zorder=2)
            ax.add_patch(circle)
        
        # Create legend
        legend_elements = [
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='red',
                      markersize=12, label='Major Cities', markeredgecolor='darkred'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
                      markersize=10, label='Pickup/Dropoff Points', markeredgecolor='darkorange'),
            plt.Line2D([0], [0], color='red', linewidth=4, alpha=0.7, label='Active Routes'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='yellow',
                      markersize=10, label='Pending Orders', markeredgecolor='black'),
            plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='lightblue',
                      markersize=10, label='Assigned Orders', markeredgecolor='black'),
            plt.Line2D([0], [0], marker='v', color='w', markerfacecolor='lightgreen',
                      markersize=10, label='In Transit Orders', markeredgecolor='black'),
            plt.Line2D([0], [0], color='red', linestyle=':', alpha=0.5,
                      linewidth=2, label='1km Proximity Zone'),
        ]
        
        ax.legend(handles=legend_elements, loc='upper left', 
                 bbox_to_anchor=(0.02, 0.98), fontsize=10)
        
        # Set title and labels
        ax.set_title('Digital Freight Matching System - Georgia Network\n' +
                    f'Routes: {len(routes)} | Orders: {len(orders)} | ' +
                    f'Locations: {len(locations)}\n' +
                    '🔹 Press ESC to close map', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)
        
        # Add statistics box
        stats_text = f"""Network Statistics:
• Total Locations: {len(locations)}
• Active Routes: {len(routes)}
• Pending Orders: {len([o for o in orders if o['status'] == 'pending'])}
• Routes in Transit: {len([o for o in orders if o['status'] == 'in_transit'])}
• Total Cargo Volume: {sum(o['cargo_volume'] for o in orders):.1f} m³"""
        
        ax.text(0.98, 0.02, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        print("\n✅ Map created successfully!")
        print("📍 Displaying Georgia freight network with:")
        print(f"   • {len(major_cities)} major cities")
        print(f"   • {len(pickup_dropoff)} pickup/dropoff locations")
        print(f"   • {len(routes)} active routes")
        print(f"   • {len(orders)} freight orders")
        print("\n🎮 Controls:")
        print("   • Press ESC to close the map")
        print("   • Use mouse to pan and zoom")
        
        plt.show()
        
        # Keep the plot open until ESC is pressed
        print("\n⏳ Map is open - press ESC in the map window to close...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating map: {e}")
        return False

def main():
    """Main function to run the OSMNX test"""
    print("🚛 DIGITAL FREIGHT MATCHING - OSMNX TEST MAP")
    print("=" * 60)
    
    # Display hardcoded data summary
    locations = get_hardcoded_locations()
    routes = get_hardcoded_routes()
    orders = get_hardcoded_orders()
    
    print(f"\n📊 Hardcoded Test Data:")
    print(f"   Locations: {len(locations)} ({len([l for l in locations.values() if l.marked])} major cities)")
    print(f"   Routes: {len(routes)} active freight routes")
    print(f"   Orders: {len(orders)} freight orders")
    
    # Show route utilization
    print(f"\n🚛 Route Utilization:")
    for route in routes:
        utilization = (route['current_load'] / route['truck_capacity']) * 100
        status = "🔴 High" if utilization > 80 else "🟡 Medium" if utilization > 50 else "🟢 Low"
        print(f"   {route['name']}: {utilization:.1f}% {status}")
    
    # Show order distribution
    order_status_count = {}
    for order in orders:
        status = order['status']
        order_status_count[status] = order_status_count.get(status, 0) + 1
    
    print(f"\n📦 Order Status Distribution:")
    for status, count in order_status_count.items():
        print(f"   {status.title()}: {count} orders")
    
    # Create and display map
    success = create_osmnx_map()
    
    if success:
        print("\n✅ OSMNX Test completed successfully!")
    else:
        print("\n❌ OSMNX Test failed!")

if __name__ == "__main__":
    main()