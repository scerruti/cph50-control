#!/usr/bin/env python3
"""CPH50 charging automation for Fly.io"""

import os
import sys
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from python_chargepoint import ChargePoint
from python_chargepoint.exceptions import ChargePointCommunicationException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_alert(subject: str, body: str):
    """Send email alert via SMTP (MailChannels or your email provider)"""
    try:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        from_email = os.getenv("FROM_EMAIL")
        to_email = os.getenv("ALERT_EMAIL")
        
        if not all([smtp_host, smtp_user, smtp_pass, from_email, to_email]):
            logger.warning("Email not configured, skipping alert")
            return
        
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            logger.info(f"Alert sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")

def should_charge_now() -> bool:
    """Check if it's 6 AM in America/Los_Angeles timezone"""
    tz = ZoneInfo("America/Los_Angeles")
    now = datetime.now(tz)
    return now.hour == 6

def charge():
    """Authenticate to ChargePoint and start a session"""
    try:
        username = os.getenv("CP_USERNAME")
        password = os.getenv("CP_PASSWORD")
        station_id = int(os.getenv("CP_STATION_ID"))
        
        if not all([username, password, station_id]):
            raise ValueError("Missing CP_USERNAME, CP_PASSWORD, or CP_STATION_ID")
        
        logger.info(f"Logging in as {username}...")
        client = ChargePoint(username=username, password=password)
        logger.info(f"✓ Login successful (User ID: {client.user_id})")
        
        logger.info("Fetching home chargers...")
        chargers = client.get_home_chargers()
        logger.info(f"✓ Found {len(chargers)} chargers")
        
        if station_id not in chargers:
            raise ValueError(f"Station {station_id} not in home chargers: {chargers}")
        
        logger.info(f"Getting charger status for {station_id}...")
        status = client.get_home_charger_status(station_id)
        logger.info(f"✓ Charger status: plugged_in={status.plugged_in}, connected={status.connected}")
        
        if not status.plugged_in:
            msg = f"Charger {station_id} not plugged in. Cannot start charging."
            logger.warning(msg)
            send_alert("⚠️ CPH50 Charging Failed", msg)
            return False
        
        logger.info(f"Starting charging session on {station_id}...")
        session = client.start_charging_session(station_id)
        logger.info(f"✓ Charging started! Session ID: {session.session_id}")
        return True
    
    except ChargePointCommunicationException as e:
        msg = f"ChargePoint API error: {e}"
        logger.error(msg)
        send_alert("⚠️ URGENT: EV Charging Failed", msg)
        return False
    except Exception as e:
        msg = f"Unexpected error: {type(e).__name__}: {e}"
        logger.error(msg)
        send_alert("⚠️ URGENT: EV Charging Failed", msg)
        return False

if __name__ == "__main__":
    if should_charge_now():
        logger.info("6 AM detected. Starting charge cycle...")
        success = charge()
        sys.exit(0 if success else 1)
    else:
        now = datetime.now(ZoneInfo("America/Los_Angeles"))
        logger.info(f"Not 6 AM yet (current time: {now.strftime('%H:%M %Z')}). Exiting.")
        sys.exit(0)
