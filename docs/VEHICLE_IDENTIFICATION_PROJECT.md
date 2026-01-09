# Vehicle Identification Project

## Overview
Automatically identify which vehicle is charging based on power consumption patterns during the first 5 minutes of each charging session. Enable per-vehicle reporting and analytics.

---

## Problem Statement
Multiple vehicles use the same ChargePoint CPH50 charger. Currently, there's no way to automatically distinguish which vehicle is charging in a given session, making it impossible to:
- Track charging history per vehicle
- Calculate cost per vehicle
- Identify charging patterns by vehicle
- Generate vehicle-specific reports

---

## Solution Approach
Collect power consumption data during the first 5 minutes of each charging session and use machine learning/data analysis to identify unique charging signatures per vehicle.

### Key Insight
Different vehicles have distinct charging profiles:
- **Initial power draw patterns** (ramp-up behavior)
- **Steady-state consumption levels** (kW range)
- **Power variance** (how stable the draw is)
- **Battery management system behavior** (negotiation with charger)

---

## Architecture

### Phase 1: Data Collection (Weeks 1-4)
**Goal:** Collect 5-minute charging profiles from multiple sessions

```
┌─────────────────────────────────────────────────────────┐
│  Polling Workflow (every 10 min)                        │
│  - Check get_user_charging_status()                     │
│  - Detect new session_id                                │
│  - Trigger data collection                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────┐
│  Data Collection Script                                 │
│  - Poll session every 10 seconds for 5 minutes          │
│  - Capture: timestamp, energy_kwh, power_kw             │
│  - Store in data/sessions/<session_id>.json             │
└────────────────┬────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────┐
│  Session Data Schema                                    │
│  {                                                      │
│    "session_id": 123456,                               │
│    "start_time": "2026-01-10T06:00:00Z",               │
│    "device_id": 12048111,                              │
│    "samples": [                                        │
│      {"elapsed_sec": 0, "power_kw": 3.7, ...},         │
│      {"elapsed_sec": 10, "power_kw": 7.2, ...},        │
│      ...                                               │
│    ],                                                  │
│    "vehicle_id": null  // Labeled later                │
│  }                                                     │
└─────────────────────────────────────────────────────────┘
```

### Phase 2: Manual Labeling (Concurrent with Phase 1)
**Goal:** Create training dataset with known vehicle labels

- Users manually label sessions via:
  - GitHub issue comments
  - Simple web form
  - File annotation
- Store labels in `data/vehicle_labels.json`:
  ```json
  {
    "vehicles": {
      "vehicle_a": {"name": "Tesla Model 3", "sessions": [123, 456]},
      "vehicle_b": {"name": "Nissan Leaf", "sessions": [789]}
    }
  }
  ```

### Phase 3: Feature Engineering & Analysis (Week 5-6)
**Goal:** Extract distinguishing features from charging profiles

**Features to Extract:**
1. **Initial Power Draw**
   - First 30 seconds average power
   - Peak power in first minute
   - Ramp-up rate (kW/second)

2. **Steady-State Characteristics**
   - Average power (1-5 minutes)
   - Power variance/standard deviation
   - Number of power level changes

3. **Pattern Recognition**
   - FFT analysis (frequency domain)
   - Power draw slope changes
   - Plateau detection

4. **Statistical Features**
   - Min/max/median power
   - 25th/75th percentile
   - Power draw histogram

### Phase 4: Model Training (Week 7-8)
**Goal:** Build classification model

**Approach Options:**

1. **Simple Rule-Based (MVP)**
   - If average power 1.4-2.0 kW → Vehicle A (Prius Prime)
   - If average power 7.0-8.0 kW → Vehicle B (Tesla)
   - Fast to implement, works for distinct vehicles

2. **Machine Learning Models**
   - **Decision Tree** (interpretable)
   - **Random Forest** (robust to noise)
   - **Gradient Boosting** (highest accuracy)
   - **Neural Network** (if large dataset)

3. **Clustering (Unsupervised)**
   - K-means on features
   - DBSCAN for outlier detection
   - Useful if vehicles not pre-labeled

**Training Process:**
```python
# Pseudo-code
sessions = load_labeled_sessions()
features = extract_features(sessions)
X = feature_matrix(features)
y = vehicle_labels(sessions)

model = RandomForestClassifier()
model.fit(X, y)
save_model('data/vehicle_classifier.pkl')
```

### Phase 5: Production Classification (Week 9+)
**Goal:** Auto-classify new sessions in real-time

```
New Session Detected
    ↓
Collect 5-min data
    ↓
Extract features
    ↓
Load model → Predict vehicle
    ↓
Update data/runs.json with vehicle_id
    ↓
Dashboard shows per-vehicle stats
```

---

## Implementation Plan

### Week 1-2: Session Monitoring Infrastructure
- [ ] Create `monitor-sessions.yml` workflow (runs every 10 min)
- [ ] Create `monitor_sessions.py` script
  - Check `get_user_charging_status()`
  - Detect new `session_id` (compare to `data/last_session.json`)
  - Trigger data collection workflow on new session
- [ ] Create `data/last_session.json` to track current session
- [ ] Test: Manually start charging, verify detection

### Week 3-4: Data Collection Implementation
- [ ] Create `collect_session_data.yml` workflow (triggered by monitor)
- [ ] Create `collect_session_data.py` script
  - Poll `get_charging_session(session_id)` every 10 seconds
  - Collect 30 samples over 5 minutes
  - Extract: `timestamp`, `energy_kwh`, `power_kw`
  - Save to `data/sessions/<session_id>.json`
- [ ] Create `data/sessions/` directory
- [ ] Add error handling for interrupted sessions
- [ ] Test: Collect data from 3-5 sessions per vehicle

### Week 5: Manual Labeling System
- [ ] Create `data/vehicle_labels.json` schema
- [ ] Create simple labeling workflow:
  - GitHub issue template for labeling
  - OR: Simple HTML form in `docs/label.html`
- [ ] Label 5-10 sessions per vehicle (minimum)
- [ ] Document vehicle characteristics

### Week 6: Feature Engineering
- [ ] Create `analyze_sessions.py` script
- [ ] Implement feature extraction functions:
  - `extract_initial_power_features()`
  - `extract_steady_state_features()`
  - `extract_statistical_features()`
- [ ] Visualize features per vehicle (matplotlib)
- [ ] Identify most discriminative features
- [ ] Generate exploratory analysis report

### Week 7-8: Model Development
- [ ] Set up Python ML environment (scikit-learn, pandas)
- [ ] Create `train_classifier.py` script
- [ ] Implement train/test split (80/20)
- [ ] Train multiple models (Decision Tree, Random Forest, GBM)
- [ ] Evaluate accuracy, precision, recall
- [ ] Select best model
- [ ] Save model to `data/vehicle_classifier.pkl`
- [ ] Document model performance

### Week 9: Production Integration
- [ ] Create `classify_vehicle.py` script
- [ ] Modify `collect_session_data.py` to auto-classify after collection
- [ ] Update `data/runs.json` schema to include `vehicle_id`
- [ ] Update dashboard to filter by vehicle
- [ ] Add vehicle selection dropdown to dashboard
- [ ] Test end-to-end: new session → classification → dashboard

### Week 10+: Refinement & Monitoring
- [ ] Monitor classification accuracy
- [ ] Collect misclassified examples
- [ ] Retrain model periodically
- [ ] Add confidence scores to predictions
- [ ] Alert on low-confidence classifications
- [ ] Implement active learning (manual review of uncertain cases)

---

## Data Structures

### `data/last_session.json`
```json
{
  "session_id": 123456,
  "last_checked": "2026-01-10T06:15:00Z",
  "status": "active"
}
```

### `data/sessions/<session_id>.json`
```json
{
  "session_id": 123456,
  "start_time": "2026-01-10T06:00:00Z",
  "device_id": 12048111,
  "device_name": "CP HOME",
  "collection_start": "2026-01-10T06:00:15Z",
  "collection_end": "2026-01-10T06:05:15Z",
  "samples": [
    {
      "elapsed_sec": 0,
      "timestamp": "2026-01-10T06:00:15Z",
      "energy_kwh": 0.001,
      "power_kw": 3.72
    },
    {
      "elapsed_sec": 10,
      "timestamp": "2026-01-10T06:00:25Z",
      "energy_kwh": 0.012,
      "power_kw": 7.15
    }
  ],
  "features": {
    "initial_power_avg": 3.8,
    "steady_state_power_avg": 7.2,
    "power_variance": 0.15,
    "ramp_up_rate": 0.34
  },
  "vehicle_id": null,
  "vehicle_confidence": null,
  "manually_labeled": false
}
```

### `data/vehicle_labels.json`
```json
{
  "vehicles": {
    "prius_prime_2023": {
      "name": "2023 Toyota Prius Prime",
      "nickname": "Prius",
      "max_charge_rate_kw": 3.3,
      "battery_capacity_kwh": 13.6,
      "sessions": [123456, 123789, 124001],
      "characteristics": "Low power draw, very stable, ramps slowly"
    },
    "tesla_model3_2021": {
      "name": "2021 Tesla Model 3 LR",
      "nickname": "Tesla",
      "max_charge_rate_kw": 11.5,
      "battery_capacity_kwh": 82,
      "sessions": [123567, 123890],
      "characteristics": "High power draw, moderate variance, fast ramp"
    }
  },
  "unknown_sessions": [124500, 124600]
}
```

### Updated `data/runs.json`
```json
{
  "runs": [
    {
      "run_id": "20858601605",
      "date": "2026-01-10",
      "time_utc": "13:00:00",
      "time_pt": "05:00:00",
      "result": "success",
      "start_time_pt": "06:00:15",
      "session_id": 123456,
      "vehicle_id": "prius_prime_2023",
      "vehicle_confidence": 0.95,
      "reason": "Charging session started successfully"
    }
  ]
}
```

---

## Technology Stack

### Data Collection
- **Python 3.12** (existing)
- **python-chargepoint** library (existing)
- **GitHub Actions** workflows (existing)

### Data Analysis & ML
- **pandas** - Data manipulation
- **numpy** - Numerical operations
- **scikit-learn** - Machine learning models
- **matplotlib/seaborn** - Visualization
- **pickle** - Model serialization

### Storage
- **JSON files** - Simple, version-controllable
- **Git LFS** (optional) - For large session datasets

---

## Success Metrics

### Phase 1 (Data Collection)
- ✅ Collect 10+ sessions per vehicle
- ✅ Data quality: <5% failed collections
- ✅ Average 30 samples per 5-minute window

### Phase 2 (Labeling)
- ✅ 100% of training sessions labeled
- ✅ At least 2 distinct vehicles identified

### Phase 3-4 (Model Training)
- ✅ Model accuracy >90% on test set
- ✅ Precision & recall >85% per vehicle
- ✅ Training completes in <5 minutes

### Phase 5 (Production)
- ✅ Auto-classification latency <10 seconds
- ✅ Classification runs without manual intervention
- ✅ Dashboard displays per-vehicle metrics

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Insufficient training data** | Model won't generalize | Collect 20+ sessions per vehicle |
| **Vehicles too similar** | Low accuracy | Focus on distinct vehicles initially |
| **Session interrupted** | Incomplete data | Handle gracefully, mark as invalid |
| **API rate limits** | Data collection fails | Add backoff, cache responses |
| **Model drift over time** | Accuracy degrades | Monitor, retrain quarterly |
| **Battery conditioning affects profile** | Misclassification | Collect diverse seasonal data |

---

## Future Enhancements

### V2: Advanced Features
- Real-time classification (stream data instead of batch)
- Multi-vehicle detection (if both vehicles charge same day)
- Anomaly detection (unusual charging patterns)
- Predictive maintenance (detect charger issues)

### V3: Integration
- Mobile app integration
- Push notifications per vehicle
- Cost tracking per vehicle
- Export to spreadsheet

### V4: Community
- Share anonymized models
- Crowdsource vehicle profiles
- Build public vehicle signature database

---

## Getting Started

### Immediate Next Steps
1. **Review & approve this plan**
2. **Set up monitoring workflow** (Week 1 deliverable)
3. **Trigger first data collection**
4. **Label 2-3 sessions manually** to validate approach

### Quick Win (Week 1)
Implement session monitoring to start seeing when charging happens, even without classification.

---

## Questions to Resolve

1. **How many vehicles** do you have? (Need at least 2 for meaningful classification)
2. **Typical charging frequency** per vehicle? (Affects data collection timeline)
3. **Preference for labeling method**? (GitHub issues, web form, or direct file edit)
4. **Dashboard priorities**? (Total cost per vehicle, kWh per vehicle, session count, etc.)
5. **ML preference**? (Simple rules vs full ML model - depends on complexity)

---

## Resources Required

- **GitHub Actions minutes**: ~50 min/month (10 min polling, 5 min data collection per session)
- **Storage**: ~1 MB per session × 60 sessions/month = ~60 MB/month
- **Development time**: ~20 hours over 10 weeks (2 hrs/week)

---

*Document Version: 1.0*  
*Created: January 9, 2026*  
*Owner: @scerruti*  
*Repository: [cph50-control](https://github.com/scerruti/cph50-control)*
