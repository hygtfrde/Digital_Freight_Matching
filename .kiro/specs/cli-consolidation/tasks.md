# Implementation Plan

- [x] 1. Create unified database manager
  - Create `db_manager.py` with consolidated initialization logic from existing scripts
  - Implement safe initialization that prevents duplicates like `safe_db_init.py`
  - Add database status checking and verification methods
  - Write unit tests for database operations
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 2. Implement order processing engine
  - Create `order_processor.py` with order validation and constraint checking
  - Implement 1km proximity constraint validation using haversine distance calculation
  - Add time calculation logic for 15-minute stops plus deviation time
  - Implement capacity checking with volume (CBM) and weight (pounds) validation
  - Write unit tests for proximity, time, and capacity constraint validation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_

- [ ] 3. Create route optimization module
  - Create `route_optimizer.py` extending existing `PricingService` logic
  - Implement profitability calculation using cost-per-mile data
  - Add route creation from pending orders with profitability validation
  - Implement route sequence optimization for minimal deviation
  - Write unit tests for profitability calculations and route optimization
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 4. Build consolidated CLI interface
  - Create `dfm_cli.py` as main entry point replacing dashboard menu system
  - Implement command parser for essential operations (status, match, routes, orders, init)
  - Add system status display showing current profitability and pending orders
  - Implement interactive order input with format validation
  - Write unit tests for CLI command parsing and user input validation
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 5. Integrate order format handling
  - Implement parser for specified order format with cargo packages array
  - Add coordinate validation for pickup/dropoff locations
  - Integrate with existing `create_order_from_dict` helper function
  - Add error handling for malformed order data
  - Write unit tests for order format parsing and validation
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 6. Implement route format support
  - Add route format parser for coordinate arrays
  - Integrate route format with existing `Route` model and path handling
  - Implement route display and management through CLI
  - Write unit tests for route format handling
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 7. Add comprehensive error handling
  - Implement input validation with clear error messages for all user inputs
  - Add business rule enforcement with specific constraint violation messages
  - Implement database error recovery with rollback and retry logic
  - Add logging for all critical operations and errors
  - Write unit tests for error scenarios and recovery mechanisms
  - _Requirements: 1.3, 2.3, 3.3, 5.4_

- [ ] 8. Create system configuration management
  - Implement configuration class for system parameters (1km limit, 15min stops, 10hr max)
  - Add support for cost-per-mile updates from external spreadsheet data
  - Implement dynamic profitability recalculation when costs change
  - Write unit tests for configuration management and cost updates
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 9. Remove redundant components
  - Delete duplicate initialization scripts (`simple_db_init.py`, `unified_db_init.py`, `init_contract_data.py`)
  - Remove stubbed dashboard methods from `dashboard_methods.py`
  - Clean up unused imports and dependencies
  - Update any remaining references to removed files
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 10. Integrate and test complete system
  - Wire all components together in main CLI application
  - Implement end-to-end order processing workflow from input to database
  - Add system status monitoring with real-time profitability tracking
  - Create comprehensive integration tests covering full order-to-route matching flow
  - Write performance tests for order processing speed and memory usage
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4_