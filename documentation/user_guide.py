"""
User Guide Generator

Generates comprehensive user documentation including installation,
setup, operation, and troubleshooting.
"""

from pathlib import Path


class UserGuideGenerator:
    """Generates user-focused documentation"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def generate(self) -> str:
        """Generate user guide"""
        content = """# Digital Freight Matching System - User Guide

## Overview

The Digital Freight Matching (DFM) system optimizes logistics operations by converting unprofitable truck routes into profitable ones through intelligent order matching.

### Business Problem
- **Infinity and Beyond** logistics has 5 contract routes losing $388.15/day total
- Need to fill unused truck capacity with third-party orders
- Goal: Convert all routes from losses to profits

## Installation

### Prerequisites
- Python 3.8+
- 4GB RAM (8GB recommended)
- 1GB free disk space

### Setup Steps
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\\Scripts\\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python db_manager.py init

# 4. Verify installation
python db_manager.py status
```

## Quick Start

### Option 1: Interactive CLI (Recommended)
```bash
python cli_menu_app/main.py
```
Follow the menu prompts to explore the system.

### Option 2: API Server
```bash
# Start server
python app/main.py

# Access at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Option 3: Direct Commands
```bash
# Check system status
python db_manager.py status

# Run validation
python validation/business_validator.py
```

## System Operation

### Key Entities

#### Trucks
- 5 trucks with 48m³ capacity each
- Weight limit: 9,180 lbs per truck
- Range: 750-900 km depending on truck

#### Routes (Contract - Must Preserve)
1. Atlanta → Ringgold: -$53.51/day
2. Atlanta → Augusta: -$50.12/day
3. Atlanta → Savannah: -$131.40/day
4. Atlanta → Albany: -$96.43/day
5. Atlanta → Columbus: -$56.69/day

#### Orders
- Freight requests with pickup/delivery locations
- Must meet proximity (≤1km), capacity, time (≤10h), and compatibility constraints

### Business Rules

#### Order Validation
- **Proximity**: Pickup/delivery within 1km of route path
- **Capacity**: Total cargo fits in truck (48m³, 9180 lbs)
- **Time**: Route completion within 10 hours including stops
- **Compatibility**: Cargo types must be compatible (no hazmat + fragile)

#### Profitability Optimization
- Add revenue-generating orders to existing routes
- Maximize truck capacity utilization
- Minimize route deviations and costs
- Maintain service quality standards

## Common Operations

### Creating Orders
```bash
# Via CLI
python cli_menu_app/main.py
# Select: Manage Orders → Create New Order

# Via API
curl -X POST http://localhost:8000/orders \\
  -H "Content-Type: application/json" \\
  -d '{
    "location_origin_id": 1,
    "location_destiny_id": 2,
    "client_id": 1
  }'
```

### Checking System Status
```bash
# Database status
python db_manager.py status

# Business validation
python validation/business_validator.py

# Performance metrics
python performance/performance_assessor.py
```

### Analytics and Reporting
```bash
# System analytics via API
curl http://localhost:8000/analytics/summary

# Expected metrics:
# - Daily P&L: Currently -$388.15
# - Truck utilization: Target >80%
# - Order match rate: Target >90%
```

## Troubleshooting

### Common Issues

#### "Database not found"
```bash
# Solution: Initialize database
source venv/bin/activate
python db_manager.py init
```

#### "Import errors"
```bash
# Solution: Check virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

#### "Orders not matching routes"
- Verify locations are within 1km of route path
- Check truck capacity isn't exceeded
- Ensure cargo types are compatible
- Confirm route time stays under 10 hours

#### "API server not responding"
```bash
# Check if running
curl http://localhost:8000/

# Restart if needed
python app/main.py
```

### Performance Issues
- Order processing should complete in <5 seconds
- If slow, check system resources and database integrity
- Run: `python db_manager.py verify`

### Getting Help
- Check logs for error messages
- Run system validation: `python tests/integration/test_integration_suite.py`
- Review API docs: `http://localhost:8000/docs`
- Verify expected system state matches installation guide

## Expected System State

After proper setup:
- **Clients**: 2 (Too-Big-To-Fail Company + Example Client)
- **Locations**: 16+ (Georgia cities + order locations)
- **Trucks**: 5 (48m³ capacity each)
- **Routes**: 5 (Atlanta to contract destinations)
- **Orders**: 10+ (Contract + example orders)
- **Daily Loss**: -$388.15 total

## Performance Expectations
- Order processing: <5 seconds per order
- Database operations: <1 second for queries
- API responses: <500ms for standard endpoints
- Memory usage: <500MB normal operations
"""
        
        file_path = self.output_dir / "user-guide.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)