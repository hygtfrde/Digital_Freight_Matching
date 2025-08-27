# Requirements Document

## Introduction

The Digital Freight Matching (DFM) system needs to implement precise freight matching logic that adheres to strict business constraints while consolidating the current overlapping components into a focused CLI application. The system must handle order matching with 1km proximity constraints, capacity management, time limits, and profitability calculations to convert the current $388.15 daily loss into profit.

## Requirements

### Requirement 1: Order Proximity Matching

**User Story:** As a logistics manager, I want orders to only match routes where pickup and dropoff locations are within 1km of existing route points, so that we minimize deviation costs and maintain schedule integrity.

#### Acceptance Criteria

1. WHEN processing an order THEN the system SHALL verify pickup location is within 1km of any point on an existing route
2. WHEN processing an order THEN the system SHALL verify dropoff location is within 1km of any point on an existing route  
3. WHEN an order doesn't meet proximity requirements THEN the system SHALL reject the match and suggest alternative options
4. WHEN calculating route deviation THEN the system SHALL include the actual distance from route to pickup/dropoff points

### Requirement 2: Capacity and Cargo Management

**User Story:** As a logistics manager, I want the system to ensure cargo fits within truck capacity considering existing loads, so that we don't overload vehicles or violate capacity constraints.

#### Acceptance Criteria

1. WHEN adding cargo to a route THEN the system SHALL calculate total volume including existing cargo and new packages
2. WHEN adding cargo to a route THEN the system SHALL verify total weight doesn't exceed truck capacity
3. WHEN cargo cannot fit THEN the system SHALL save the order for potential combination with other orders to form new routes
4. WHEN combining saved orders THEN the system SHALL create new routes only if they are profitable

### Requirement 3: Time and Schedule Management

**User Story:** As a logistics manager, I want routes to respect time constraints including pickup/dropoff time and daily limits, so that we maintain operational feasibility and driver compliance.

#### Acceptance Criteria

1. WHEN adding stops to a route THEN the system SHALL add 15 minutes per pickup and dropoff
2. WHEN calculating route time THEN the system SHALL include deviation time based on distance from main route (up to 1km)
3. WHEN total route time exceeds 10 hours THEN the system SHALL reject additional stops
4. WHEN routes return to origin THEN the system SHALL ensure round-trip completion within time limits

### Requirement 4: Order and Route Data Formats

**User Story:** As a developer, I want the system to handle standardized order and route formats, so that data processing is consistent and reliable.

#### Acceptance Criteria

1. WHEN receiving orders THEN the system SHALL parse the format: `{cargo: {packages: [volume_cbm, weight_pounds, type]}, pick-up: {latitude, longitude}, drop-off: {latitude, longitude}}`
2. WHEN processing routes THEN the system SHALL handle the format: `route: [{latitude, longitude}]` starting from origin point
3. WHEN validating package data THEN the system SHALL verify volume (CBM), weight (pounds), and type fields
4. WHEN storing location data THEN the system SHALL maintain precision for latitude/longitude coordinates

### Requirement 5: Profitability and Cost Management

**User Story:** As a logistics manager, I want accurate profitability calculations using current cost data, so that I can make informed decisions about order acceptance and route optimization.

#### Acceptance Criteria

1. WHEN calculating route costs THEN the system SHALL use per-mile costs from Mr. Lightyear's updated spreadsheet
2. WHEN evaluating new routes THEN the system SHALL ensure profitability before creation
3. WHEN adding orders to existing routes THEN the system SHALL show profitability impact in real-time
4. WHEN displaying route status THEN the system SHALL show current profit/loss for each of the 5 contract routes

### Requirement 6: System Consolidation

**User Story:** As a developer, I want a single, focused CLI interface that eliminates redundant components, so that the system is maintainable and efficient.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL provide a consolidated CLI with essential operations only
2. WHEN database initialization is needed THEN the system SHALL use a single, reliable initialization process
3. WHEN managing the system THEN all operations SHALL be accessible through the main CLI interface
4. WHEN consolidation is complete THEN duplicate scripts and stubbed methods SHALL be removed