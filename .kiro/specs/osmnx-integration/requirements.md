# Requirements Document

## Introduction

This feature refactors the existing Digital Freight Matcher system to use OSMnx (OpenStreetMap) for calculating actual road distances and drive times instead of the current Haversine formula that calculates straight-line distances. This will provide more accurate route planning and time estimates for freight matching operations.

## Requirements

### Requirement 1

**User Story:** As a logistics coordinator, I want the system to calculate actual road distances between locations, so that route planning reflects real-world driving conditions.

#### Acceptance Criteria

1. WHEN the system calculates distance between two locations THEN it SHALL use OSMnx to find the shortest road path
2. WHEN OSMnx is unavailable or fails THEN the system SHALL fallback to Haversine distance calculation
3. WHEN calculating route distances THEN the system SHALL return both distance in kilometers and estimated drive time
4. WHEN multiple waypoints exist on a route THEN the system SHALL calculate the total road distance through all waypoints

### Requirement 2

**User Story:** As a freight dispatcher, I want accurate drive time estimates for routes, so that I can provide realistic delivery schedules to clients.

#### Acceptance Criteria

1. WHEN calculating drive time THEN the system SHALL use road network data to estimate realistic travel times
2. WHEN calculating route time THEN the system SHALL include both driving time and stop time for loading/unloading
3. WHEN road data is unavailable THEN the system SHALL use a fallback speed calculation based on distance
4. WHEN route includes multiple stops THEN the system SHALL add appropriate stop time for each pickup/dropoff

### Requirement 3

**User Story:** As a system administrator, I want the OSMnx integration to be performant and reliable, so that route calculations don't slow down the matching process.

#### Acceptance Criteria

1. WHEN OSMnx data is requested THEN the system SHALL cache road network data to avoid repeated downloads
2. WHEN calculating distances for nearby locations THEN the system SHALL reuse existing network graphs
3. WHEN OSMnx operations fail THEN the system SHALL log errors and continue with fallback calculations
4. WHEN network requests timeout THEN the system SHALL use cached data or fallback methods

### Requirement 4

**User Story:** As a developer, I want the OSMnx integration to be modular and testable, so that it can be easily maintained and updated.

#### Acceptance Criteria

1. WHEN integrating OSMnx THEN the system SHALL create a separate service class for route calculations
2. WHEN implementing route calculations THEN the system SHALL maintain backward compatibility with existing interfaces
3. WHEN testing route calculations THEN the system SHALL provide mock capabilities for OSMnx operations
4. WHEN updating existing models THEN the system SHALL preserve all current functionality while adding new capabilities

### Requirement 5

**User Story:** As a logistics coordinator, I want route deviation calculations to use actual road networks, so that order matching considers real detour distances.

#### Acceptance Criteria

1. WHEN calculating route deviation for new orders THEN the system SHALL use road distance instead of straight-line distance
2. WHEN determining if an order fits a route THEN the system SHALL calculate actual additional driving distance
3. WHEN optimizing routes THEN the system SHALL consider real road constraints and network topology
4. WHEN multiple route options exist THEN the system SHALL compare actual drive times and distances