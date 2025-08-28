"""
Route Calculation Service for OSMnx Integration.

This module provides route calculation capabilities using OSMnx for actual
road distances and drive times, with fallback to Haversine calculations.
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import threading

# OSMnx imports (will be imported when needed to handle optional dependency)
try:
    import osmnx as ox
    import networkx as nx
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False
    logging.warning("OSMnx not available. Route calculations will use fallback methods.")

# Configure logging for this module
logger = logging.getLogger(__name__)


# ============= COORDINATE VALIDATION AND ERROR HANDLING UTILITIES =============

class CoordinateValidationError(ValueError):
    """Exception raised for invalid coordinate values."""
    pass


class RouteCalculationError(Exception):
    """Exception raised for route calculation failures."""
    pass


def validate_coordinates(lat: float, lng: float, location_name: str = "location") -> None:
    """
    Validate latitude and longitude coordinates.
    
    Args:
        lat: Latitude value
        lng: Longitude value  
        location_name: Name for error messages
        
    Raises:
        CoordinateValidationError: If coordinates are invalid
    """
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        raise CoordinateValidationError(
            f"Coordinates must be numeric for {location_name}: lat={lat}, lng={lng}"
        )
    
    # Check for NaN first (NaN comparisons always return False)
    if math.isnan(lat) or math.isnan(lng):
        raise CoordinateValidationError(
            f"Coordinates cannot be NaN for {location_name}: lat={lat}, lng={lng}"
        )
    
    # Check for infinity
    if math.isinf(lat) or math.isinf(lng):
        raise CoordinateValidationError(
            f"Coordinates cannot be infinite for {location_name}: lat={lat}, lng={lng}"
        )
    
    # Check valid ranges
    if not (-90 <= lat <= 90):
        raise CoordinateValidationError(
            f"Latitude must be between -90 and 90 for {location_name}: {lat}"
        )
    
    if not (-180 <= lng <= 180):
        raise CoordinateValidationError(
            f"Longitude must be between -180 and 180 for {location_name}: {lng}"
        )


def validate_location_object(location, location_name: str = "location") -> None:
    """
    Validate a location object has required attributes and valid coordinates.
    
    Args:
        location: Location object to validate
        location_name: Name for error messages
        
    Raises:
        CoordinateValidationError: If location is invalid
    """
    if location is None:
        raise CoordinateValidationError(f"{location_name} cannot be None")
    
    if not hasattr(location, 'lat') or not hasattr(location, 'lng'):
        raise CoordinateValidationError(
            f"{location_name} must have 'lat' and 'lng' attributes: {location}"
        )
    
    validate_coordinates(location.lat, location.lng, location_name)


def validate_location_list(locations: List, min_locations: int = 1) -> None:
    """
    Validate a list of location objects.
    
    Args:
        locations: List of location objects
        min_locations: Minimum number of locations required
        
    Raises:
        CoordinateValidationError: If location list is invalid
    """
    if not locations:
        raise CoordinateValidationError("Location list cannot be empty")
    
    if len(locations) < min_locations:
        raise CoordinateValidationError(
            f"At least {min_locations} locations required, got {len(locations)}"
        )
    
    for i, location in enumerate(locations):
        validate_location_object(location, f"location[{i}]")


def safe_distance_calculation(calc_func, *args, fallback_value: float = 0.0, 
                            operation_name: str = "distance calculation") -> float:
    """
    Safely execute a distance calculation with error handling.
    
    Args:
        calc_func: Function to execute
        *args: Arguments for the function
        fallback_value: Value to return on error
        operation_name: Name of operation for logging
        
    Returns:
        Calculated distance or fallback value
    """
    try:
        result = calc_func(*args)
        if isinstance(result, (int, float)) and result >= 0:
            return float(result)
        else:
            logger.warning(f"{operation_name} returned invalid result: {result}")
            return fallback_value
    except Exception as e:
        logger.error(f"Error in {operation_name}: {e}")
        return fallback_value


def create_error_result(error_message: str, calculation_method: str = "error") -> "DistanceResult":
    """
    Create a DistanceResult indicating an error occurred.
    
    Args:
        error_message: Description of the error
        calculation_method: Method that failed
        
    Returns:
        DistanceResult with error information
    """
    return DistanceResult(
        distance_km=0.0,
        calculation_method=calculation_method,
        error=error_message
    )


def create_error_route_result(error_message: str, calculation_method: str = "error") -> "RouteResult":
    """
    Create a RouteResult indicating an error occurred.
    
    Args:
        error_message: Description of the error
        calculation_method: Method that failed
        
    Returns:
        RouteResult with error information
    """
    return RouteResult(
        total_distance_km=0.0,
        total_time_hours=0.0,
        waypoint_distances=[],
        calculation_method=calculation_method,
        network_available=False,
        error=error_message
    )


@dataclass
class DistanceResult:
    """Result of a distance calculation between two locations."""
    distance_km: float
    calculation_method: str  # "osmnx" or "haversine"
    drive_time_hours: Optional[float] = None
    route_nodes: Optional[List] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validate distance result data."""
        if self.distance_km < 0:
            raise ValueError(f"Distance cannot be negative: {self.distance_km}")
        
        if self.calculation_method not in ["osmnx", "haversine", "cached", "placeholder", "error"]:
            raise ValueError(f"Invalid calculation method: {self.calculation_method}")
        
        if self.drive_time_hours is not None and self.drive_time_hours < 0:
            raise ValueError(f"Drive time cannot be negative: {self.drive_time_hours}")
    
    @property
    def is_successful(self) -> bool:
        """Check if calculation was successful (no error)."""
        return self.error is None
    
    @property
    def used_road_network(self) -> bool:
        """Check if result used actual road network data."""
        return self.calculation_method in ["osmnx", "cached"]
    
    def get_speed_kmh(self) -> Optional[float]:
        """Calculate average speed if both distance and time are available."""
        if self.drive_time_hours and self.drive_time_hours > 0:
            return self.distance_km / self.drive_time_hours
        return None
    
    def __str__(self) -> str:
        """String representation of distance result."""
        if self.error:
            return f"DistanceResult(ERROR: {self.error})"
        
        time_str = f", {self.drive_time_hours:.2f}h" if self.drive_time_hours else ""
        return f"DistanceResult({self.distance_km:.2f}km{time_str}, method={self.calculation_method})"


@dataclass
class RouteResult:
    """Result of a multi-waypoint route calculation."""
    total_distance_km: float
    total_time_hours: float
    waypoint_distances: List[float]
    calculation_method: str
    network_available: bool
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validate route result data."""
        if self.total_distance_km < 0:
            raise ValueError(f"Total distance cannot be negative: {self.total_distance_km}")
        
        if self.total_time_hours < 0:
            raise ValueError(f"Total time cannot be negative: {self.total_time_hours}")
        
        if any(d < 0 for d in self.waypoint_distances):
            raise ValueError("Waypoint distances cannot be negative")
        
        if self.calculation_method not in ["osmnx", "haversine", "cached", "mixed", "placeholder", "error"]:
            raise ValueError(f"Invalid calculation method: {self.calculation_method}")
    
    @property
    def is_successful(self) -> bool:
        """Check if calculation was successful (no error)."""
        return self.error is None
    
    @property
    def used_road_network(self) -> bool:
        """Check if result used actual road network data."""
        return self.calculation_method in ["osmnx", "cached", "mixed"]
    
    @property
    def num_waypoints(self) -> int:
        """Get number of waypoints in the route."""
        return len(self.waypoint_distances) + 1 if self.waypoint_distances else 0
    
    def get_average_speed_kmh(self) -> Optional[float]:
        """Calculate average speed for the entire route."""
        if self.total_time_hours > 0:
            return self.total_distance_km / self.total_time_hours
        return None
    
    def get_longest_segment_km(self) -> float:
        """Get the distance of the longest segment in the route."""
        return max(self.waypoint_distances) if self.waypoint_distances else 0.0
    
    def get_shortest_segment_km(self) -> float:
        """Get the distance of the shortest segment in the route."""
        return min(self.waypoint_distances) if self.waypoint_distances else 0.0
    
    def validate_consistency(self) -> bool:
        """Validate that waypoint distances sum approximately to total distance."""
        if not self.waypoint_distances:
            return self.total_distance_km == 0.0
        
        waypoint_sum = sum(self.waypoint_distances)
        # Allow 1% tolerance for rounding errors
        tolerance = max(0.1, self.total_distance_km * 0.01)
        return abs(waypoint_sum - self.total_distance_km) <= tolerance
    
    def __str__(self) -> str:
        """String representation of route result."""
        if self.error:
            return f"RouteResult(ERROR: {self.error})"
        
        segments = len(self.waypoint_distances)
        return (f"RouteResult({self.total_distance_km:.2f}km, {self.total_time_hours:.2f}h, "
                f"{segments} segments, method={self.calculation_method})")


@dataclass
class BoundingBox:
    """Geographic bounding box for network graph retrieval."""
    north: float
    south: float
    east: float
    west: float
    
    def __post_init__(self):
        """Validate bounding box coordinates."""
        if not self._validate_coordinates():
            raise ValueError(f"Invalid bounding box coordinates: {self}")
    
    def _validate_coordinates(self) -> bool:
        """Validate that coordinates are within valid ranges."""
        if not (-90 <= self.south <= 90 and -90 <= self.north <= 90):
            return False
        if not (-180 <= self.west <= 180 and -180 <= self.east <= 180):
            return False
        if self.south >= self.north:
            return False
        if self.west >= self.east:
            return False
        return True
    
    @classmethod
    def from_locations(cls, locations: List, padding_km: float = 10.0) -> 'BoundingBox':
        """
        Create bounding box from list of locations with padding.
        
        Args:
            locations: List of Location objects
            padding_km: Padding distance in kilometers
            
        Returns:
            BoundingBox encompassing all locations with padding
            
        Raises:
            ValueError: If locations list is empty or contains invalid coordinates
        """
        if not locations:
            raise ValueError("Cannot create bounding box from empty locations list")
        
        # Extract coordinates and validate
        coords = []
        for loc in locations:
            if not hasattr(loc, 'lat') or not hasattr(loc, 'lng'):
                raise ValueError(f"Location object missing lat/lng attributes: {loc}")
            if not (-90 <= loc.lat <= 90 and -180 <= loc.lng <= 180):
                raise ValueError(f"Invalid coordinates in location: {loc}")
            coords.append((loc.lat, loc.lng))
        
        # Find min/max coordinates
        lats = [coord[0] for coord in coords]
        lngs = [coord[1] for coord in coords]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        # Convert padding from km to degrees (approximate)
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        lat_padding = padding_km / 111.0
        
        # Use average latitude for longitude padding calculation
        avg_lat = (min_lat + max_lat) / 2
        lng_padding = padding_km / (111.0 * abs(math.cos(math.radians(avg_lat))))
        
        # Apply padding and ensure we stay within valid coordinate ranges
        south = max(-90.0, min_lat - lat_padding)
        north = min(90.0, max_lat + lat_padding)
        west = max(-180.0, min_lng - lng_padding)
        east = min(180.0, max_lng + lng_padding)
        
        return cls(north=north, south=south, east=east, west=west)
    
    @classmethod
    def adaptive_padding(cls, locations: List) -> 'BoundingBox':
        """
        Create bounding box with adaptive padding based on route distance.
        
        Uses intelligent padding algorithm:
        - Short routes (<50km): 10km padding
        - Medium routes (50-200km): 15% of route distance as padding
        - Long routes (>200km): 30km padding (capped at 50km max)
        
        Args:
            locations: List of Location objects
            
        Returns:
            BoundingBox with adaptive padding
        """
        if not locations:
            raise ValueError("Cannot create bounding box from empty locations list")
        
        if len(locations) < 2:
            # Single location, use base padding
            return cls.from_locations(locations, padding_km=10.0)
        
        # Calculate approximate route distance using Haversine
        total_distance = 0.0
        for i in range(len(locations) - 1):
            loc1, loc2 = locations[i], locations[i + 1]
            distance = cls._haversine_distance(loc1.lat, loc1.lng, loc2.lat, loc2.lng)
            total_distance += distance
        
        # Determine padding based on route distance
        if total_distance < 50:
            # Short routes: 10km padding
            padding_km = 10.0
        elif total_distance < 200:
            # Medium routes: 15% of distance as padding
            padding_km = max(10.0, total_distance * 0.15)
        else:
            # Long routes: 30km padding, capped at 50km
            padding_km = min(50.0, max(30.0, total_distance * 0.15))
        
        logger.debug(f"Adaptive padding: route_distance={total_distance:.1f}km, padding={padding_km:.1f}km")
        
        return cls.from_locations(locations, padding_km=padding_km)
    
    @staticmethod
    def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate Haversine distance between two coordinate pairs."""
        R = 6371  # Earth radius in km
        lat1, lng1 = math.radians(lat1), math.radians(lng1)
        lat2, lng2 = math.radians(lat2), math.radians(lng2)
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def area_km2(self) -> float:
        """Calculate approximate area of bounding box in square kilometers."""
        # Convert degrees to km (approximate)
        lat_km = (self.north - self.south) * 111.0
        avg_lat = (self.north + self.south) / 2
        lng_km = (self.east - self.west) * 111.0 * abs(math.cos(math.radians(avg_lat)))
        return lat_km * lng_km
    
    def is_reasonable_size(self, max_area_km2: float = 50000) -> bool:
        """Check if bounding box is reasonable size for network download."""
        return self.area_km2() <= max_area_km2
    
    def __str__(self) -> str:
        """String representation of bounding box."""
        return f"BoundingBox(N:{self.north:.4f}, S:{self.south:.4f}, E:{self.east:.4f}, W:{self.west:.4f})"


class NetworkCache:
    """Thread-safe cache for OSMnx network graphs."""
    
    def __init__(self, max_age_hours: int = 24, max_cache_size: int = 50):
        """
        Initialize network cache.
        
        Args:
            max_age_hours: Maximum age of cached entries in hours
            max_cache_size: Maximum number of cached network graphs
        """
        self.cache = {}  # bbox_key -> network_graph
        self.cache_times = {}  # bbox_key -> datetime
        self.cache_access_times = {}  # bbox_key -> datetime (for LRU)
        self.max_age_hours = max_age_hours
        self.max_cache_size = max_cache_size
        self._lock = threading.Lock()
        logger.info(f"NetworkCache initialized with max_age_hours={max_age_hours}, max_size={max_cache_size}")
    
    def _bbox_to_key(self, bbox: BoundingBox) -> str:
        """Convert bounding box to cache key string."""
        # Round coordinates to avoid cache misses due to tiny differences
        return f"{bbox.north:.6f},{bbox.south:.6f},{bbox.east:.6f},{bbox.west:.6f}"
    
    def _is_expired(self, cache_time: datetime, max_age_hours: Optional[int] = None) -> bool:
        """Check if cache entry is expired."""
        age_limit = max_age_hours if max_age_hours is not None else self.max_age_hours
        age_delta = timedelta(hours=age_limit)
        return datetime.now() - cache_time > age_delta
    
    def _evict_lru_entry(self) -> None:
        """Evict least recently used cache entry."""
        if not self.cache_access_times:
            return
        
        # Find least recently used entry
        lru_key = min(self.cache_access_times.keys(), 
                     key=lambda k: self.cache_access_times[k])
        
        # Remove from all caches
        self.cache.pop(lru_key, None)
        self.cache_times.pop(lru_key, None)
        self.cache_access_times.pop(lru_key, None)
        
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    def get_network(self, bbox: BoundingBox) -> Optional:
        """
        Retrieve cached network graph for bounding box.
        
        Args:
            bbox: Bounding box for network area
            
        Returns:
            Cached network graph or None if not found/expired
        """
        cache_key = self._bbox_to_key(bbox)
        
        with self._lock:
            # Check if entry exists
            if cache_key not in self.cache:
                logger.debug(f"Cache miss for bbox: {cache_key}")
                return None
            
            # Check if entry is expired
            cache_time = self.cache_times.get(cache_key)
            if cache_time and self._is_expired(cache_time):
                logger.debug(f"Cache entry expired for bbox: {cache_key}")
                # Remove expired entry
                self.cache.pop(cache_key, None)
                self.cache_times.pop(cache_key, None)
                self.cache_access_times.pop(cache_key, None)
                return None
            
            # Update access time for LRU
            self.cache_access_times[cache_key] = datetime.now()
            
            logger.debug(f"Cache hit for bbox: {cache_key}")
            return self.cache[cache_key]
    
    def cache_network(self, bbox: BoundingBox, graph) -> None:
        """
        Cache network graph for bounding box.
        
        Args:
            bbox: Bounding box for network area
            graph: Network graph to cache
        """
        if graph is None:
            logger.warning("Attempted to cache None graph")
            return
        
        cache_key = self._bbox_to_key(bbox)
        current_time = datetime.now()
        
        with self._lock:
            # Check if we need to evict entries to make room
            while len(self.cache) >= self.max_cache_size:
                self._evict_lru_entry()
            
            # Store the network graph
            self.cache[cache_key] = graph
            self.cache_times[cache_key] = current_time
            self.cache_access_times[cache_key] = current_time
            
            logger.debug(f"Cached network for bbox: {cache_key}")
    
    def clear_expired_cache(self, max_age_hours: Optional[int] = None) -> int:
        """
        Remove expired cache entries.
        
        Args:
            max_age_hours: Override default max age for this cleanup
            
        Returns:
            Number of entries removed
        """
        removed_count = 0
        
        with self._lock:
            expired_keys = []
            
            for cache_key, cache_time in self.cache_times.items():
                if self._is_expired(cache_time, max_age_hours):
                    expired_keys.append(cache_key)
            
            # Remove expired entries
            for key in expired_keys:
                self.cache.pop(key, None)
                self.cache_times.pop(key, None)
                self.cache_access_times.pop(key, None)
                removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleared {removed_count} expired cache entries")
        
        return removed_count
    
    def clear_all(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            self.cache_times.clear()
            self.cache_access_times.clear()
            
            if count > 0:
                logger.info(f"Cleared all {count} cache entries")
        
        return count
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            current_time = datetime.now()
            
            # Count expired entries
            expired_count = 0
            for cache_time in self.cache_times.values():
                if self._is_expired(cache_time):
                    expired_count += 1
            
            # Calculate total cache size (approximate)
            total_size_mb = 0
            try:
                import sys
                for graph in self.cache.values():
                    if graph is not None:
                        total_size_mb += sys.getsizeof(graph) / (1024 * 1024)
            except Exception:
                total_size_mb = -1  # Size calculation failed
            
            return {
                "total_entries": len(self.cache),
                "expired_entries": expired_count,
                "max_cache_size": self.max_cache_size,
                "max_age_hours": self.max_age_hours,
                "total_size_mb": round(total_size_mb, 2) if total_size_mb >= 0 else "unknown",
                "cache_utilization": round(len(self.cache) / self.max_cache_size * 100, 1)
            }
    
    def contains_bbox(self, bbox: BoundingBox) -> bool:
        """
        Check if bounding box is in cache (not expired).
        
        Args:
            bbox: Bounding box to check
            
        Returns:
            True if bbox is cached and not expired
        """
        cache_key = self._bbox_to_key(bbox)
        
        with self._lock:
            if cache_key not in self.cache:
                return False
            
            cache_time = self.cache_times.get(cache_key)
            if cache_time and self._is_expired(cache_time):
                return False
            
            return True
    
    def get_bbox_coverage(self, target_bbox: BoundingBox) -> List[BoundingBox]:
        """
        Find cached bounding boxes that overlap with target bbox.
        
        Args:
            target_bbox: Target bounding box to find coverage for
            
        Returns:
            List of cached bounding boxes that overlap with target
        """
        overlapping_bboxes = []
        
        with self._lock:
            for cache_key in self.cache.keys():
                # Skip expired entries
                cache_time = self.cache_times.get(cache_key)
                if cache_time and self._is_expired(cache_time):
                    continue
                
                # Parse cache key back to bbox
                try:
                    coords = cache_key.split(',')
                    cached_bbox = BoundingBox(
                        north=float(coords[0]),
                        south=float(coords[1]),
                        east=float(coords[2]),
                        west=float(coords[3])
                    )
                    
                    # Check for overlap
                    if self._bboxes_overlap(target_bbox, cached_bbox):
                        overlapping_bboxes.append(cached_bbox)
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse cached bbox key: {cache_key}, error: {e}")
        
        return overlapping_bboxes
    
    def _bboxes_overlap(self, bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
        """Check if two bounding boxes overlap."""
        return not (bbox1.east < bbox2.west or bbox2.east < bbox1.west or
                   bbox1.north < bbox2.south or bbox2.north < bbox1.south)


class RouteCalculationService:
    """
    Service for calculating route distances and times using OSMnx.
    
    Provides road-based distance calculations with fallback to Haversine
    when OSMnx is unavailable or fails.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the route calculation service."""
        self.config = config or self._get_default_config()
        self.cache = NetworkCache(max_age_hours=self.config.get('cache_max_age_hours', 24))
        self.osmnx_available = OSMNX_AVAILABLE
        
        logger.info(f"RouteCalculationService initialized. OSMnx available: {self.osmnx_available}")
        
        if self.osmnx_available:
            self._configure_osmnx()
    
    def _get_default_config(self) -> dict:
        """Get default configuration for route calculations."""
        try:
            # Try to import configuration from app.config
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from app.config import get_osmnx_config
            return get_osmnx_config()
        except ImportError:
            logger.warning("Could not import app.config, using fallback configuration")
            return {
                "cache_enabled": True,
                "cache_max_age_hours": 24,
                "network_timeout_seconds": 30,
                "fallback_speed_kmh": 80.0,
                "base_padding_km": 10.0,
                "min_padding_km": 5.0,
                "max_padding_km": 50.0,
                "adaptive_padding": True,
                "network_type": "drive"
            }
    
    def _configure_osmnx(self) -> None:
        """Configure OSMnx settings."""
        if not self.osmnx_available:
            return
            
        try:
            # Configure OSMnx settings
            ox.settings.log_console = False
            ox.settings.use_cache = self.config.get('cache_enabled', True)
            ox.settings.timeout = self.config.get('network_timeout_seconds', 30)
            logger.info("OSMnx configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure OSMnx: {e}")
    
    def calculate_distance(self, loc1, loc2) -> DistanceResult:
        """
        Calculate distance between two locations.
        
        Args:
            loc1: First location (Location object)
            loc2: Second location (Location object)
            
        Returns:
            DistanceResult with distance and calculation method
        """
        # Implementation will be added in later tasks
        logger.info(f"Distance calculation requested between locations")
        return DistanceResult(
            distance_km=0.0,
            calculation_method="placeholder",
            error="Implementation pending"
        )
    
    def calculate_route_distance(self, waypoints: List) -> RouteResult:
        """
        Calculate total distance for route with multiple waypoints.
        
        Args:
            waypoints: List of Location objects representing route waypoints
            
        Returns:
            RouteResult with total distance and time
        """
        # Implementation will be added in later tasks
        logger.info(f"Route calculation requested for {len(waypoints)} waypoints")
        return RouteResult(
            total_distance_km=0.0,
            total_time_hours=0.0,
            waypoint_distances=[],
            calculation_method="placeholder",
            network_available=self.osmnx_available
        )
    
    def calculate_drive_time(self, distance_km: float, route_type: str = "highway") -> float:
        """
        Calculate drive time based on distance and route type.
        
        Args:
            distance_km: Distance in kilometers
            route_type: Type of route (highway, urban, rural)
            
        Returns:
            Drive time in hours
        """
        # Implementation will be added in later tasks
        speed_kmh = self.config.get('fallback_speed_kmh', 80.0)
        return distance_km / speed_kmh
    
    def is_location_near_route(self, location, route_points: List) -> Tuple[bool, float]:
        """
        Check if location is near a route and return deviation distance.
        
        Args:
            location: Location to check
            route_points: List of Location objects representing route
            
        Returns:
            Tuple of (is_near, deviation_distance_km)
        """
        # Implementation will be added in later tasks
        logger.info("Route proximity check requested")
        return False, 0.0


# Global service instance (will be initialized when needed)
_route_service: Optional[RouteCalculationService] = None


def get_route_service(config: Optional[dict] = None) -> RouteCalculationService:
    """
    Get or create the global route calculation service instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        RouteCalculationService instance
    """
    global _route_service
    if _route_service is None:
        _route_service = RouteCalculationService(config)
    return _route_service