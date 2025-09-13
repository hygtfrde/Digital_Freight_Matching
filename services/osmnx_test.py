#!/usr/bin/env python3
"""
Modular OSMnx Street Route Display
Shows realistic vehicle routing on street maps like Google Maps.
Displays actual roads, highways, and street-level navigation.
"""

import osmnx as ox
import networkx as nx
import folium
import math
import webbrowser
import tempfile
import os
from typing import Tuple, List, Optional

# Configure OSMnx for better street detail (newer API)
ox.settings.log_console = True
ox.settings.use_cache = True

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the linear (straight-line) distance between two points using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_detailed_vehicle_route(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, List[Tuple[float, float]], int]:
    """
    Calculate detailed vehicle route between two points using OSMnx
    Returns (distance_km, route_coordinates, num_road_segments)
    """
    try:
        # Create bounding box with adequate padding for road network
        padding = 0.02  # ~2km padding for better road coverage
        north = max(lat1, lat2) + padding
        south = min(lat1, lat2) - padding
        east = max(lon1, lon2) + padding
        west = min(lon1, lon2) - padding
        
        print("🚗 Downloading vehicle road network...")
        
        # Download comprehensive driving network - THIS IS KEY FOR STREET DETAIL
        G = ox.graph_from_bbox(
            bbox=(north, south, east, west),
            network_type='drive',    # All driveable roads (highways, arterials, residential)
            simplify=False,          # CRITICAL: Keep all road geometry for realistic routes
            retain_all=True          # Keep all road segments including small streets
        )
        
        print(f"🛣️  Road network: {len(G.nodes):,} intersections, {len(G.edges):,} road segments")
        
        # Find nearest road intersections to our points
        start_node = ox.distance.nearest_nodes(G, lon1, lat1)
        end_node = ox.distance.nearest_nodes(G, lon2, lat2)
        
        print(f"📍 Nearest intersections found - Start: {start_node}, End: {end_node}")
        
        # Calculate shortest path using actual road distances
        route_nodes = nx.shortest_path(G, start_node, end_node, weight='length')
        
        print(f"🗺️  Vehicle route calculated: {len(route_nodes)} road intersections")
        
        # Extract coordinates for each intersection along the route
        route_coordinates = []
        for node in route_nodes:
            lat = G.nodes[node]['y']  # latitude
            lon = G.nodes[node]['x']  # longitude
            route_coordinates.append((lat, lon))
        
        # Calculate total driving distance using road lengths
        total_distance_m = sum(G[route_nodes[i]][route_nodes[i+1]][0]['length'] 
                             for i in range(len(route_nodes)-1))
        
        distance_km = total_distance_m / 1000
        
        print(f"✅ Vehicle route complete:")
        print(f"   Distance: {distance_km:.2f} km")
        print(f"   Route points: {len(route_coordinates)} (following actual streets)")
        
        return distance_km, route_coordinates, len(route_nodes)
        
    except Exception as e:
        print(f"❌ Vehicle routing failed: {e}")
        print("   This might be due to disconnected road networks or remote areas")
        return None, None, 0

def create_vehicle_route_map(lat1: float, lon1: float, lat2: float, lon2: float, 
                           route_coords: Optional[List[Tuple[float, float]]] = None, 
                           road_dist: Optional[float] = None, 
                           linear_dist: Optional[float] = None,
                           route_points: int = 0) -> str:
    """
    Create an interactive map showing detailed vehicle routing like Google Maps
    Returns the filename of the saved map
    """
    # Center map between the two points  
    center_lat = (lat1 + lat2) / 2
    center_lon = (lon1 + lon2) / 2
    
    # Calculate appropriate zoom level based on distance
    if linear_dist:
        if linear_dist > 100:
            zoom = 8
        elif linear_dist > 50:
            zoom = 9
        elif linear_dist > 20:
            zoom = 10
        elif linear_dist > 10:
            zoom = 11
        elif linear_dist > 5:
            zoom = 12
        else:
            zoom = 13
    else:
        zoom = 12
    
    # Create map with street-focused tiles
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=zoom,
        tiles='OpenStreetMap'  # Shows street names and details
    )
    
    # Add title with route info
    title_html = f'''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                background-color: rgba(255,255,255,0.95); padding: 15px; border-radius: 8px;
                border: 3px solid #1e90ff; z-index: 9999; text-align: center;">
        <h3 style="margin: 0; color: #1e90ff;">🚗 Vehicle Route - Like Google Maps</h3>
        <p style="margin: 5px 0 0 0; font-size: 14px;">
            {f"Distance: {road_dist:.2f} km • " if road_dist else ""}
            {f"Route Points: {route_points} • " if route_points else ""}
            Press ESC to close
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add start marker (green with car icon)
    folium.Marker(
        location=[lat1, lon1],
        popup=f"<b>🚗 Route Start</b><br>Lat: {lat1:.6f}<br>Lon: {lon1:.6f}",
        tooltip="Start - Vehicle Route",
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)
    
    # Add end marker (red with destination icon)  
    folium.Marker(
        location=[lat2, lon2],
        popup=f"<b>🏁 Route End</b><br>Lat: {lat2:.6f}<br>Lon: {lon2:.6f}",
        tooltip="End - Vehicle Route",
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(m)
    
    # Add straight line for comparison (thin, dashed)
    if linear_dist:
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color='gray',
            weight=2,
            opacity=0.5,
            dash_array='5, 5',
            popup=f"Direct Distance: {linear_dist:.2f} km",
            tooltip="Direct line (as the crow flies)"
        ).add_to(m)
    
    # Add detailed vehicle route (thick, blue like Google Maps)
    if route_coords and len(route_coords) > 1:
        # Convert to format folium expects
        folium_coords = [[lat, lon] for lat, lon in route_coords]
        
        folium.PolyLine(
            locations=folium_coords,
            color='#1e90ff',  # Google Maps blue
            weight=5,         # Thick line like navigation apps
            opacity=0.9,
            popup=f"<b>Vehicle Route</b><br>Distance: {road_dist:.2f} km<br>Follows actual roads<br>Points: {len(route_coords)}",
            tooltip=f"Vehicle Route: {road_dist:.2f} km"
        ).add_to(m)
        
        print(f"📍 Route added to map: {len(route_coords)} coordinate points following streets")
    else:
        print("⚠️  No detailed route available - check if routing succeeded")
    
    # Add comprehensive info panel
    if road_dist and linear_dist:
        difference = road_dist - linear_dist
        ratio = road_dist / linear_dist
        efficiency = (linear_dist / road_dist) * 100
        
        info_html = f'''
        <div style="position: fixed; top: 80px; right: 10px; width: 280px;
                    background-color: rgba(255,255,255,0.95); padding: 15px; border-radius: 8px;
                    border: 2px solid #1e90ff; z-index: 9999; font-family: Arial;">
            <h4 style="margin: 0 0 10px 0; color: #1e90ff;">📊 Route Analysis</h4>
            <table style="width: 100%; font-size: 13px;">
                <tr><td><b>🛣️ Vehicle Route:</b></td><td>{road_dist:.2f} km</td></tr>
                <tr><td><b>📏 Direct Distance:</b></td><td>{linear_dist:.2f} km</td></tr>
                <tr><td><b>➕ Extra Distance:</b></td><td>+{difference:.2f} km</td></tr>
                <tr><td><b>📈 Route Factor:</b></td><td>{ratio:.2f}x</td></tr>
                <tr><td><b>⚡ Route Efficiency:</b></td><td>{efficiency:.1f}%</td></tr>
                <tr><td><b>🗺️ Route Points:</b></td><td>{route_points:,}</td></tr>
            </table>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0; font-size: 12px;">
                <b>🎮 Map Controls:</b><br>
                • Zoom in to see street names<br>
                • Click route for details<br>
                • <b>Press ESC to close</b>
            </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(info_html))
    
    # Add ESC key functionality
    esc_script = '''
    <script>
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            alert('Closing vehicle route map...');
            window.close();
        }
    });
    </script>
    '''
    m.get_root().html.add_child(folium.Element(esc_script))
    
    # Save to temporary file that auto-opens
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    m.save(temp_file.name)
    temp_file.close()
    
    return temp_file.name

def show_vehicle_route(lat1: float, lon1: float, lat2: float, lon2: float, 
                      start_name: str = "Start", end_name: str = "End",
                      auto_open: bool = True):
    """
    Main function to calculate and display vehicle route like Google Maps
    """
    print(f"\n{'='*60}")
    print("🚗 VEHICLE ROUTE CALCULATOR - Like Google Maps")
    print(f"{'='*60}")
    print(f"📍 Start: {start_name} ({lat1:.6f}, {lon1:.6f})")
    print(f"🏁 End: {end_name} ({lat2:.6f}, {lon2:.6f})")
    print()
    
    # Calculate linear distance first
    print("📏 Calculating direct distance...")
    linear_dist = haversine_distance(lat1, lon1, lat2, lon2)
    linear_miles = linear_dist * 0.621371
    print(f"   Direct distance: {linear_dist:.2f} km ({linear_miles:.2f} miles)")
    
    # Calculate detailed vehicle route
    print("\n🚗 Calculating vehicle route (street-level)...")
    road_dist, route_coords, route_points = get_detailed_vehicle_route(lat1, lon1, lat2, lon2)
    
    if road_dist and route_coords:
        road_miles = road_dist * 0.621371
        difference = road_dist - linear_dist
        ratio = road_dist / linear_dist
        efficiency = (linear_dist / road_dist) * 100
        
        print(f"\n✅ VEHICLE ROUTE CALCULATED:")
        print(f"   🛣️  Vehicle distance: {road_dist:.2f} km ({road_miles:.2f} miles)")
        print(f"   ➕ Extra distance: +{difference:.2f} km (+{difference * 0.621371:.2f} miles)")
        print(f"   📈 Route factor: {ratio:.2f}x longer than direct")
        print(f"   ⚡ Route efficiency: {efficiency:.1f}%")
        print(f"   🗺️  Route points: {route_points:,} road intersections")
        
        # Create interactive map
        print(f"\n🎨 Creating interactive vehicle route map...")
        map_file = create_vehicle_route_map(
            lat1, lon1, lat2, lon2, 
            route_coords, road_dist, linear_dist, route_points
        )
        
        if auto_open:
            print(f"🌐 Opening vehicle route in browser...")
            print(f"   💡 Zoom in to see street names and road details")
            print(f"   🎮 Press ESC in browser to close the map")
            webbrowser.open('file://' + map_file)
            
            try:
                input(f"\n⏳ Map is open. Press Enter to clean up and exit...")
                os.unlink(map_file)
                print("🧹 Temporary files cleaned up")
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
        else:
            print(f"📁 Map saved as: {map_file}")
        
    else:
        print(f"\n❌ VEHICLE ROUTING FAILED")
        print(f"   This might happen if:")
        print(f"   • Locations are in remote areas without road networks")
        print(f"   • Points are on islands or disconnected road systems")
        print(f"   • OSMnx data is unavailable for this region")
        print(f"\n🔄 Creating basic comparison map...")
        
        # Create basic map even if routing failed
        map_file = create_vehicle_route_map(
            lat1, lon1, lat2, lon2, 
            None, None, linear_dist, 0
        )
        
        if auto_open:
            webbrowser.open('file://' + map_file)
    
    print(f"\n{'='*60}")
    print("🎯 Vehicle route analysis complete!")
    print(f"{'='*60}")


def quick_demo():
    """Run a quick demo with good test locations"""
    print("🚀 Quick Vehicle Route Demo")
    print("=" * 40)
    
    # Good test locations that definitely have detailed street networks
    demo_routes = [
        {
            "name": "San Francisco Bay Area",
            "start": (37.7749, -122.4194, "San Francisco"),
            "end": (37.8044, -122.2712, "Oakland"),
            "description": "Urban route with bridges and highways"
        },
        {
            "name": "Atlanta Metro", 
            "start": (33.7490, -84.3880, "Downtown Atlanta"),
            "end": (33.7756, -84.3963, "Georgia Tech"),
            "description": "City streets and campus routing"
        },
        {
            "name": "Your Original Route",
            "start": (33.754413815792205, -84.3875298776525, "Atlanta"),
            "end": (34.87433823445323, -85.084123334995166, "Ringgold"),
            "description": "Interstate highway routing"
        }
    ]
    
    print("Choose a demo route:")
    for i, route in enumerate(demo_routes, 1):
        print(f"  {i}. {route['name']} - {route['description']}")
    
    try:
        choice = int(input("\nSelect route (1-3): ")) - 1
        if 0 <= choice < len(demo_routes):
            route = demo_routes[choice]
            start_lat, start_lon, start_name = route["start"]
            end_lat, end_lon, end_name = route["end"]
            
            show_vehicle_route(
                start_lat, start_lon, end_lat, end_lon,
                start_name, end_name
            )
        else:
            print("Invalid choice, using default route...")
            show_vehicle_route(37.7749, -122.4194, 37.8044, -122.2712, "San Francisco", "Oakland")
            
    except (ValueError, KeyboardInterrupt):
        print("Using default route...")
        show_vehicle_route(37.7749, -122.4194, 37.8044, -122.2712, "San Francisco", "Oakland")


def main():
    """
    Main function - shows vehicle routing demo
    """
    try:
        quick_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure you have: pip install folium osmnx networkx")

if __name__ == "__main__":
    # Run the main demo
    main()
    
    # For direct testing, you can also call:
    # show_vehicle_route(lat1, lon1, lat2, lon2, "Start Name", "End Name")