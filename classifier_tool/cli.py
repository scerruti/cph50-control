#!/usr/bin/env python3
"""
CLI entry point for classifier_tool
"""
import argparse
from .core import batch_classify_sessions

def main():
    parser = argparse.ArgumentParser(description="Batch classify ChargePoint sessions.")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--min-confidence", type=float, default=0.9, help="Minimum confidence to update vehicle map")
    parser.add_argument("--update-map", action="store_true", help="Update session_vehicle_map.json")
    parser.add_argument("--label-unknown", action="store_true", help="Label low-confidence sessions as 'Unknown'")
    parser.add_argument("--username", required=True, help="ChargePoint username")
    parser.add_argument("--password", required=True, help="ChargePoint password")
    args = parser.parse_args()
    batch_classify_sessions(args)

if __name__ == "__main__":
    main()
