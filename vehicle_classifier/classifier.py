"""
Runtime inference module for vehicle classification.

Designed to be integrated into data collection scripts or other applications.

Usage:
  from vehicle_classifier import VehicleClassifier
  
  classifier = VehicleClassifier("data/classifier_summary.json")
  power_samples = [8.5, 8.6, 8.7, ...]
  vehicle, confidence = classifier.predict(power_samples)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


class VehicleClassifier:
    """Statistical classifier for vehicle identification, supporting context filtering and charger as feature."""

    def __init__(self, summary_file: str = "data/classifier_summary.json"):
        self.summary = {}
        summary_path = Path(summary_file)
        if summary_path.exists():
            with open(summary_path, "r") as f:
                self.summary = json.load(f)
        else:
            raise FileNotFoundError(f"Classifier summary not found: {summary_file}")

    def extract_features(self, power_samples: List[float]) -> Optional[Dict[str, float]]:
        if not power_samples or len(power_samples) < 2:
            return None
        arr = np.array(power_samples)
        active = arr[arr >= 0.5]
        if len(active) < 1:
            active = arr[arr > 0]
        if len(active) < 1:
            return None
        mean_power = float(np.mean(active))
        std_power = float(np.std(active))
        cv = std_power / mean_power if mean_power > 0 else 0.0
        return {
            "mean_power_kw": mean_power,
            "cv_stability": float(cv),
        }

    def predict(self, power_samples: List[float], eligible_vehicles: Optional[dict] = None, charger_id: Optional[str] = None) -> Tuple[Optional[str], float]:
        """
        Predict vehicle from power samples, optionally restricting to eligible vehicles and using charger_id as a feature.
        Args:
            power_samples: List of power readings in kW
            eligible_vehicles: Dict of vehicle_id -> vehicle_config to consider (filtered by valid_periods)
            charger_id: Optional charger/device_id for future use
        Returns:
            Tuple of (vehicle_name, confidence_0_to_1)
        """
        features = self.extract_features(power_samples)
        if features is None:
            return None, 0.0
        mean_power = features["mean_power_kw"]
        # Use only eligible vehicles if provided
        summary = self.summary
        if eligible_vehicles is not None:
            summary = {k: v for k, v in self.summary.items() if k in eligible_vehicles}
        # Optionally, charger_id could be used to further filter or weight results here
        distances = {}
        for vehicle, stats in summary.items():
            vehicle_mean = stats["mean_power"]["mean"]
            vehicle_std = stats["mean_power"].get("std", 0.1)
            if vehicle_std > 0:
                distance = abs(mean_power - vehicle_mean) / vehicle_std
            else:
                distance = abs(mean_power - vehicle_mean)
            # Optionally, adjust distance if charger_id is known to affect this vehicle
            distances[vehicle] = distance
        if not distances:
            return None, 0.0
        best_vehicle = min(distances, key=distances.get)
        best_distance = distances[best_vehicle]
        worst_distance = max(distances.values())
        if worst_distance > 0:
            confidence = (worst_distance - best_distance) / worst_distance
        else:
            confidence = 0.0
        return best_vehicle, float(confidence)
