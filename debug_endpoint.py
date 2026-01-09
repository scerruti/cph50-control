#!/usr/bin/env python3
"""
Debug script to show which endpoint is being used
"""
import logging
from python_chargepoint import ChargePoint

# Enable debug logging to see endpoints
logging.basicConfig(level=logging.DEBUG)

username = "scerruti"
password = "4ndZ!^Vy?5NbNuT"

print("Attempting to discover region endpoint...")
try:
    client = ChargePoint(username=username, password=password)
    print(f"\n✓ Authentication successful")
    print(f"Region: {client.global_config.region}")
    print(f"Accounts Endpoint: {client.global_config.endpoints.accounts}")
    print(f"User ID: {client.user_id}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nThis is likely a rate limit / captcha block.")
    print("GitHub Actions will use different IPs and should work.")
