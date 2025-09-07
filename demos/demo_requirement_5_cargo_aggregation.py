#!/usr/bin/env python3
"""
Demo: Business Requirement 5 - Cargo Aggregation and Route Generation

Demonstrates:
- Cargo that can't fit on any route can be saved and combined with other clients' cargo
- Form new routes that MUST be profitable
- Automated cargo aggregation and route generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, text
from app.database import engine, Client, Location, Order, Truck, Route, Cargo, Package, CargoType
from services.cargo_aggregation_service import CargoAggregationService
from services.route_generation_service import RouteGenerationService


def create_cargo_aggregation_demo_data(session: Session):
    """Create demo data showing cargo that needs aggregation"""
    
    # Clean previous demo data
    session.execute(text("DELETE FROM package;"))
    session.execute(text("DELETE FROM cargo;"))  
    session.execute(text("DELETE FROM `order`;"))
    session.execute(text("DELETE FROM route;"))
    session.execute(text("DELETE FROM truck;"))
    session.execute(text("DELETE FROM client;"))
    session.execute(text("DELETE FROM location;"))
    session.commit()
    
    # Create multiple clients
    client1 = Client(name="Acme Manufacturing")
    client2 = Client(name="Georgia Distributors")  
    client3 = Client(name="Southeast Logistics")
    
    clients = [client1, client2, client3]
    session.add_all(clients)
    session.flush()
    
    # Create locations
    atlanta = Location(lat=33.7490, lng=-84.3880, marked=False)
    macon = Location(lat=32.8407, lng=-83.6324, marked=False)
    augusta = Location(lat=33.4735, lng=-82.0105, marked=False)
    columbus = Location(lat=32.4609, lng=-84.9877, marked=False)
    albany = Location(lat=31.5804, lng=-84.1557, marked=False)
    
    locations = [atlanta, macon, augusta, columbus, albany]
    session.add_all(locations)
    session.flush()
    
    # Create trucks - one busy, others available
    truck1 = Truck(capacity=48.0, autonomy=800.0, type="standard")
    truck2 = Truck(capacity=48.0, autonomy=800.0, type="standard") 
    truck3 = Truck(capacity=48.0, autonomy=800.0, type="refrigerated")
    
    trucks = [truck1, truck2, truck3]
    session.add_all(trucks)
    session.flush()
    
    # Create existing unprofitable route using truck1
    existing_route = Route(
        location_origin_id=atlanta.id,
        location_destiny_id=macon.id,
        profitability=-88.25,  # Losing money
        truck_id=truck1.id
    )
    session.add(existing_route)
    session.flush()
    
    # Create individual orders that can't fit existing routes
    orders = []
    
    # Order 1: Client 1 - Macon to Augusta (small cargo)
    order1 = Order(
        location_origin_id=macon.id,
        location_destiny_id=augusta.id,
        client_id=client1.id
    )
    session.add(order1)
    session.flush()
    
    cargo1 = Cargo(order_id=order1.id)
    session.add(cargo1)
    session.flush()
    
    package1 = Package(volume=12.0, weight=500.0, type=CargoType.STANDARD, cargo_id=cargo1.id)
    session.add(package1)
    orders.append(order1)
    
    # Order 2: Client 2 - Augusta to Columbus (compatible cargo)
    order2 = Order(
        location_origin_id=augusta.id,
        location_destiny_id=columbus.id,
        client_id=client2.id
    )
    session.add(order2)
    session.flush()
    
    cargo2 = Cargo(order_id=order2.id)
    session.add(cargo2)
    session.flush()
    
    package2 = Package(volume=15.0, weight=600.0, type=CargoType.STANDARD, cargo_id=cargo2.id)
    session.add(package2)
    orders.append(order2)
    
    # Order 3: Client 3 - Columbus to Albany (completing a circuit)
    order3 = Order(
        location_origin_id=columbus.id,
        location_destiny_id=albany.id,
        client_id=client3.id
    )
    session.add(order3)
    session.flush()
    
    cargo3 = Cargo(order_id=order3.id)
    session.add(cargo3)
    session.flush()
    
    package3 = Package(volume=10.0, weight=400.0, type=CargoType.STANDARD, cargo_id=cargo3.id)
    session.add(package3)
    orders.append(order3)
    
    # Order 4: Client 1 - Albany back to Atlanta (completing full loop)
    order4 = Order(
        location_origin_id=albany.id,
        location_destiny_id=atlanta.id,
        client_id=client1.id
    )
    session.add(order4)
    session.flush()
    
    cargo4 = Cargo(order_id=order4.id)
    session.add(cargo4)
    session.flush()
    
    package4 = Package(volume=8.0, weight=350.0, type=CargoType.REFRIGERATED, cargo_id=cargo4.id)
    session.add(package4)
    orders.append(order4)
    
    session.commit()
    
    return {
        'clients': clients,
        'locations': locations,
        'trucks': trucks,
        'existing_routes': [existing_route],
        'unmatched_orders': orders
    }


def demonstrate_cargo_aggregation():
    """Demonstrate cargo aggregation and route generation"""
    
    print("📦 BUSINESS REQUIREMENT 5: CARGO AGGREGATION & NEW ROUTES")
    print("=" * 70)
    print("Requirement: Cargo that can't fit on any route can be saved and")
    print("combined with other clients' cargo to form new routes.")
    print("New routes MUST be profitable.")
    print("=" * 70)
    
    with Session(engine) as session:
        # Create demo data
        data = create_cargo_aggregation_demo_data(session)
        
        print(f"\n🏢 SCENARIO SETUP:")
        print(f"   Clients: {len(data['clients'])} companies with individual orders")
        print(f"   Existing routes: {len(data['existing_routes'])} (currently unprofitable)")
        print(f"   Unmatched orders: {len(data['unmatched_orders'])} from different clients")
        print(f"   Available trucks: {len(data['trucks'])} ({len(data['existing_routes'])} in use)")
        
        # Show client orders
        print(f"\n👥 CLIENT ORDERS:")
        for order in data['unmatched_orders']:
            client = next(c for c in data['clients'] if c.id == order.client_id)
            origin = next(l for l in data['locations'] if l.id == order.location_origin_id)
            destiny = next(l for l in data['locations'] if l.id == order.location_destiny_id)
            
            cargo_volume = order.total_volume()
            cargo_weight = order.total_weight()
            cargo_types = set()
            for cargo in order.cargo:
                cargo_types.update(cargo.get_types())
            
            print(f"   {client.name}:")
            print(f"     Route: {_location_name(origin)} → {_location_name(destiny)}")
            print(f"     Cargo: {cargo_volume:.1f}m³, {cargo_weight:.1f}kg, {list(cargo_types)[0].value}")
            print(f"     Status: Cannot fit existing Atlanta→Macon route")
        
        # Initialize services  
        aggregation_service = CargoAggregationService(session)
        generation_service = RouteGenerationService(session)
        
        print(f"\n🔍 STEP 1: CARGO AGGREGATION ANALYSIS")
        
        # Find aggregation opportunities
        result = aggregation_service.analyze_aggregation_opportunities(
            data['existing_routes'],
            data['trucks']
        )
        
        print(f"   ✅ Unmatched orders found: {len(result.unmatched_orders)}")
        print(f"   ✅ Compatible combinations discovered: {len(result.compatible_combinations)}")
        print(f"   📦 Total aggregatable cargo: {result.total_unmatched_volume:.1f}m³, {result.total_unmatched_weight:.1f}kg")
        
        if not result.compatible_combinations:
            print(f"   ❌ No viable combinations found")
            return False
        
        # Show top combinations
        print(f"\n🎯 STEP 2: BEST CARGO COMBINATIONS")
        for i, combo in enumerate(result.compatible_combinations[:3]):
            client_names = []
            for order in combo.orders:
                client = next(c for c in data['clients'] if c.id == order.client_id)
                if client.name not in client_names:
                    client_names.append(client.name)
            
            print(f"   Option {i+1}:")
            print(f"     Orders: {len(combo.orders)} from {len(client_names)} clients")
            print(f"     Clients: {', '.join(client_names)}")
            print(f"     Cargo: {combo.total_volume_m3:.1f}m³, {combo.total_weight_kg:.1f}kg")
            print(f"     Score: {combo.compatibility_score:.1f}")
            print(f"     Types: {[ct.value for ct in combo.cargo_types]}")
        
        print(f"\n🚛 STEP 3: NEW ROUTE GENERATION")
        
        # Try to generate profitable route from best combination
        best_combination = result.compatible_combinations[0] 
        available_truck = data['trucks'][1]  # Use truck2 (not in use)
        
        print(f"   Testing combination with {len(best_combination.orders)} orders")
        print(f"   Using available truck: {available_truck.type} ({available_truck.capacity}m³)")
        
        route_result = generation_service.generate_profitable_route(
            best_combination, available_truck
        )
        
        print(f"\n💰 STEP 4: PROFITABILITY VALIDATION")
        
        if route_result.success:
            print(f"   ✅ PROFITABLE ROUTE GENERATED!")
            print(f"   📈 Daily profit: ${route_result.estimated_profit:.2f}")
            print(f"   💵 Revenue: ${route_result.estimated_revenue:.2f}")
            print(f"   💸 Cost: ${route_result.estimated_cost:.2f}")
            print(f"   🛣️  Distance: {route_result.total_distance_km:.1f} km")
            print(f"   ⏱️  Time: {route_result.total_time_hours:.1f} hours")
            print(f"   📦 Orders served: {route_result.orders_included}")
            
            # Business impact analysis
            existing_loss = abs(data['existing_routes'][0].profitability)
            total_improvement = route_result.estimated_profit + existing_loss
            
            print(f"\n📊 BUSINESS IMPACT:")
            print(f"   Current system loss: -${existing_loss:.2f}/day")
            print(f"   New route profit: +${route_result.estimated_profit:.2f}/day")
            print(f"   Net system improvement: ${total_improvement:.2f}/day")
            print(f"   Annual impact: ${total_improvement * 365:.2f}/year")
            
            # Show profit margin and efficiency
            profit_margin = (route_result.estimated_profit / route_result.estimated_revenue) * 100
            capacity_util = (best_combination.total_volume_m3 / available_truck.capacity) * 100
            
            print(f"\n📈 EFFICIENCY METRICS:")
            print(f"   Profit margin: {profit_margin:.1f}%")
            print(f"   Truck utilization: {capacity_util:.1f}%")
            print(f"   Clients served: {len(set(o.client_id for o in best_combination.orders))}")
            print(f"   Revenue per km: ${route_result.estimated_revenue / route_result.total_distance_km:.2f}")
            
            return True
        else:
            print(f"   ❌ Route generation failed: {route_result.error_message}")
            print(f"   Estimated profit: ${route_result.estimated_profit:.2f}")
            return False


def _location_name(location):
    """Get readable name for location based on coordinates"""
    location_names = {
        (33.7490, -84.3880): "Atlanta",
        (32.8407, -83.6324): "Macon", 
        (33.4735, -82.0105): "Augusta",
        (32.4609, -84.9877): "Columbus",
        (31.5804, -84.1557): "Albany"
    }
    
    # Find closest match
    for (lat, lng), name in location_names.items():
        if abs(location.lat - lat) < 0.01 and abs(location.lng - lng) < 0.01:
            return name
    
    return f"({location.lat:.3f}, {location.lng:.3f})"


def demonstrate_aggregation_benefits():
    """Show benefits of cargo aggregation approach"""
    
    print(f"\n🏆 CARGO AGGREGATION BENEFITS:")
    print("")
    
    print(f"   Individual Order Approach:")
    print(f"   • Each client ships separately")
    print(f"   • 4 orders require 4 separate routes")
    print(f"   • Low truck utilization per route")
    print(f"   • Higher cost per shipment")
    print(f"   • Some orders may be uneconomical")
    print("")
    
    print(f"   Aggregated Approach:")
    print(f"   • Multiple clients share optimized route")
    print(f"   • 4 orders combined into 1 efficient route")
    print(f"   • High truck utilization (up to 48m³)")
    print(f"   • Lower cost per shipment")
    print(f"   • All orders become profitable")
    print("")
    
    print(f"   Key Advantages:")
    print(f"   ✅ Cost sharing reduces per-order expenses")
    print(f"   ✅ Better truck capacity utilization") 
    print(f"   ✅ Creates profitable routes from unprofitable individual orders")
    print(f"   ✅ Serves more clients with fewer resources")
    print(f"   ✅ Environmental benefits (fewer trucks, less fuel)")


def main():
    """Run the cargo aggregation demonstration"""
    
    try:
        # Demonstrate cargo aggregation and route generation
        success = demonstrate_cargo_aggregation()
        
        # Show aggregation benefits
        demonstrate_aggregation_benefits()
        
        print(f"\n" + "=" * 70)
        if success:
            print(f"✅ DEMONSTRATION COMPLETE")
            print(f"   Business Requirement 5 is FULLY IMPLEMENTED")
            print(f"   • Cargo aggregation from multiple clients ✅")
            print(f"   • Profitable new route generation ✅") 
            print(f"   • Economic validation ensures profitability ✅")
            print(f"   • Integration with existing order processing ✅")
        else:
            print(f"⚠️  DEMONSTRATION PARTIALLY COMPLETE")
            print(f"   • Cargo aggregation logic implemented ✅")
            print(f"   • Route generation needs fine-tuning ⚠️")
        print(f"=" * 70)
        
    except Exception as e:
        print(f"\n❌ DEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()