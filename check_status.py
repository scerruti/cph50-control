#!/usr/bin/env python3
"""
Quick charger status check script
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from python_chargepoint import ChargePoint

print("=" * 60)
print("CPH50 Charger Status Check")
print(f"UTC Time: {datetime.now(ZoneInfo('UTC')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"PST Time: {datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
print("=" * 60)

username = "scerruti"
password = "4ndZ!^Vy?5NbNuT"

try:
    print(f"\n🔐 Authenticating as {username}...")
    client = ChargePoint(username=username, password=password)
    print("✓ Authentication successful\n")
    
    print("🔍 Fetching home chargers...")
    chargers = client.get_home_chargers()
    
    if not chargers:
        print("❌ No chargers found")
        exit(1)
    
    print(f"✓ Found {len(chargers)} charger(s)\n")
    
    for charger_id in chargers:
        print(f"📊 Charger ID: {charger_id}")
        print("-" * 60)
        
        status = client.get_home_charger_status(charger_id)
        
        print(f"  Model:          {status.model}")
        print(f"  Connected:      {status.connected} {'✅' if status.connected else '❌'}")
        print(f"  Plugged In:     {status.plugged_in} {'✅' if status.plugged_in else '❌'}")
        print(f"  Last Connected: {status.last_connected_at}")
        print(f"  Port Number:    {status.port_number}")
        print(f"  MAC Address:    {status.mac_address}")
        
        if hasattr(status, 'status'):
            print(f"  Status:         {status.status}")
        
        print()
        
        if status.connected and status.plugged_in:
            print("✅ Charger is READY to charge")
        elif status.connected and not status.plugged_in:
            print("⚠️  Charger is online but NO VEHICLE plugged in")
        elif not status.connected:
            print("❌ Charger is OFFLINE (not connected to network)")
            print("   → Restart charger (unplug 30 sec)")
            print("   → Check WiFi connection")
            print("   → Verify in ChargePoint app")
        
        print()
    
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
    exit(1)
