# Implementation Plan

- [x] 1. Set up OSMnx dependencies and basic infrastructure
  - Add osmnx, networkx, and folium to requirements.txt
  - Create services/route_calculation.py module structure
  - Set up basic configuration and logging
  - _Requirements: 3.1, 3.3, 4.1_

- [-] 2. Implement core data models and utilities
- [x] 2.1 Create BoundingBox and result data classes
  - Implement BoundingBox dataclass with adaptive padding methods
  - Create DistanceResult and RouteResult dataclasses
  - Add coordinate validation and error handling utilities
  - _Requirements: 1.1, 1.3, 4.4_

- [-] 2.2 Implement NetworkCache class
  - Create cache storage and retrieval mechanisms
  - Add cache expiration and cleanup functionality
  - Implement thread-safe cache operations
  - Write unit tests for cache behavior
  - _Requirements: 3.1, 3.2_

- [ ] 3. Build RouteCalculationService core functionality
- [ ] 3.1 Implement basic distance calculation with OSMnx
  - Create calculate_distance method with OSMnx integration
  - Add fallback to Haversine when OSMnx fails
  - Implement error handling and logging
  - Write unit tests with mocked OSMnx calls
  - _Requirements: 1.1, 1.2, 3.3_

- [ ] 3.2 Add multi-waypoint route calculation
  - Implement calculate_route_distance for multiple locations
  - Add route optimization for waypoint ordering
  - Handle edge cases with invalid or unreachable locations
  - Write tests for complex multi-stop routes
  - _Requirements: 1.4, 2.4_

- [ ] 3.3 Implement drive time calculations
  - Add calculate_drive_time method using road network data
  - Include stop time calculations for loading/unloading
  - Add different speed profiles for route types
  - Write tests comparing with existing time calculations
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4. Enhance Location model with road distance capabilities
- [ ] 4.1 Add road distance methods to Location class
  - Implement road_distance_to method using RouteCalculationService
  - Add road_time_to method for drive time estimates
  - Maintain backward compatibility with existing distance_to method
  - Write unit tests for new Location methods
  - _Requirements: 1.1, 4.2, 4.4_

- [ ] 4.2 Update Location model error handling
  - Add graceful fallback when road calculation fails
  - Implement caching for frequently calculated distances
  - Add logging for fallback usage monitoring
  - Write integration tests with real OSMnx data
  - _Requirements: 3.3, 3.4_

- [ ] 5. Enhance Route model with road-based calculations
- [ ] 5.1 Update Route.total_distance to use road calculations
  - Modify total_distance method to optionally use road distances
  - Add use_roads parameter with default True
  - Ensure backward compatibility for existing code
  - Write tests comparing road vs linear distance results
  - _Requirements: 1.4, 4.2, 4.4_

- [ ] 5.2 Update Route.total_time with realistic drive times
  - Enhance total_time method to use road-based calculations
  - Include realistic speed estimates based on road types
  - Add stop time calculations for pickup/dropoff operations
  - Write performance tests for route time calculations
  - _Requirements: 2.1, 2.2, 2.4_

- [ ] 6. Update route matching and optimization logic
- [ ] 6.1 Enhance CriteriaMatcher with road distance calculations
  - Update is_location_near_route to use road distances
  - Modify route deviation calculations in OrderProcessor
  - Add realistic distance thresholds based on road networks
  - Write tests for improved route matching accuracy
  - _Requirements: 5.1, 5.2_

- [ ] 6.2 Update PricingService route optimization
  - Enhance route profitability calculations with accurate distances
  - Update order matching logic to use road-based deviations
  - Add route optimization considering actual drive times
  - Write integration tests for end-to-end order processing
  - _Requirements: 5.3, 5.4_

- [ ] 7. Add performance monitoring and optimization
- [ ] 7.1 Implement caching and performance monitoring
  - Add metrics collection for OSMnx vs fallback usage
  - Implement batch distance calculation optimization
  - Add performance logging and monitoring dashboards
  - Write performance tests and benchmarks
  - _Requirements: 3.1, 3.2_

- [ ] 7.2 Add configuration and deployment support
  - Create configuration management for OSMnx settings
  - Add environment-specific configuration (dev/prod)
  - Implement graceful degradation for offline environments
  - Write deployment and configuration documentation
  - _Requirements: 3.4, 4.1_

- [ ] 8. Integration testing and validation
- [ ] 8.1 Create comprehensive integration tests
  - Test end-to-end route calculations with real data
  - Validate accuracy improvements over Haversine calculations
  - Test error handling and fallback scenarios
  - Create performance benchmarks and regression tests
  - _Requirements: 1.1, 1.2, 2.1, 3.3_

- [ ] 8.2 Update existing tests and documentation
  - Update all existing route calculation tests
  - Add migration guide for teams using the system
  - Create troubleshooting guide for OSMnx issues
  - Update API documentation with new capabilities
  - _Requirements: 4.2, 4.3, 4.4_