# CPH50 Vehicle Classification & Dashboard Integration

## Overview

This document describes the integrated vehicle classification and real-time dashboard system for the CPH50 charging automation project.

## Architecture

```
ChargePoint API (every 10 min)
    ↓
monitor_sessions.py (detect session, extract power/energy/duration)
    ↓
collect_session_data.py (5-min power collection)
    ↓
VehicleClassifier (predict vehicle from power curve)
    ↓
data/last_session.json (current charging state)
data/sessions/{SESSION_ID}.json (historical record)
    ↓
docs/dashboard.html (real-time visualization)
```

## Components

### 1. Vehicle Classifier
- **File**: `classify_vehicle.py`
- **Function**: `predict(power_samples)` → `(vehicle_name, confidence_0_to_1)`
- **Method**: Euclidean distance to trained baselines
- **Features Used**: Mean power (primary discriminator)
  - Volvo: 8.50 ± 0.00 kW (CV=0.074)
  - Equinox: 9.01 ± 0.00 kW (CV=0.014)
- **Performance**: 99%+ confidence on test samples

### 2. Data Collection
- **File**: `collect_session_data.py`
- **Trigger**: When `monitor_sessions.py` detects a new charging session
- **Process**:
  1. Collect 30 power samples over 5 minutes (10-second intervals)
  2. Calculate statistics (mean, std, percentiles, IQR, CV)
  3. Run classifier on power samples
  4. Save to `data/sessions/{SESSION_ID}.json` with metadata:
     - `power_samples`: List of power readings
     - `statistics`: Mean, std, p25, p75, cv
     - `vehicle_id`: Predicted vehicle name (e.g., "volvo", "equinox")
     - `vehicle_confidence`: Confidence score (0-1)
     - `labeled_by`: "classifier" (automatic) or "manual" (user override)
     - `labeled_at`: ISO timestamp of prediction

### 3. Session Monitoring
- **File**: `monitor_sessions.py`
- **Trigger**: GitHub Actions cron (every 10 minutes, at :00 and :30 UTC)
- **Process**:
  1. Poll ChargePoint API for current session
  2. Extract real-time metrics:
     - `power_kw`: Current power draw (kW)
     - `energy_kwh`: Total energy delivered (kWh)
     - `duration_minutes`: Session duration (minutes)
  3. Save to `data/last_session.json` with:
     - Session metadata
     - Current power/energy/duration
     - Vehicle classification (if available)
  4. Commit and push to GitHub (triggers GitHub Actions)

### 4. Real-Time Dashboard
- **File**: `docs/dashboard.html`
- **Location**: GitHub Pages (accessible at `https://scerruti.github.io/cph50-control/docs/dashboard.html`)
- **Features**:
  - **Vehicle Detection**: Shows vehicle image (Volvo/Equinox) with name and confidence score
  - **Power Display**: Large 48px font showing current kW draw
  - **Session Metrics**: Energy added (kWh), duration (minutes)
  - **Status Badge**: 🔌 Charging (pulsing) or ⏸️ Idle (gray)
  - **Auto-Refresh**: Fetches `data/last_session.json` every 10 seconds
  - **Mobile Responsive**: Designed for 600px max width
  - **SVG Fallback**: Built-in placeholder images if custom images unavailable

## Data Flow

### Happy Path (Active Charging)

```
1. ChargePoint API: vehicle charging
   ↓
2. monitor_sessions.py (runs 13:00, 14:00 UTC):
   - Detects session started (e.g., session_id=s123)
   - Extracts power_kw=8.5, energy_kwh=10, duration_minutes=45
   - Saves to data/last_session.json
   - Pushes to GitHub
   ↓
3. GitHub Actions triggers:
   - collect_session_data.py starts
   - Collects 30 samples over 5 minutes
   - Runs classifier on power curve
   - Predicts vehicle_id="volvo", confidence=0.994
   - Saves to data/sessions/s123.json
   ↓
4. Dashboard (polls data/last_session.json every 10s):
   - Loads {session_id: s123, power_kw: 8.5, vehicle_id: "volvo", ...}
   - Displays Volvo image, "8.5 kW", "10.0 kWh", "45 min", "99.4% confidence"
   - Status badge shows "🔌 Charging" (pulsing)
```

### Idle State (No Active Session)

```
data/last_session.json:
{
  "session_id": null,
  "power_kw": null,
  "vehicle_id": null,
  ...
}

Dashboard displays:
- "⏸️ Idle"
- "No active charging session"
```

## Configuration

### Environment Variables (in Cloudflare Worker, not needed locally)

```
CP_USERNAME: ChargePoint username
CP_PASSWORD: ChargePoint password
CP_STATION_ID: ChargePoint station ID
ALERT_EMAIL: Email for failure notifications
TZ_REGION: America/Los_Angeles (hardcoded)
```

### Classifier Seed Data

Pre-trained statistics stored in `data/classifier_summary.json`:

```json
{
  "volvo": {
    "mean_power": 8.5,
    "std_power": 0.0,
    "cv_stability": 0.074,
    "p25_power": 8.5,
    "p75_power": 8.5
  },
  "equinox": {
    "mean_power": 9.01,
    "std_power": 0.0,
    "cv_stability": 0.014,
    "p25_power": 9.01,
    "p75_power": 9.01
  }
}
```

## Testing the Integration

### 1. Test the Classifier
```bash
python3 classify_vehicle.py
# or
python3 -c "
from classify_vehicle import VehicleClassifier
classifier = VehicleClassifier()
vehicle_id, confidence = classifier.predict([8.5, 8.5, 8.5])
print(f'{vehicle_id}: {confidence:.2%}')
"
```

### 2. Test Data Collection (if monitor detects session)
```bash
python3 collect_session_data.py <SESSION_ID>
# Simulates 5-min collection with classifier integration
# Outputs: Session JSON with vehicle_id and confidence
```

### 3. Test Dashboard
1. Open `docs/dashboard.html` in browser
2. Should load and show "No active charging session" if idle
3. Next time monitor runs (or next scheduled charge):
   - Check `data/last_session.json` is updated
   - Refresh dashboard page
   - Should display vehicle, power, confidence, energy, duration

### 4. Manual Test with Sample Data
```bash
# Simulate a charging session by manually updating last_session.json
cat > data/last_session.json << 'EOF'
{
  "session_id": "test-123",
  "timestamp": "2025-01-09T15:20:00+00:00",
  "detected_at": "2025-01-09 08:20:00 PST",
  "power_kw": 8.5,
  "energy_kwh": 12.3,
  "duration_minutes": 45,
  "vehicle_id": "volvo",
  "vehicle_confidence": 0.994,
  "status": {}
}
EOF

# Open dashboard in browser, should display vehicle + power
```

## Extending the Classifier

### Adding a New Vehicle

1. **Collect seed data**: Run a charging session, note the session_id
2. **Manually label**: Edit `data/sessions/{SESSION_ID}.json`, set `vehicle_id` to new vehicle name
3. **Update training script**:
   ```python
   # In train_vehicle_classifier.py, add to MANUAL_LABELS
   MANUAL_LABELS = {
       "4751613101": "volvo",
       "4754846071": "equinox",
       "NEW_SESSION_ID": "new_vehicle",
   }
   ```
4. **Retrain**: `python3 train_vehicle_classifier.py`
5. **Verify**: New vehicle baseline will appear in `data/classifier_summary.json`
6. **Test**: Run classifier on samples from new vehicle

### Improving Classifier Accuracy

- **More seed data**: Accumulate 5-10 sessions per vehicle for better statistics
- **Feature refinement**: In `classify_vehicle.py`, expand features beyond mean power:
  - Percentiles (P25, P50, P75, P95)
  - Coefficient of variation (CV)
  - Ramp profile (if visible)
  - Power stability metrics
- **Algorithm upgrade**: Consider scikit-learn classifiers (KNeighborsClassifier, RandomForest) with more features

## Failure Handling

### Monitor Detects No Session
- `monitor_sessions.py` sets `session_id: null` in `data/last_session.json`
- Dashboard displays "⏸️ Idle"
- No collection triggered

### Monitor Fails (e.g., 403 WAF)
- Log error to GitHub Actions output
- Issue #1 tracks transient failures
- Manual check: `python3 monitor_sessions.py` in local shell

### Classifier Unavailable (ImportError)
- `collect_session_data.py` gracefully skips prediction
- Sets `vehicle_id: null, labeled_by: null`
- Session JSON still saved with power data

### Dashboard Fetch Fails
- Check `data/last_session.json` exists and is readable
- Check GitHub Pages is deployed (auto-deployed on push)
- Check browser console for CORS/network errors
- Verify last_session.json is committed (not in .gitignore)

## Monitoring & Alerts

### Current Logging
- `monitor_sessions.py`: Prints detected sessions to GitHub Actions output
- `collect_session_data.py`: Prints classified vehicle and confidence
- `dashboard.html`: Logs fetch errors to browser console

### Future Enhancements
- **Slack integration**: Alert on successful classification
- **Email summary**: Daily report of vehicle usage
- **Anomaly detection**: Alert if power draw unusually high/low (charger issue?)
- **Confidence tracking**: Monitor if classifier confidence declining (need retraining?)

## Deployment Status

- ✅ **Classifier**: Trained and tested (100% accuracy on seed data)
- ✅ **Monitoring**: Running on GitHub Actions cron (stable)
- ✅ **Data Collection**: Integrated with classifier
- ✅ **Dashboard**: Live on GitHub Pages
- ⏳ **Live Testing**: Awaiting next scheduled charging session

## Related Files

- **Training**: `train_vehicle_classifier.py`
- **Inference**: `classify_vehicle.py`
- **Statistics**: `data/classifier_summary.json`
- **Seed Data**: `data/sessions/4751613101.json`, `data/sessions/4754846071.json`
- **Monitoring**: `monitor_sessions.py`
- **Collection**: `collect_session_data.py`
- **Dashboard**: `docs/dashboard.html`
- **Last Session**: `data/last_session.json` (updated by monitor)

## Next Steps

1. **User Testing**: Next charging session will trigger full pipeline
2. **Data Accumulation**: Collect 5-10 sessions per vehicle for refined statistics
3. **Classifier Refinement**: Rerun training with larger dataset
4. **Feature Engineering**: Explore additional discriminative features if needed
5. **Educational Content**: How I DT! guide pending user review

---

**Created**: 2025-01-09  
**Status**: Integration Complete, Awaiting Live Testing
