# Session Data

This directory contains charging session data collected for vehicle identification.

Each file is named `{session_id}.json` and contains:
- 30 samples of charging data collected over 5 minutes at 10-second intervals
- Power (kW), energy (kWh), duration, and status for each sample
- Statistics: average power, max power, min power, variance
- Vehicle labeling fields (to be filled later)

Files are automatically created by the `collect_session_data.py` script when triggered by session monitoring.
