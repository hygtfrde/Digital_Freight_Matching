#!/usr/bin/env python3
"""
Demo script showing the hybrid CLI architecture
Shows both direct database and API modes working
"""

from data_service import create_data_service

def demo_both_modes():
    print("🚛 Digital Freight Matching - Hybrid Architecture Demo")
    print("=" * 60)
    
    # Test Direct Mode
    print("\n1️⃣ Testing DIRECT DATABASE Mode:")
    print("-" * 40)
    
    try:
        direct_service = create_data_service({'mode': 'direct'})
        health = direct_service.health_check()
        print(f"✅ Health Check: {health}")
        
        status = direct_service.get_system_status()
        print(f"📊 System Status Type: {type(status)}")
        print(f"📈 Total Routes: {status.total_routes}")
        print(f"🚛 Trucks: {status.trucks}")
        
    except Exception as e:
        print(f"❌ Direct mode error: {e}")
    
    # Test API Mode
    print("\n2️⃣ Testing API Mode:")
    print("-" * 40)
    
    try:
        api_service = create_data_service({
            'mode': 'api', 
            'api_url': 'http://localhost:8000'
        })
        health = api_service.health_check()
        print(f"✅ Health Check: {health}")
        
        status = api_service.get_system_status()
        print(f"📊 System Status Type: {type(status)}")
        print(f"🚛 Trucks: {status.get('trucks', 'N/A')}")
        print(f"📦 Orders: {status.get('orders', 'N/A')}")
        
        # Test CRUD operation
        trucks = api_service.get_all('trucks')
        print(f"🚛 Available trucks: {len(trucks)}")
        
    except Exception as e:
        print(f"❌ API mode error: {e}")
    
    # Configuration Demo
    print("\n3️⃣ Configuration Options:")
    print("-" * 40)
    print("CLI Usage Examples:")
    print("  python cli_dashboard.py --mode=direct")
    print("  python cli_dashboard.py --mode=api --api-url=http://localhost:8000")
    print("  python cli_dashboard.py --environment=production")
    
    print("\n_Environment Variables:")
    print("  export DFM_DATA_MODE=api")
    print("  export DFM_API_URL=http://api.company.com")
    
    print("\n_Config File: config/settings.yaml")
    print("  Supports development/production environment overrides")
    
    print("\n✨ Hybrid architecture successfully implemented!")

if __name__ == "__main__":
    demo_both_modes()