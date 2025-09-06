
# Design Document

## Overview

This design integrates OSMnx (OpenStreetMap) routing capabilities into the existing Digital Freight Matcher system to replace Haversine distance calculations with actual road distances and drive times. The integration maintains backward compatibility while adding enhanced route calculation capabilities.

## Architecture

### Current System
- `Location.distance_to()` uses Haversine formula for straight-line distances
- `Route.total_distance()` and `Route.total_time()` use simple calculations
- `CriteriaMatcher.is_location_near_route()` uses linear distance checks
- `OrderProcessor._calculate_route_deviation()` uses approximations

### New Architecture
The design introduces a new `RouteCalculationService` that encapsulates OSMnx functionality while maintaining existing interfaces through a strategy pattern.

```
┌─────────────────────┐    ┌──────────────────────┐
│   Location Model    │    │  Route Model         │
│                     │    │                      │
│ + distance_to()     │◄───┤ + total_distance()   │
│ + road_distance_to()│    │ + total_time()       │
└─────────────────────┘    └──────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────────────────────────────────┐
│         RouteCalculationService                 │
│                                                 │
│ + calculate_distance(loc1, loc2)               │
│ + calculate_route_distance(waypoints)          │
│ + calculate_drive_time(distance, route_type)   │
│ + get_network_graph(bbox)                      │
└─────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│            OSMnx Integration                    │
│                                                 │
│ + NetworkCache                                  │
│ + FallbackCalculator                           │
│ + RouteOptimizer                               │
└─────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. RouteCalculationService
Primary service class that handles all route calculations with OSMnx integration.

**Interface:**
```python
class RouteCalculationService:
    def calculate_distance(self, loc1: Location, loc2: Location) -> DistanceResult
    def calculate_route_distance(self, waypoints: List[Location]) -> RouteResult  
    def calculate_drive_time(self, distance_km: float, route_type: str = "highway") -> float
    def is_location_near_route(self, location: Location, route_points: List[Location]) -> Tuple[bool, float]
```

### 2. NetworkCache
Manages OSMnx network graph caching to improve performance.

**Interface:**
```python
class NetworkCache:
    def get_network(self, bbox: BoundingBox) -> Optional[NetworkGraph]
    def cache_network(self, bbox: BoundingBox, graph: NetworkGraph) -> None
    def clear_expired_cache(self, max_age_hours: int = 24) -> None
```

### 3. Enhanced Location Model
Extends existing Location model with road distance capabilities.

**New Methods:**
```python
def road_distance_to(self, other: Location) -> float
def road_time_to(self, other: Location, speed_kmh: float = 80.0) -> float
```

### 4. Enhanced Route Model  
Updates Route model to use road distances while maintaining compatibility.

**Updated Methods:**
```python
def total_distance(self, use_roads: bool = True) -> float
def total_time(self, base_speed_kmh: float = 80.0, use_roads: bool = True) -> float
```

## Data Models

### DistanceResult
```python
@dataclass
class DistanceResult:
    distance_km: float
    calculation_method: str  # "osmnx" or "haversine"
    drive_time_hours: Optional[float] = None
    route_nodes: Optional[List] = None
    error: Optional[str] = None
```

### RouteResult
```python
@dataclass  
class RouteResult:
    total_distance_km: float
    total_time_hours: float
    waypoint_distances: List[float]
    calculation_method: str
    network_available: bool
```

### BoundingBox
```python
@dataclass
class BoundingBox:
    north: float
    south: float  
    east: float
    west: float
    
    @classmethod
    def from_locations(cls, locations: List[Location], padding_km: float = 10.0) -> 'BoundingBox'
    
    @classmethod
    def adaptive_padding(cls, locations: List[Location]) -> 'BoundingBox'
```

## Error Handling

### Fallback Strategy
1. **Primary**: OSMnx road network calculation
2. **Secondary**: Cached network data if available  
3. **Fallback**: Haversine distance calculation
4. **Logging**: All fallbacks logged for monitoring

### Error Scenarios
- Network unavailable → Use Haversine + estimated speed
- OSMnx timeout → Use cached data or fallback
- Invalid coordinates → Return error with details
- Graph download failure → Use existing cache or fallback

## Testing Strategy

### Unit Tests
- `RouteCalculationService` with mocked OSMnx calls
- `NetworkCache` functionality and expiration
- Fallback behavior under various failure conditions
- Distance calculation accuracy comparisons

### Integration Tests  
- End-to-end route calculations with real OSMnx data
- Performance testing with cached vs uncached networks
- Backward compatibility with existing route calculations
- Error handling with network failures

### Test Data
- Use existing test locations from `test_order_processor.py`
- Atlanta to Ringgold route from OSMnx test
- Short distance routes for cache testing
- Invalid coordinate edge cases
#
# Implementation Approach

### Phase 1: Core Service Implementation
Create `RouteCalculationService` with basic OSMnx integration and fallback mechanisms.

### Phase 2: Model Integration  
Update `Location` and `Route` models to use the new service while maintaining backward compatibility.

### Phase 3: System Integration
Update `OrderProcessor` to use enhanced route calculations.

### Phase 4: Performance Optimization
Implement caching, batch processing, and performance monitoring.

## Configuration

### Settings
```python
OSMNX_CONFIG = {
    "cache_enabled": True,
    "cache_max_age_hours": 24,
    "network_timeout_seconds": 30,
    "fallback_speed_kmh": 80.0,
    "base_padding_km": 10.0,  # Increased to capture major highways
    "min_padding_km": 5.0,    # Minimum padding for short routes
    "max_padding_km": 50.0,   # Maximum to prevent huge downloads
    "adaptive_padding": True,  # Use distance-based padding
    "network_type": "drive"
}
```

### Dependencies
- Add `osmnx` to requirements.txt
- Add `networkx` (dependency of osmnx)
- Add `folium` for optional map visualization
- Ensure `geopandas` compatibility

## Migration Strategy

### Backward Compatibility
- Existing `distance_to()` method unchanged
- New methods added with `road_` prefix
- Optional parameters for road vs linear calculations
- Gradual migration path for existing code

### Performance Considerations
- Network graphs cached by geographic region
- Batch distance calculations when possible
- Async operations for non-critical calculations
- Monitoring and alerting for fallback usage

## Security and Privacy

### Data Handling
- No sensitive location data stored in OSMnx cache
- Network graphs contain only public road data
- Cache files stored locally, not transmitted
- Optional cache encryption for sensitive deployments

### Network Access
- OSMnx requires internet access for initial downloads
- Graceful degradation when offline
- Configurable timeout and retry policies
- Optional proxy support for corporate environments
## 
Bounding Box Strategy

### Adaptive Padding Algorithm
The system uses intelligent padding based on route characteristics:

1. **Base Padding**: 10km minimum to capture major highways and arterials
2. **Distance-Based Scaling**: 
   - Short routes (<50km): 10km padding
   - Medium routes (50-200km): 15% of route distance as padding  
   - Long routes (>200km): 30km padding (capped at 50km max)
3. **Highway Detection**: For routes >100km, expand bounding box to include major highway corridors

### Example Calculations
- **Atlanta to Ringgold (120km)**: 18km padding to capture I-75 corridor
- **Local delivery (5km)**: 10km padding for arterial roads
- **Cross-state route (400km)**: 50km padding for interstate system

### Fallback for Large Areas
If bounding box exceeds reasonable size limits:
1. Split route into segments with overlapping bounding boxes
2. Calculate each segment separately and combine results
3. Use state-level cached networks for very long routes
4. Fallback to Haversine + highway speed estimates if needed

This ensures we capture optimal routing through major transportation corridors while maintaining reasonable download sizes and performance.