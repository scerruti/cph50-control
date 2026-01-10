#!/usr/bin/env python3
"""
Session Monitoring Script
Checks for new charging sessions every 10 minutes and triggers data collection.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from python_chargepoint import ChargePoint
from python_chargepoint.exceptions import ChargePointCommunicationException


def load_last_session():
    """Load the last known session ID from tracking file."""
    session_file = "data/last_session.json"
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            data = json.load(f)
            return data.get("session_id"), data.get("timestamp")
    return None, None


def save_current_session(session_id, status_info=None):
    """Save current session ID and metadata to tracking file."""
    session_file = "data/last_session.json"

    data = {
        "session_id": session_id,
        "timestamp": datetime.now(ZoneInfo('UTC')).isoformat(),
        "detected_at": datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z'),
        "power_kw": status_info.get("power_kw") if status_info else None,
        "energy_kwh": status_info.get("energy_kwh") if status_info else None,
        "duration_minutes": status_info.get("duration_minutes") if status_info else None,
        "vehicle_id": status_info.get("vehicle_id") if status_info else None,
        "vehicle_confidence": status_info.get("vehicle_confidence") if status_info else None,
        "status": status_info or {}
    }

    with open(session_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Commit to git
    try:
        subprocess.run(["git", "add", session_file], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Monitor: detected session {session_id}"], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        print(f"✓ Saved session {session_id} to tracking file")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not commit session tracking: {e}")


def trigger_data_collection(session_id):
    """Trigger the data collection workflow for this session."""
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("⚠️  Warning: No GITHUB_TOKEN, cannot trigger data collection workflow")
        return False
    
    # Use gh CLI to trigger workflow
    try:
        result = subprocess.run(
            ["gh", "workflow", "run", "Collect Session Data", 
             "--ref", "main",
             "-f", f"session_id={session_id}"],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "GH_TOKEN": github_token}
        )
        print(f"✓ Triggered data collection workflow for session {session_id}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not trigger data collection: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False


def monitor():
    """Check for new charging sessions and trigger data collection if found."""
    print("=" * 60)
    print("Charging Session Monitor")
    utc_time = datetime.now(ZoneInfo('UTC')).strftime('%Y-%m-%d %H:%M:%S %Z')
    local_time = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M:%S %Z')
    print(f"Check Time (UTC):  {utc_time}")
    print(f"Check Time (PT):   {local_time}")
    print("=" * 60)
    
    username = os.environ.get("CP_USERNAME")
    password = os.environ.get("CP_PASSWORD")
    
    if not all([username, password]):
        print("❌ ERROR: Missing CP_USERNAME or CP_PASSWORD")
        sys.exit(1)
    
    try:
        # Authenticate
        print(f"🔐 Authenticating as {username}...")
        client = ChargePoint(username=username, password=password)
        print("✓ Authentication successful")
        
        # Get charger status (online/plugged) for dashboard context
        print("🔍 Fetching home charger status...")
        charger_ids = client.get_home_chargers()
        charger_id = charger_ids[0] if charger_ids else None
        charger_status = None
        status_data = {}

        if charger_id:
            charger_status = client.get_home_charger_status(charger_id)
            status_data.update(
                {
                    "charger_id": charger_id,
                    "connected": getattr(charger_status, "connected", False),
                    "plugged_in": getattr(charger_status, "plugged_in", False),
                    "charging_status": getattr(charger_status, "charging_status", "UNKNOWN"),
                    "last_connected_at": getattr(charger_status, "last_connected_at", None).isoformat()
                    if getattr(charger_status, "last_connected_at", None)
                    else None,
                }
            )
            print(
                f"📡 Charger {charger_id} | Connected: {status_data['connected']} | Plugged: {status_data['plugged_in']} | State: {status_data['charging_status']}"
            )
        else:
            print("⚠️  No charger IDs returned; skipping charger status")

        # Get charging status
        print("🔍 Checking charging status...")
        status = client.get_user_charging_status()

        # Extract current session info
        current_session_id = None
        is_charging = False

        # Treat library's user status and home charger status together
        user_state = getattr(status, "state", None) if status else None
        if status and getattr(status, "session_id", 0):
            current_session_id = str(status.session_id)
            is_charging = True
        elif user_state == "in_use" or (status_data.get("charging_status") == "CHARGING"):
            # Charging detected but sessionId not yet available: retry until consistent
            print("⏳ Charging detected; waiting for session ID (eventual consistency)...")
            for attempt in range(1, 11):
                try:
                    sleep(2)
                except Exception:
                    pass
                status = client.get_user_charging_status()
                if status and getattr(status, "session_id", 0):
                    current_session_id = str(status.session_id)
                    is_charging = True
                    print(f"✓ Session ID acquired after {attempt*2}s: {current_session_id}")
                    break
            if not current_session_id:
                # Still charging but without sessionId; record charging state only
                is_charging = True
                print("⚠️  Charging without session ID (yet); will update snapshot and recheck next cycle")
        else:
            print("ℹ️  No active charging session")

        if is_charging:
            status_data.update({
                "session_id": current_session_id,
                "charging": True,
            })
            if current_session_id:
                print(f"📊 Active Session: {current_session_id}")
        
        # Load last known session
        last_session_id, last_timestamp = load_last_session()
        print(f"📁 Last Known Session: {last_session_id or 'None'}")
        
        # Detect new session
        if current_session_id and current_session_id != last_session_id:
            print("=" * 60)
            print(f"🆕 NEW SESSION DETECTED: {current_session_id}")
            print("=" * 60)
            
            # Save session
            save_current_session(current_session_id, status_data)
            
            # Trigger data collection
            trigger_data_collection(current_session_id)
            
        elif current_session_id == last_session_id:
            print(f"✓ Same session continuing: {current_session_id}")
            # Update current status for dashboard
            save_current_session(current_session_id, status_data)
        else:
            print("✓ No active session (vehicle not charging)")
            # Update dashboard with latest charger state
            save_current_session(None, status_data)
        
        print("=" * 60)
        print("✅ Session monitoring check complete")
        print("=" * 60)
        
    except ChargePointCommunicationException as e:
        print(f"❌ ERROR: ChargePoint API communication failed")
        print(f"   {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Unexpected error occurred")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    monitor()
