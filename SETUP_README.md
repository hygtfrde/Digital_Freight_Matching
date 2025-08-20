# Digital Freight Matcher - Simplified Setup

This simplified setup extracts all the starter data from the Google Sheets PDF and initializes your database in one step, all within a virtual environment.

## Quick Start

1. **Run the setup script:**
   ```bash
   python setup_dfm.py
   ```

That's it! The script will:
- Create a virtual environment (if needed)
- Install all required dependencies in the virtual environment
- Extract data from the PDF sheets
- Initialize the database with all starter data
- Verify everything is working

## Virtual Environment Usage

The setup automatically creates a virtual environment (`venv/`) to isolate dependencies.

### Activating the Virtual Environment

```bash
source venv/bin/activate
```

### Running Commands

**With activated virtual environment:**
```bash
# Activate first
source venv/bin/activate

# Then run commands normally
python verify_database.py
python app/main.py
```

**Without activating (direct execution):**
```bash
venv/bin/python verify_database.py
```

### Helper Script

For convenience, use the activation helper:
```bash
python activate_venv.py
```

## What Gets Created

### From Too-Big-To-Fail Contract Sheet:
- **5 specialized trucks** (800km range, 48m³ capacity each)
- **5 routes** from Atlanta to:
  - Ringgold (202 miles, -$53.51/day loss)
  - Augusta (189.2 miles, -$50.12/day loss)  
  - Savannah (496 miles, -$131.40/day loss)
  - Albany (364 miles, -$96.43/day loss)
  - Columbus (214 miles, -$56.69/day loss)
- **Contract orders** with pallets for each route

### From Order Examples Sheet:
- **Example client** with sample orders
- **Various pickup/dropoff locations** across Georgia
- **Package quantities** as specified in the examples

### From Price Calculator Sheet:
- **Route pricing data** for potential additional revenue
- **Availability status** for each route

## Database Structure

The setup creates a SQLite database (`logistics.db`) with:
- **Clients**: Too-Big-To-Fail Company + Example Client
- **Locations**: All Georgia cities + order locations
- **Trucks**: 5 specialized contract trucks
- **Routes**: 5 contract routes (currently losing $388.15/day total)
- **Orders**: Contract orders + example orders
- **Cargo & Packages**: Detailed cargo information

## Verification

After setup, you can verify the data:
```bash
python verify_database.py
```

This shows:
- Entity counts
- Route profitability
- Truck utilization
- Total cargo volume/weight

## Next Steps

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Start the API server:**
   ```bash
   python app/main.py
   ```

3. **View API documentation:**
   Open http://localhost:8000/docs

4. **Begin optimization:**
   - Match new orders to existing routes
   - Fill unused truck capacity
   - Convert losses to profits

## Business Context

Your company (Infinity and Beyond) has:
- **Problem**: 5 routes losing $388.15/day total
- **Solution**: Fill unused capacity with 3rd party orders
- **Goal**: Convert all routes to profitable
- **Constraint**: Must maintain 4-year binding contract

The DFM system helps you:
- Match incoming orders to existing routes
- Optimize truck utilization
- Calculate profitability improvements
- Maintain contract compliance

## File Structure

- `setup_dfm.py` - Complete setup automation with virtual environment
- `unified_db_init.py` - Main initialization script
- `verify_database.py` - Database verification
- `activate_venv.py` - Virtual environment helper
- `requirements.txt` - Python dependencies
- `venv/` - Virtual environment directory (created by setup)
- `app/database.py` - Database models
- `app/data_ingestion_service.py` - Data processing (legacy)
- `init_contract_data.py` - Contract-specific init (legacy)
- `simple_db_init.py` - Simple SQLite init (legacy)

The new unified approach replaces the multiple initialization scripts with a single, comprehensive solution that handles all the PDF data extraction and database setup within a virtual environment.

## Troubleshooting

### Virtual Environment Issues

If you encounter virtual environment issues:

1. **Delete and recreate:**
   ```bash
   # Remove existing venv
   rm -rf venv
   
   # Run setup again
   python setup_dfm.py
   ```

2. **Manual virtual environment creation:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python unified_db_init.py
   ```

### Permission Issues

On some systems, you may need to use `python3` instead of `python`:
```bash
python3 setup_dfm.py
```