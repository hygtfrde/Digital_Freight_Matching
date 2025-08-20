# Database Setup - Refactored for Safety

This document explains the refactored database setup system that prevents duplicate data seeding.

## Problem Solved

The original database setup scripts could create duplicate data if run multiple times:
- Multiple contract clients
- Duplicate trucks and routes  
- Redundant contract orders
- Inconsistent database state

## Solution: Safe Database Initialization

The new `safe_db_init.py` script includes comprehensive checks to prevent duplicate seeding:

### Key Features

1. **Existence Checks**: Verifies if data already exists before creating new records
2. **Smart Detection**: Identifies contract data by client name and location coordinates
3. **Partial Recovery**: Can complete initialization if only some data exists
4. **Force Override**: Option to reinitialize anyway (for development/testing)

### How It Works

```python
# Check existing data counts
existing_data, counts = check_existing_data()

# Determine if already initialized
if is_database_initialized(counts):
    logger.info("Database already initialized - skipping")
    return

# Only create missing data
if not find_contract_client():
    create_contract_client()

# Reuse existing locations where possible
existing_locations = find_existing_locations()
```

## Usage

### Command Line Interface

Use the new `manage_db.py` script for database management:

```bash
# Initialize database safely (recommended)
python manage_db.py init

# Force reinitialize (creates duplicates)
python manage_db.py init --force

# Check database status
python manage_db.py status

# Verify database contents
python manage_db.py verify

# Reset database completely
python manage_db.py reset --confirm
```

### Programmatic Usage

```python
from safe_db_init import SafeDataIngestion
from sqlmodel import Session
from database import engine

with Session(engine) as session:
    ingestion = SafeDataIngestion(session)
    
    # Safe initialization (default)
    ingestion.initialize_safely()
    
    # Force reinitialize
    ingestion.initialize_safely(force_reinit=True)
```

### Integration with Setup Scripts

The existing setup scripts now use safe initialization:

- `setup_dfm.py` → calls `safe_db_init.py`
- `setup_database.py` → calls `safe_db_init.py`
- `app/main.py` → runs safe init on startup

## Detection Logic

### Contract Client Detection
```python
client = session.exec(
    select(Client).where(Client.name == "Too-Big-To-Fail Company")
).first()
```

### Location Detection
```python
# Match coordinates within 100m tolerance
tolerance = 0.001  # ~100 meters
location = session.exec(
    select(Location).where(
        Location.lat.between(lat - tolerance, lat + tolerance),
        Location.lng.between(lng - tolerance, lng + tolerance)
    )
).first()
```

### Route Detection
```python
existing_route = session.exec(
    select(Route).where(
        Route.location_origin_id == atlanta.id,
        Route.location_destiny_id == destination.id
    )
).first()
```

## Expected Data Structure

After safe initialization, the database should contain:

- **1 Contract Client**: "Too-Big-To-Fail Company"
- **6 Locations**: Atlanta (origin) + 5 destinations
- **5 Trucks**: Specialized contract trucks
- **5 Routes**: Atlanta to each destination
- **5 Contract Orders**: One per route with cargo/packages
- **1 Example Client**: For demo orders (optional)

## Migration from Old Scripts

If you have data from old initialization scripts:

1. **Check current state**:
   ```bash
   python manage_db.py status
   ```

2. **Verify data integrity**:
   ```bash
   python manage_db.py verify
   ```

3. **If duplicates exist, reset and reinitialize**:
   ```bash
   python manage_db.py reset --confirm
   python manage_db.py init
   ```

## Testing

Test the safe initialization:

```bash
# Run the test script
python test_safe_init.py
```

This will:
1. Show initial database state
2. Run first initialization
3. Run second initialization (should skip)
4. Run forced initialization (creates duplicates)

## Benefits

1. **Idempotent**: Can run multiple times safely
2. **Resilient**: Handles partial initialization states
3. **Transparent**: Clear logging of what's created vs. reused
4. **Flexible**: Force option for development needs
5. **Integrated**: Works with existing setup workflows

## Files Changed

- **New**: `safe_db_init.py` - Main safe initialization logic
- **New**: `manage_db.py` - CLI for database management
- **New**: `test_safe_init.py` - Test script
- **Updated**: `setup_dfm.py` - Uses safe initialization
- **Updated**: `setup_database.py` - Uses safe initialization  
- **Updated**: `app/main.py` - Safe init on startup

## Backward Compatibility

The refactored system is fully backward compatible:
- Existing databases work without changes
- Old scripts still function (but may create duplicates)
- New safe scripts detect and work with existing data

## Troubleshooting

### "Database already initialized" message
This is normal - the system detected existing data and skipped initialization to prevent duplicates.

### Want to reinitialize anyway
Use the force flag: `python manage_db.py init --force`

### Partial data detected
The system will complete the missing parts automatically.

### Duplicates from old scripts
Reset and reinitialize:
```bash
python manage_db.py reset --confirm
python manage_db.py init
```