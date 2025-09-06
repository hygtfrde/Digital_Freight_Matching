#!/usr/bin/env python3
"""
Demo script for Business Requirements Validation Framework

This script demonstrates the business validator in action with sample data
that represents the Digital Freight Matching system scenarios.
"""

from datetime import datetime
from validation.business_validator import BusinessValidator, ValidationStatus
from schemas.schemas import Order, Route, Truck, Location, Cargo, Package, CargoType


def create_sample_data():
    """Create sample data for demonstration"""
    
    # Create sample locations (Georgia cities from business requirements)
    atlanta = Location(lat=33.7490, lng=-84.3880)
    ringgold = Location(lat=34.9161, lng=-85.1094)
    augusta = Location(lat=33.4735, lng=-82.0105)
    savannah = Location(lat=32.0835, lng=-81.0998)
    albany = Location(lat=31.5804, lng=-84.1557)
    columbus = Location(lat=32.4609, lng=-84.9877)
    
    # Create 5 contract routes (as per business requirements)
    routes = [
        Route(
            id=1,
            location_origin_id=1,
            location_destiny_id=2,
            location_origin=atlanta,
            location_destiny=ringgold,
            path=[atlanta, ringgold],
            profitability=25.0,  # Improved from original -$53.51 loss
            orders=[]
        ),
        Route(
            id=2,
            location_origin_id=1,
            location_destiny_id=3,
            location_origin=atlanta,
            location_destiny=augusta,
            path=[atlanta, augusta],
            profitability=30.0,  # Improved from original -$50.12 loss
            orders=[]
        ),
        Route(
            id=3,
            location_origin_id=1,
            location_destiny_id=4,
            location_origin=atlanta,
            location_destiny=savannah,
            path=[atlanta, savannah],
            profitability=75.0,  # Improved from original -$131.40 loss
            orders=[]
        ),
        Route(
            id=4,
            location_origin_id=1,
            location_destiny_id=5,
            location_origin=atlanta,
            location_destiny=albany,
            path=[atlanta, albany],
            profitability=50.0,  # Improved from original -$96.43 loss
            orders=[]
        ),
        Route(
            id=5,
            location_origin_id=1,
            location_destiny_id=6,
            location_origin=atlanta,
            location_destiny=columbus,
            path=[atlanta, columbus],
            profitability=40.0,  # Improved from original -$56.69 loss
            orders=[]
        )
    ]
    
    # Create sample trucks with proper capacity limits
    trucks = [
        Truck(
            id=1,
            autonomy=800.0,
            capacity=48.0,  # Within 48m³ limit
            type="standard",
            cargo_loads=[]
        ),
        Truck(
            id=2,
            autonomy=800.0,
            capacity=45.0,  # Within limit
            type="refrigerated",
            cargo_loads=[]
        ),
        Truck(
            id=3,
            autonomy=800.0,
            capacity=47.0,  # Within limit
            type="standard",
            cargo_loads=[]
        )
    ]
    
    # Create sample orders with various compliance scenarios
    orders = []
    
    # Compliant order - within 1km of route
    nearby_pickup = Location(lat=33.7500, lng=-84.3890)  # ~1km from Atlanta
    nearby_dropoff = Location(lat=34.9170, lng=-85.1100)  # ~1km from Ringgold
    
    compliant_package = Package(
        id=1,
        volume=2.0,  # Within capacity
        weight=100.0,  # ~220 lbs - within weight limit
        type=CargoType.STANDARD
    )
    
    compliant_cargo = Cargo(
        id=1,
        order_id=1,
        packages=[compliant_package]
    )
    
    compliant_order = Order(
        id=1,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=nearby_pickup,
        location_destiny=nearby_dropoff,
        cargo=[compliant_cargo]
    )
    orders.append(compliant_order)
    
    # Non-compliant order - too far from route
    far_pickup = Location(lat=30.0000, lng=-80.0000)  # Very far from any route
    far_dropoff = Location(lat=35.0000, lng=-90.0000)  # Very far from any route
    
    non_compliant_order = Order(
        id=2,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=far_pickup,
        location_destiny=far_dropoff,
        cargo=[compliant_cargo]
    )
    orders.append(non_compliant_order)
    
    # Oversized order - exceeds capacity
    oversized_package = Package(
        id=2,
        volume=50.0,  # Exceeds 48m³ limit
        weight=1000.0,
        type=CargoType.STANDARD
    )
    
    oversized_cargo = Cargo(
        id=2,
        order_id=3,
        packages=[oversized_package]
    )
    
    oversized_order = Order(
        id=3,
        location_origin_id=1,
        location_destiny_id=2,
        location_origin=nearby_pickup,
        location_destiny=nearby_dropoff,
        cargo=[oversized_cargo]
    )
    orders.append(oversized_order)
    
    return orders, routes, trucks


def print_validation_report(report):
    """Print a formatted validation report"""
    status_symbol = {
        ValidationStatus.PASSED: "✅",
        ValidationStatus.WARNING: "⚠️",
        ValidationStatus.FAILED: "❌",
        ValidationStatus.NOT_TESTED: "⏸️"
    }
    
    print(f"\n{status_symbol[report.status]} Requirement {report.requirement_id}: {report.requirement_description}")
    print(f"   Status: {report.status.value.upper()}")
    print(f"   Details: {report.details}")
    
    if report.metrics:
        print("   Key Metrics:")
        for key, value in report.metrics.items():
            if isinstance(value, float):
                print(f"     • {key}: {value:.2f}")
            else:
                print(f"     • {key}: {value}")
    
    if report.recommendations:
        print("   Recommendations:")
        for rec in report.recommendations:
            print(f"     • {rec}")


def main():
    """Main demonstration function"""
    print("=" * 80)
    print("DIGITAL FREIGHT MATCHING - BUSINESS REQUIREMENTS VALIDATION")
    print("=" * 80)
    
    # Create sample data
    print("\n📊 Creating sample data...")
    orders, routes, trucks = create_sample_data()
    
    print(f"   • {len(orders)} sample orders created")
    print(f"   • {len(routes)} contract routes created")
    print(f"   • {len(trucks)} trucks created")
    
    # Initialize validator
    print("\n🔍 Initializing Business Validator...")
    validator = BusinessValidator()
    
    # Run all validations
    print("\n🧪 Running Business Requirements Validation...")
    reports = validator.validate_all_requirements(
        orders=orders,
        routes=routes,
        trucks=trucks,
        baseline_daily_loss=388.15  # Original daily loss from business requirements
    )
    
    # Print individual reports
    print("\n📋 VALIDATION RESULTS:")
    print("-" * 60)
    
    for report in reports:
        print_validation_report(report)
    
    # Generate and print summary
    print("\n📊 SUMMARY REPORT:")
    print("-" * 60)
    
    summary = validator.generate_summary_report(reports)
    
    print(f"\n_Overall Status: {summary['overall_status']}")
    print(f"Total Requirements: {summary['total_requirements']}")
    print(f"Passed: {summary['passed_count']}")
    print(f"Failed: {summary['failed_count']}")
    print(f"Warnings: {summary['warning_count']}")
    print(f"Pass Rate: {summary['pass_rate_percent']:.1f}%")
    
    # Business impact analysis
    print("\n💰 BUSINESS IMPACT ANALYSIS:")
    print("-" * 60)
    
    profitability_report = reports[0]  # First report is profitability
    if profitability_report.metrics:
        baseline_loss = profitability_report.metrics.get('baseline_daily_loss', 0)
        current_profit = profitability_report.metrics.get('current_daily_profit', 0)
        improvement = profitability_report.metrics.get('improvement_amount', 0)
        
        print(f"Original Daily Loss: ${baseline_loss:.2f}")
        print(f"Current Daily Result: ${current_profit:.2f}")
        print(f"Total Improvement: ${improvement:.2f}")
        
        if current_profit > 0:
            print(f"🎉 SUCCESS: System converted losses into ${current_profit:.2f} daily profit!")
        elif improvement > 0:
            print(f"📈 PROGRESS: System reduced daily losses by ${improvement:.2f}")
        else:
            print(f"⚠️  CONCERN: System has not yet improved profitability")
    
    # Compliance summary
    print("\n📋 COMPLIANCE SUMMARY:")
    print("-" * 60)
    
    for report in reports:
        status_icon = "✅" if report.status == ValidationStatus.PASSED else "❌" if report.status == ValidationStatus.FAILED else "⚠️"
        print(f"{status_icon} Requirement {report.requirement_id}: {report.status.value}")
    
    print(f"\n🕒 Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()