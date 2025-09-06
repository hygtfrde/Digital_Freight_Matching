# Codebase Cleanup Report
Generated for project: .
Python files analyzed: 62

## Duplicate Code Analysis
Found 134 potential duplicates:
- main in demo_business_validator.py and db_manager.py
- get_system_status in db_manager.py and data_service.py
- initialize_database in db_manager.py and data_service.py
- verify_integrity in db_manager.py and data_service.py
- reset_database in db_manager.py and data_service.py
- main in demo_business_validator.py and debug_batch.py
- main in demo_business_validator.py and demo_documentation_generator.py
- __init__ in db_manager.py and order_processor.py
- main in demo_business_validator.py and validate_performance_system.py
- main in demo_business_validator.py and demo_performance_assessment.py

## Dead Code Analysis
Found 492 potentially unused items:
- function 'initialize_database' in db_manager.py:106
- function 'check_existing_data' in db_manager.py:161
- function 'verify_integrity' in db_manager.py:178
- function 'get_system_status' in db_manager.py:208
- function 'reset_database' in db_manager.py:250
- function 'get_all' in data_service.py:147
- function 'get_by_id' in data_service.py:151
- function 'create' in data_service.py:155
- function 'update' in data_service.py:159
- function 'delete' in data_service.py:163

## Code Quality Issues
Found 77 quality issues across 62 files
- complexity: 23 occurrences
- line_length: 40 occurrences
- todo: 14 occurrences

## Refactoring Recommendations
### Medium Priority:
- File is very large (718 lines) (db_manager.py)
- File is very large (502 lines) (documentation/deployment_guide.py)
- File is very large (531 lines) (documentation/examples.py)
- File is very large (860 lines) (app/main.py)
- File is very large (511 lines) (tests/test_route_data_models.py)