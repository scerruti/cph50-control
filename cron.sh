#!/bin/bash
# Run the charger script at 6 AM PST, with fallback to 2 PM PST (handles DST transitions)

# Install crond if not present
apt-get update && apt-get install -y supercronic

# Create crontab: 6 AM and 2 PM PST (13:00 and 14:00 UTC, adjusted for DST)
cat > /tmp/crontab << 'EOF'
0 13 * * * python /app/fly_charger.py
0 14 * * * python /app/fly_charger.py
EOF

exec supercronic /tmp/crontab
