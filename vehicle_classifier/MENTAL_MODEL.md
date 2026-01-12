# Vehicle Classifier Library - Mental Model

## Overview

The `vehicle_classifier` library provides a complete workflow for vehicle classification and management.

## 1. Manage Vehicles

### 1.1 Manually (VehicleManager) ✅
- **CRUD operations** for vehicle metadata in `vehicle_config.json`
- Add/edit/delete vehicles
- Get display names and metadata
- **Status**: ✅ Implemented

### 1.2 Update Vehicle Characteristics by Training ⚠️
- Train classifier from session data
- Generate/update `classifier_summary.json` based on labeled sessions
- Update vehicle power characteristics from collected data
- **Status**: ⚠️ Partially implemented (exists in `train_vehicle_classifier.py` but not in library)

## 2. Maintain session_vehicle_map.json

The session_vehicle_map is the **source of truth** for which vehicle was used in each charging session.

### 2.1 Manual Labeling ⚠️
- Add/edit/remove session labels
- Mark sessions as unknown
- Override classifier predictions
- **Status**: ⚠️ Not yet in library (exists in `collect_session_data.py` as `update_session_vehicle_map()`)

### 2.2 Batch Processing Sessions (with ChargePoint Data) 📋
- Retrieve usage data from ChargePoint (Project 3 integration)
- Process multiple sessions at once
- Classify sessions from historical data
- Update session_vehicle_map in batch
- **Status**: 📋 Planned (will use Project 3 data retrieval)

### 2.3 Real-time Classification of Current Session ✅
- Classify active charging session from power samples
- Update session_vehicle_map automatically
- Return vehicle_id and confidence
- **Status**: ✅ Implemented (`VehicleClassifier.predict()`)

## Current Library Status

### ✅ Implemented
- `VehicleClassifier`: Real-time classification
- `VehicleManager`: Vehicle CRUD operations

### ⚠️ Needs to be Added
- `SessionLabelManager`: Manage session_vehicle_map.json (manual labeling, batch operations)
- `ClassifierTrainer`: Train/retrain classifier from session data (update classifier_summary.json)

### 📋 Integration Points
- Project 3 (ChargePoint Data Cache) will provide batch processing capabilities
- Desktop tool will use all components for training/labeling/classification UI

## Data Flow

```
Training Workflow:
session_data (JSON files) 
  → ClassifierTrainer 
  → classifier_summary.json (updated)
  → VehicleClassifier (uses updated stats)

Classification Workflow:
power_samples (real-time)
  → VehicleClassifier.predict()
  → (vehicle_id, confidence)
  → SessionLabelManager.update()
  → session_vehicle_map.json

Manual Labeling Workflow:
user selects vehicle for session
  → SessionLabelManager.label_session()
  → session_vehicle_map.json (updated)
```
