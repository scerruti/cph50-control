#!/usr/bin/env python3
"""
Fetch complete ChargePoint session data and cache locally for history display.

Usage: python fetch_session_details.py <session_id>

This script:
1. Authenticates with ChargePoint
2. Fetches complete session data via ChargePoint API
3. Merges vehicle classification from data/sessions/{date}/{id}.json
4. Saves to data/session_cache/YYYY-MM.json (organized by month)
5. Git commits the monthly cache file

The cached monthly files contain an array of session objects with:
- Vehicle info (name, model, VIN)
- Location/charger info
- Session metrics (energy, duration, cost)
- Utility data (rate plan, grid info)
- Vehicle classification (vehicle_id, confidence from ML)

This allows the history.html page to display comprehensive charging data
without making repeated ChargePoint API calls. Monthly organization allows
efficient loading of month/year views.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

try:
    from chargepoint.client import ChargePoint
except ImportError:
    print("ERROR: python-chargepoint library not found")
    print("Install with: pip install python-chargepoint")
    sys.exit(1)


def fetch_session_details(session_id):
    """
    Fetch full ChargePoint session data and cache locally in monthly JSON files.
    
    Args:
        session_id (str): ChargePoint session ID
        
    Returns:
        dict: Session data with vehicle classification merged in
    """
    
    # Get credentials from environment
    username = os.getenv('CP_USERNAME')
    password = os.getenv('CP_PASSWORD')
    
    if not username or not password:
        print("ERROR: CP_USERNAME and CP_PASSWORD environment variables required")
        sys.exit(1)
    
    print(f"[fetch_session_details] Fetching session {session_id}...")
    
    try:
        # Authenticate with ChargePoint
        client = ChargePoint(username=username, password=password)
        
        # Fetch the session
        session_obj = client.get_charging_session(session_id)
        
        # Extract session start time for organizing by month
        session_start = datetime.fromisoformat(session_obj.session_start_time.isoformat())
        year = session_start.year
        month = session_start.month
        
        # Convert session object to dictionary with nested structures
        session_dict = {
            "session_id": session_id,
            "session_start_time": session_obj.session_start_time.isoformat(),
            "session_end_time": session_obj.session_end_time.isoformat() if session_obj.session_end_time else None,
            
            # Vehicle information
            "vehicle": {
                "vehicle_id": getattr(session_obj.vehicle, 'vehicle_id', None),
                "vehicle_name": getattr(session_obj.vehicle, 'vehicle_name', None),
                "model": getattr(session_obj.vehicle, 'model', None),
                "vin": getattr(session_obj.vehicle, 'vin', None),
                "make": getattr(session_obj.vehicle, 'make', None)
            },
            
            # Location information
            "location": {
                "location_id": getattr(session_obj.location, 'location_id', None),
                "name": getattr(session_obj.location, 'name', None),
                "address": getattr(session_obj.location, 'address', None),
                "city": getattr(session_obj.location, 'city', None),
                "state": getattr(session_obj.location, 'state', None),
                "zip_code": getattr(session_obj.location, 'zip_code', None)
            },
            
            # Charger information
            "charger": {
                "charger_id": getattr(session_obj.charger, 'charger_id', None),
                "connector_type": getattr(session_obj.charger, 'connector_type', None),
                "charger_model": getattr(session_obj.charger, 'charger_model', None),
                "level": getattr(session_obj.charger, 'level', None)
            },
            
            # Session metrics
            "session": {
                "energy_kwh": float(session_obj.energy_kwh) if session_obj.energy_kwh else None,
                "duration_seconds": int(session_obj.duration_seconds) if session_obj.duration_seconds else None,
                "cost": float(session_obj.cost) if session_obj.cost else None,
                "peak_power_kw": float(session_obj.peak_power_kw) if session_obj.peak_power_kw else None,
                "status": session_obj.status
            },
            
            # Utility information
            "utility": {
                "utility_name": getattr(session_obj.utility, 'utility_name', None),
                "utility_company": getattr(session_obj.utility, 'utility_company', None) if hasattr(session_obj, 'utility') else None
            }
        }
        
        # Try to merge vehicle classification from collection data
        # Classification files are organized by date: data/sessions/YYYY/MM/DD/{session_id}.json
        # Try multiple possible date paths (session might span dates)
        for date_offset in range(-1, 2):  # Try day before, same day, day after
            possible_date = session_start + timedelta(days=date_offset)
            classification_path = f"data/sessions/{possible_date.year:04d}/{possible_date.month:02d}/{possible_date.day:02d}/{session_id}.json"
            
            if os.path.exists(classification_path):
                print(f"[fetch_session_details] Merging classification from {classification_path}")
                with open(classification_path, 'r') as f:
                    classification_data = json.load(f)
                    if "vehicle_id" in classification_data:
                        session_dict["vehicle_id"] = classification_data["vehicle_id"]
                    if "vehicle_confidence" in classification_data:
                        session_dict["vehicle_confidence"] = classification_data["vehicle_confidence"]
                break
        
        # Organize cache by month: data/session_cache/YYYY-MM.json
        cache_dir = f"data/session_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = f"{cache_dir}/{year:04d}-{month:02d}.json"
        
        # Read existing sessions for this month
        sessions = []
        if os.path.exists(cache_file):
            print(f"[fetch_session_details] Loading existing {cache_file}")
            with open(cache_file, 'r') as f:
                sessions = json.load(f)
        
        # Check if session already exists (avoid duplicates)
        existing_index = next((i for i, s in enumerate(sessions) if s["session_id"] == session_id), None)
        
        if existing_index is not None:
            print(f"[fetch_session_details] Updating existing session at index {existing_index}")
            sessions[existing_index] = session_dict
        else:
            print(f"[fetch_session_details] Adding new session to {cache_file}")
            sessions.append(session_dict)
        
        # Write atomically: write to temp file, then rename
        temp_file = f"{cache_file}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        os.rename(temp_file, cache_file)
        print(f"[fetch_session_details] Saved {len(sessions)} sessions to {cache_file}")
        
        # Git commit
        try:
            subprocess.run(["git", "add", cache_file], cwd=".", check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Cache: {len(sessions)} sessions for {year:04d}-{month:02d}"],
                cwd=".",
                check=True
            )
            print(f"[fetch_session_details] Committed to git")
        except subprocess.CalledProcessError as e:
            print(f"[fetch_session_details] WARNING: Git commit failed: {e}")
            # Don't fail the entire operation if git fails
        
        return session_dict
        
    except Exception as e:
        print(f"ERROR: Failed to fetch session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_session_details.py <session_id>")
        print("Example: python fetch_session_details.py abc123xyz")
        sys.exit(1)
    
    session_id = sys.argv[1]
    result = fetch_session_details(session_id)
    print(json.dumps(result, indent=2))
