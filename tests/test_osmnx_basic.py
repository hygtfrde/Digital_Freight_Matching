#!/usr/bin/env python3
"""
Standalone OSMnx Test Module
Simple tool to compare road distance vs linear distance between two points
and visualize the route on a map.
"""

import osmnx as ox
import networkx as nx
import folium
import math
from typing import Tuple

# Configure OSMnx with new settings for logging and caching
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

def get_road_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, list]:
    """
    Calculate road distance between two points using OSMnx
    Returns (distance_km, route_nodes)
    """
    try:
        # Create bounding box with padding
        padding = 0.01  # ~1km padding
        north = max(lat1, lat2) + padding
        south = min(lat1, lat2) - padding
        east = max(lon1, lon2) + padding
        west = min(lon1, lon2) - padding
        
        print("Downloading road network...")
        
        # Download road network
        G = ox.graph_from_bbox(
            north, south, east, west,
            network_type='drive'
        )
        
        print(f"Network downloaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
        
        # Find nearest nodes to our points
        start_node = ox.nearest_nodes(G, lon1, lat1)
        end_node = ox.nearest_nodes(G, lon2, lat2)
        
        print(f"Start node: {start_node}, End node: {end_node}")
        
        # Calculate shortest path
        route = nx.shortest_path(G, start_node, end_node, weight='length')
        
        # Calculate total distance
        total_distance_m = sum(G[route[i]][route[i+1]][0]['length'] 
                             for i in range(len(route)-1))
        
        distance_km = total_distance_m / 1000
        
        return distance_km, route, G
        
    except Exception as e:
        print(f"Error calculating road distance: {e}")
        return None, None, None

def create_route_map(lat1: float, lon1: float, lat2: float, lon2: float, 
                    route=None, G=None, road_dist=None, linear_dist=None) -> str:
    """
    Create an interactive map showing the route between two points
    Returns the filename of the saved map
    """
    # Center map between the two points
    center_lat = (lat1 + lat2) / 2
    center_lon = (lon1 + lon2) / 2
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Add start marker (green)
    folium.Marker(
        location=[lat1, lon1],
        popup=f"Start<br>Lat: {lat1:.6f}<br>Lon: {lon1:.6f}",
        tooltip="Start Point",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    # Add end marker (red)
    folium.Marker(
        location=[lat2, lon2],
        popup=f"End<br>Lat: {lat2:.6f}<br>Lon: {lon2:.6f}",
        tooltip="End Point",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)
    
    # Add straight line (linear distance)
    folium.PolyLine(
        locations=[[lat1, lon1], [lat2, lon2]],
        color='blue',
        weight=2,
        opacity=0.7,
        popup=f"Linear Distance: {linear_dist:.2f} km" if linear_dist else "Linear Distance"
    ).add_to(m)
    
    # Add road route if available
    if route and G:
        try:
            # Get coordinates for each node in the route
            route_coords = []
            for node in route:
                lat = G.nodes[node]['y']
                lon = G.nodes[node]['x']
                route_coords.append([lat, lon])
            
            # Add road route
            folium.PolyLine(
                locations=route_coords,
                color='red',
                weight=4,
                opacity=0.8,
                popup=f"Road Distance: {road_dist:.2f} km" if road_dist else "Road Route"
            ).add_to(m)
            
        except Exception as e:
            print(f"Could not add road route to map: {e}")
    
    # Add distance comparison as a text box
    if road_dist and linear_dist:
        difference = road_dist - linear_dist
        ratio = road_dist / linear_dist
        
        html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 200px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Distance Comparison</b><br>
        Linear: {linear_dist:.2f} km<br>
        Road: {road_dist:.2f} km<br>
        Difference: +{difference:.2f} km<br>
        Ratio: {ratio:.2f}x
        </div>
        """
        m.get_root().html.add_child(folium.Element(html))
    
    # Save map
    filename = "route_map.html"
    m.save(filename)
    return filename

def _test_route(lat1: float, lon1: float, lat2: float, lon2: float):
    """
    Main function to test route between two points
    """
    print(f"\n{'='*50}")
    print("OSMnx Route Distance Test")
    print(f"{'='*50}")
    print(f"Start: {lat1:.6f}, {lon1:.6f}")
    print(f"End: {lat2:.6f}, {lon2:.6f}")
    print()
    
    # Calculate linear distance
    print("Calculating linear distance...")
    linear_dist = haversine_distance(lat1, lon1, lat2, lon2)
    linear_miles = linear_dist * 0.621371
    print(f"Linear distance: {linear_dist:.2f} km ({linear_miles:.2f} miles)")
    
    # Calculate road distance
    print("\nCalculating road distance...")
    road_dist, route, G = get_road_distance(lat1, lon1, lat2, lon2)
    
    if road_dist:
        road_miles = road_dist * 0.621371
        difference = road_dist - linear_dist
        ratio = road_dist / linear_dist
        
        print(f"Road distance: {road_dist:.2f} km ({road_miles:.2f} miles)")
        print(f"Difference: +{difference:.2f} km (+{difference * 0.621371:.2f} miles)")
        print(f"Road/Linear ratio: {ratio:.2f}x")
    else:
        print("Could not calculate road distance")
        route, G = None, None
    
    # Create map
    print("\nCreating route map...")
    map_file = create_route_map(lat1, lon1, lat2, lon2, route, G, road_dist, linear_dist)
    print(f"Map saved as: {map_file}")
    
    print(f"\n{'='*50}")
    print("Test complete! Open route_map.html to view the route.")
    print(f"{'='*50}")

def main():
    """
    Main function with example usage
    """
    print("Standalone OSMnx Route Distance Calculator")
    print("Usage examples:")
    
    # Example 1: Atlanta to Ringgold (from your freight data)
    print("\nExample 1: Atlanta to Ringgold, GA")
    _test_route(
        lat1=33.754413815792205, lon1=-84.3875298776525,  # Atlanta
        lat2=34.87433823445323, lon2=-85.084123334995166   # Ringgold
    )
    
    # You can test other routes by calling _test_route with different coordinates
    # Example 2: Shorter route within Atlanta
    # print("\nExample 2: Short route within Atlanta")
    # _test_route(
    #     lat1=33.7490, lon1=-84.3880,  # Downtown Atlanta
    #     lat2=33.7756, lon2=-84.3963   # Georgia Tech
    # )

if __name__ == "__main__":
    # For interactive use, you can also call _test_route directly:
    # _test_route(lat1, lon1, lat2, lon2)
    
    main()