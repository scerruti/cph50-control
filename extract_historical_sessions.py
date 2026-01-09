#!/usr/bin/env python3
"""
Extract historical charging sessions from ChargePoint monthly activity endpoint
and fetch detailed power curve data to seed ML vehicle classifier.

Usage:
  1. Get monthly activity from ChargePoint web UI:
     fetch("https://mc.chargepoint.com/map-prod/v2", {
       body: '{"charging_activity_monthly":{"page_size":20,"show_address_for_home_sessions":true}}',
       credentials: "include"
     })
  
  2. Save response JSON to a file (e.g., monthly_activity.json)
  
  3. Run: python3 extract_historical_sessions.py <monthly_activity.json> <cookies_file>
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

import requests


def load_monthly_activity(filepath: str) -> dict:
    """Load monthly activity response from file."""
    with open(filepath, "r") as f:
        return json.load(f)


def load_cookies(cookies_file: str) -> dict:
    """Load cookies from file (from cp_cookies.txt)."""
    cookies = {}
    with open(cookies_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    cookies[key] = val
    return cookies


def fetch_session_details(
    session_id: int, cookies: dict, access_token: str
) -> Optional[dict]:
    """
    Fetch detailed power curve data for a session.
    
    Returns the charging_status response or None if failed.
    """
    url = "https://mc.chargepoint.com/map-prod/v2"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-requested-with": "XMLHttpRequest",
    }
    
    body = {
        "charging_status": {
            "mfhs": {},
            "session_id": session_id
        }
    }
    
    try:
        resp = requests.post(
            url,
            json=body,
            headers=headers,
            cookies=cookies,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        
        if "charging_status" in data:
            return data["charging_status"]
        else:
            print(f"  ✗ Session {session_id}: No charging_status in response")
            return None
            
    except requests.RequestException as e:
        print(f"  ✗ Session {session_id}: {e}")
        return None


def filter_full_charges(sessions: list, min_kwh: float = 40.0) -> list:
    """
    Filter sessions to likely full charges (exclude short top-ups).
    
    Args:
        sessions: List of session dicts from monthly activity
        min_kwh: Minimum energy threshold (default 40 kWh for full charges)
    
    Returns:
        Filtered list sorted by energy_kwh descending
    """
    full_charges = [
        s for s in sessions 
        if s.get("energy_kwh", 0) >= min_kwh
    ]
    return sorted(full_charges, key=lambda x: x["energy_kwh"], reverse=True)


def structure_session_data(charging_status: dict) -> dict:
    """
    Convert API charging_status response into standardized seed dataset format.
    """
    return {
        "session_id": charging_status["session_id"],
        "vehicle": {
            "make": charging_status["vehicle_info"]["make"],
            "model": charging_status["vehicle_info"]["model"],
            "year": charging_status["vehicle_info"]["year"],
            "vehicle_id": charging_status["vehicle_info"]["vehicle_id"],
            "battery_capacity": charging_status["vehicle_info"].get("battery_capacity"),
            "ev_range": charging_status["vehicle_info"].get("ev_range"),
        },
        "location": {
            "address": charging_status["address1"],
            "city": charging_status["city"],
            "state": charging_status["state_name"],
            "zipcode": charging_status["zipcode"],
            "lat": charging_status["lat"],
            "lon": charging_status["lon"],
        },
        "charger": {
            "device_id": charging_status["device_id"],
            "device_name": charging_status["device_name"],
            "port_level": charging_status["port_level"],
            "outlet_number": charging_status["outlet_number"],
            "is_home_charger": charging_status["is_home_charger"],
        },
        "session": {
            "start_time": charging_status["start_time"],
            "end_time": charging_status["end_time"],
            "session_time_ms": charging_status["session_time"],
            "charging_time_ms": charging_status["charging_time"],
            "current_charging": charging_status["current_charging"],
            "energy_kwh": charging_status["energy_kwh"],
            "energy_kwh_display": charging_status["energy_kwh_display"],
            "power_kw_display": charging_status["power_kw_display"],
            "miles_added": charging_status["miles_added"],
            "total_amount": charging_status["total_amount"],
            "payment_type": charging_status["payment_type"],
            "payment_completed": charging_status["payment_completed"],
            "currency": charging_status["currency_iso_code"],
        },
        "power_samples": [
            {
                "timestamp": sample["timestamp"],
                "energy_kwh": sample["energy_kwh"],
                "power_kw": sample["power_kw"],
            }
            for sample in charging_status.get("update_data", [])
        ],
        "data_source": "chargepoint_api_historical",
        "capture_date": time.strftime("%Y-%m-%d"),
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    monthly_file = sys.argv[1]
    cookies_file = sys.argv[2]
    max_sessions = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    # Load data
    print(f"📥 Loading monthly activity from {monthly_file}...")
    monthly = load_monthly_activity(monthly_file)
    
    print(f"🍪 Loading cookies from {cookies_file}...")
    cookies = load_cookies(cookies_file)
    
    # Aggregate all sessions from all months
    all_sessions = []
    for month_info in monthly.get("charging_activity_monthly", {}).get("month_info", []):
        all_sessions.extend(month_info.get("sessions", []))
    
    print(f"📊 Found {len(all_sessions)} total sessions across all months")
    
    # Filter to full charges
    full_charges = filter_full_charges(all_sessions, min_kwh=40.0)
    print(f"⚡ Found {len(full_charges)} full-charge sessions (≥40 kWh)")
    
    # Show top candidates
    print(f"\n🎯 Top {min(5, len(full_charges))} candidates by energy:")
    for i, session in enumerate(full_charges[:5], 1):
        print(
            f"  {i}. Session {session['session_id']}: "
            f"{session['energy_kwh']:.1f} kWh, {session['miles_added']:.1f} mi"
        )
    
    # Fetch detailed data for N sessions
    print(f"\n🔄 Fetching detailed data for {max_sessions} sessions...")
    sessions_dir = Path("/Users/scerruti/cph50 control/data/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    fetched = 0
    for session in full_charges[:max_sessions]:
        session_id = session["session_id"]
        print(f"\n  → Session {session_id}...")
        
        charging_status = fetch_session_details(session_id, cookies, "")
        if charging_status:
            # Structure and save
            structured = structure_session_data(charging_status)
            output_file = sessions_dir / f"{session_id}.json"
            
            with open(output_file, "w") as f:
                json.dump(structured, f, indent=2)
            
            print(f"    ✓ Saved to {output_file.relative_to('/')}")
            fetched += 1
        
        # Rate limit
        if fetched < max_sessions:
            time.sleep(1)
    
    print(f"\n✅ Successfully fetched {fetched}/{max_sessions} sessions")


if __name__ == "__main__":
    main()
