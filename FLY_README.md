# Fly.io CPH50 Charging Automation

Automatically start your ChargePoint Home Flex (CPH50) charging at 6 AM PST daily.

## Prerequisites

- Fly.io account (free tier available)
- ChargePoint account credentials
- Station ID (see setup below)
- Email for alerts (optional, requires SMTP config)

## Local Testing

Before deploying to Fly.io, test locally:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CP_USERNAME="your_username"
export CP_PASSWORD="your_password"
export CP_STATION_ID="12048111"
export ALERT_EMAIL="your_email@example.com"

# Run the script
python fly_charger.py
```

## Deployment to Fly.io

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly.io:**
   ```bash
   fly auth login
   ```

3. **Create app (if not already created):**
   ```bash
   fly apps create cph50-charger
   ```

4. **Set secrets:**
   ```bash
   fly secrets set CP_USERNAME="scerruti"
   fly secrets set CP_PASSWORD="your_password"
   fly secrets set CP_STATION_ID="12048111"
   fly secrets set ALERT_EMAIL="steve.cerruti@gmail.com"
   ```

5. **Optional: Configure email alerts** (using SendGrid, Gmail, or MailChannels):
   ```bash
   fly secrets set SMTP_HOST="smtp.sendgrid.net"
   fly secrets set SMTP_PORT="587"
   fly secrets set SMTP_USER="apikey"
   fly secrets set SMTP_PASS="your_sendgrid_api_key"
   fly secrets set FROM_EMAIL="noreply@yourdomain.com"
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

## How It Works

- **Cron Schedule:** Runs at 13:00 and 14:00 UTC daily (6 AM and 2 PM PST)
- **Time Check:** Script verifies it's actually 6 AM in America/Los_Angeles timezone
- **Charging Flow:**
  1. Logs in with CP_USERNAME / CP_PASSWORD
  2. Fetches home chargers
  3. Checks if vehicle is plugged in
  4. Starts charging session
  5. Sends alert email on failure
- **Failure Handling:** Retries are built into the python-chargepoint library

## Troubleshooting

Check logs:
```bash
fly logs
```

Run a manual test:
```bash
fly ssh console
python /app/fly_charger.py
```

Monitor the app:
```bash
fly status
```

## Important Notes

- **Vehicle must be plugged in** for charging to start
- **Secrets are encrypted** at rest and in transit on Fly.io
- **Free tier works** for this light cron job (~10 seconds/day)
- **Email is optional** — script continues even if email is not configured
