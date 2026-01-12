# Vehicle Classifier

EV Vehicle Classification Library - Classify electric vehicles based on charging power curve analysis.

Includes vehicle configuration management for training, labeling, and classification workflows.

## Installation

```bash
pip install -e .
```

Or for production use (once published):
```bash
pip install vehicle-classifier
```

## Usage

### Vehicle Classification

```python
from vehicle_classifier import VehicleClassifier

# Initialize with classifier summary file
classifier = VehicleClassifier("data/classifier_summary.json")

# Predict vehicle from power samples (kW)
power_samples = [8.5, 8.6, 8.7, 9.0, 9.01, 9.02]
vehicle_id, confidence = classifier.predict(power_samples)

print(f"Predicted: {vehicle_id} (confidence: {confidence:.1%})")
```

### Vehicle Configuration Management

```python
from vehicle_classifier import VehicleManager

# Initialize vehicle manager
manager = VehicleManager("data/vehicle_config.json")

# Get all vehicles
vehicles = manager.get_all_vehicles()

# Get a specific vehicle
vehicle = manager.get_vehicle("serenity_equinox_2024")
print(vehicle["nickname"])  # "Serenity"

# Add a new vehicle
manager.add_vehicle(
    vehicle_id="tesla_model_3_2023",
    nickname="Tesla",
    make="Tesla",
    model="Model 3",
    year=2023,
    battery_capacity_kwh=75,
    max_charge_rate_kw=11.5,
    efficiency_mi_per_kwh=4.2,
    paint_color="Pearl White",
    paint_color_hex="#FFFFFF",
    display_color="White"
)
manager.save()

# Update vehicle
manager.update_vehicle("tesla_model_3_2023", efficiency_mi_per_kwh=4.5)
manager.save()

# Get display name
name = manager.get_display_name("serenity_equinox_2024")  # "Serenity"

# Validate consistency with classifier summary
missing = manager.validate_vehicle_ids(classifier_summary)
if missing:
    print(f"Warning: Classifier has vehicles not in config: {missing}")
```

### Session Labeling

```python
from vehicle_classifier import SessionLabelManager

# Initialize label manager
label_manager = SessionLabelManager("data/session_vehicle_map.json")

# Label a session manually
label_manager.label_session(
    session_id="4751613101",
    vehicle_id="serenity_equinox_2024",
    source="manual"
)
label_manager.save()

# Label from classifier prediction
vehicle_id, confidence = classifier.predict(power_samples)
label_manager.label_session(
    session_id="4751613102",
    vehicle_id=vehicle_id,
    confidence=confidence,
    source="classifier"
)
label_manager.save()

# Get label for a session
label = label_manager.get_label("4751613101")
print(f"Vehicle: {label['vehicle']}, Confidence: {label['confidence']}")

# Get unknown sessions (need labeling)
unknown = label_manager.get_unknown_sessions()

# Get sessions by vehicle
volvo_sessions = label_manager.get_sessions_by_vehicle("volvo_xc40_2021")

# Batch label multiple sessions
labels = [
    ("4751613103", "serenity_equinox_2024", None, "manual"),
    ("4751613104", "volvo_xc40_2021", None, "manual"),
]
label_manager.batch_label(labels)
label_manager.save()
```

### Training the Classifier

```python
from vehicle_classifier import ClassifierTrainer, SessionLabelManager

# Initialize trainer
label_manager = SessionLabelManager("data/session_vehicle_map.json")
trainer = ClassifierTrainer(
    sessions_dir="data/sessions",
    label_manager=label_manager
)

# Train from labeled sessions
result = trainer.train_from_labeled_sessions(
    output_file="data/classifier_summary.json"
)

print(f"Processed: {result['processed']} sessions")
print(f"Skipped: {result['skipped']} sessions")
print(f"Vehicles: {result['vehicles']}")
```

### Integration Example

```python
from vehicle_classifier import (
    VehicleClassifier, VehicleManager, SessionLabelManager
)

# Load all components
classifier = VehicleClassifier("data/classifier_summary.json")
vehicle_manager = VehicleManager("data/vehicle_config.json")
label_manager = SessionLabelManager("data/session_vehicle_map.json")

# Classify a session
power_samples = [9.0, 9.01, 9.02, 9.0, 9.01]
vehicle_id, confidence = classifier.predict(power_samples)

# Save classification to session map
label_manager.label_session(
    session_id="4751613105",
    vehicle_id=vehicle_id,
    confidence=confidence,
    source="classifier"
)
label_manager.save()

# Get display information
if vehicle_id:
    vehicle = vehicle_manager.get_vehicle(vehicle_id)
    print(f"Vehicle: {vehicle['nickname']}")
    print(f"Make/Model: {vehicle['make']} {vehicle['model']}")
    print(f"Confidence: {confidence:.1%}")
```

## Features

### VehicleClassifier
- Statistical classification based on mean power and stability metrics
- Robust to partial captures and anomalies
- Works with varying capture window sizes
- Confidence scoring (0-1)

### VehicleManager
- CRUD operations for vehicle configurations
- Validates consistency between classifier summary and vehicle config
- Manages vehicle metadata (nickname, make, model, efficiency, colors, etc.)
- Atomic file writes for data safety

### SessionLabelManager
- Manage session-to-vehicle mappings (session_vehicle_map.json)
- Manual labeling and batch operations
- Query labeled/unknown sessions
- Track labeling source and confidence
- Automatic statistics tracking

### ClassifierTrainer
- Train classifier from labeled session data
- Extract features from session power samples
- Generate/update classifier_summary.json
- Update vehicle power characteristics based on collected data

## Data Files

The library works with two JSON files:

- **classifier_summary.json**: ML training statistics (mean power, std, CV) for each vehicle
- **vehicle_config.json**: Vehicle metadata (display names, efficiency, colors, etc.)

Vehicle IDs must match between the two files for proper integration.

## Requirements

- Python 3.8+
- numpy >= 1.24.0

## License

MIT
