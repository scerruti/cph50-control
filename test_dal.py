#!/usr/bin/env python3
"""
Quick test for ChargePointDAL: fetch and print session IDs for the current month.
"""
import os
from datetime import datetime
from chargepoint_dal import ChargePointDAL

username = os.environ.get("CP_USERNAME")
password = os.environ.get("CP_PASSWORD")

if not username or not password:
    print("ERROR: CP_USERNAME and CP_PASSWORD must be set in the environment.")
    exit(1)

from datetime import timezone
dt = datetime.now(timezone.utc)
year = dt.year
month = dt.month

dal = ChargePointDAL(username, password, rate_limit=1, rate_period=60.0)
sessions = dal.get_sessions(year=year, month=month, max_batches=1, batch_size=20)

print(f"Fetched {len(sessions)} sessions for {year}-{month:02d}:")
for s in sessions:
    sid = s.get("session_id") or s.get("sessionId")
    print(f"  Session ID: {sid}")
