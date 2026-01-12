#!/usr/bin/env python3
"""
Classifier Tool: Batch classify ChargePoint sessions and update session_vehicle_map.json

Usage:
  python3 classifier_tool.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--min-confidence 0.9] [--update-map] [--label-unknown]

- Fetches sessions in the date range using the DAL
- Classifies each session
- Updates session_vehicle_map.json for high-confidence sessions
- Optionally marks low-confidence sessions as 'Unknown'
"""
import argparse
import os
import sys
import json
from datetime import datetime, timedelta
from chargepoint_dal import ChargePointDAL
from vehicle_classifier import VehicleClassifier
from threading import Lock

SESSION_MAP_PATH = "data/session_vehicle_map.json"
LOCK = Lock()


def parse_args():
    parser = argparse.ArgumentParser(description="Batch classify ChargePoint sessions.")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--min-confidence", type=float, default=0.9, help="Minimum confidence to update vehicle map")
    parser.add_argument("--update-map", action="store_true", help="Update session_vehicle_map.json")
    parser.add_argument("--label-unknown", action="store_true", help="Label low-confidence sessions as 'Unknown'")
    parser.add_argument("--username", required=True, help="ChargePoint username")
    parser.add_argument("--password", required=True, help="ChargePoint password")
    return parser.parse_args()


def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


def load_session_map():
    if not os.path.exists(SESSION_MAP_PATH):
        return {"sessions": {}, "unknown_sessions": [], "last_updated": None, "statistics": {}}
    with open(SESSION_MAP_PATH, "r") as f:
        return json.load(f)

def save_session_map(data):
    tmp_path = SESSION_MAP_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, SESSION_MAP_PATH)

def main():
    args = parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    dal = ChargePointDAL(args.username, args.password)
    classifier = VehicleClassifier()
    session_map = load_session_map()
    updated = False

    for single_date in daterange(start_date, end_date):
        year = single_date.year
        month = single_date.month
        print(f"Fetching sessions for {year}-{month:02d}")
        sessions = dal.get_sessions(year=year, month=month)
        for session in sessions:
            session_id = str(session.get("session_id") or session.get("sessionId"))
            if not session_id:
                continue
            # Fetch activity for classification
            activity = dal.get_session_activity(session_id)
            if not activity:
                print(f"  [!] No activity for session {session_id}")
                continue
            # Classify
            result = classifier.classify(activity)
            vehicle = result.get("vehicle")
            confidence = result.get("confidence", 0.0)
            print(f"  Session {session_id}: {vehicle} (confidence={confidence:.3f})")
            if confidence >= args.min_confidence:
                if args.update_map:
                    with LOCK:
                        session_map["sessions"][session_id] = {
                            "vehicle": vehicle,
                            "confidence": confidence,
                            "source": "classifier",
                            "labeled_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                        }
                        updated = True
            elif args.label_unknown:
                if args.update_map:
                    with LOCK:
                        session_map["sessions"][session_id] = {
                            "vehicle": "Unknown",
                            "confidence": confidence,
                            "source": "classifier",
                            "labeled_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                        }
                        if session_id not in session_map.get("unknown_sessions", []):
                            session_map.setdefault("unknown_sessions", []).append(session_id)
                        updated = True
    if updated and args.update_map:
        session_map["last_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        from datetime import timezone
        save_session_map(session_map)
        print("Session vehicle map updated.")
    else:
        print("No updates made to session vehicle map.")

if __name__ == "__main__":
    main()
