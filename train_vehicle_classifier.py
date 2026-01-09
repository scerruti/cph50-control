#!/usr/bin/env python3
"""
Extract robust statistical features from charging power data.

Features designed to work with both full sessions and partial 5-minute captures:
- Mean power (kW)
- 25th percentile power (robust to anomalies)
- 75th percentile power (robust to anomalies)
- Coefficient of variation (std / mean) - captures stability
- IQR (75th - 25th) - noise indicator

These statistics are invariant to ramps (present or missed) and resistant to dips/spikes.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


def extract_features(power_samples: List[float]) -> Dict[str, float]:
    """
    Extract robust statistical features from a list of power samples.
    
    Args:
        power_samples: List of power_kw values (can be partial or full session)
    
    Returns:
        Dict with feature names and values
    """
    if not power_samples or len(power_samples) < 2:
        return None
    
    arr = np.array(power_samples)
    
    # Remove zero/near-zero values (ramp-up, ramp-down, or idle)
    # Keep values >= 0.5 kW (excludes startup/shutdown transients)
    active = arr[arr >= 0.5]
    
    if len(active) < 2:
        # Not enough active data—use all if available
        active = arr[arr > 0]
    
    if len(active) < 1:
        return None
    
    mean_power = float(np.mean(active))
    std_power = float(np.std(active))
    p25 = float(np.percentile(active, 25))
    p75 = float(np.percentile(active, 75))
    iqr = p75 - p25
    
    # Coefficient of variation (std / mean)
    # Higher CV = less stable charging (anomalies, load shifts, etc.)
    cv = std_power / mean_power if mean_power > 0 else 0.0
    
    return {
        "mean_power_kw": mean_power,
        "p25_power_kw": p25,
        "p75_power_kw": p75,
        "iqr_power_kw": iqr,
        "cv_stability": float(cv),
        "sample_count": len(active),
    }


def load_session_data(session_file: str) -> Optional[Tuple[str, List[float]]]:
    """Load a session JSON and extract power samples."""
    with open(session_file, "r") as f:
        data = json.load(f)
    
    vehicle_label = data["vehicle"]["make"]
    if "Chevrolet" in vehicle_label or "Equinox" in data["vehicle"]["model"]:
        vehicle_label = "equinox"
    elif "Volvo" in vehicle_label:
        vehicle_label = "volvo"
    
    power_samples = [s["power_kw"] for s in data.get("power_samples", [])]
    
    return vehicle_label, power_samples


def analyze_seed_dataset(sessions_dir: str = "data/sessions") -> Dict:
    """
    Load all seed sessions and compute feature statistics.
    
    Returns:
        Dict with per-vehicle feature statistics
    """
    sessions_path = Path(sessions_dir)
    vehicle_features = {"volvo": [], "equinox": []}
    
    for session_file in sorted(sessions_path.glob("*.json")):
        result = load_session_data(str(session_file))
        if result is None:
            continue
        
        vehicle, power_samples = result
        features = extract_features(power_samples)
        
        if features:
            vehicle_features[vehicle].append(features)
            print(f"✓ {session_file.name} ({vehicle})")
            print(f"  Mean: {features['mean_power_kw']:.2f} kW | "
                  f"P25: {features['p25_power_kw']:.2f} | "
                  f"P75: {features['p75_power_kw']:.2f} | "
                  f"IQR: {features['iqr_power_kw']:.2f} | "
                  f"CV: {features['cv_stability']:.3f}")
    
    # Compute summary statistics per vehicle
    summary = {}
    for vehicle, features_list in vehicle_features.items():
        if not features_list:
            continue
        
        summary[vehicle] = {
            "count": len(features_list),
            "mean_power": {
                "mean": float(np.mean([f["mean_power_kw"] for f in features_list])),
                "std": float(np.std([f["mean_power_kw"] for f in features_list])),
            },
            "p25_power": {
                "mean": float(np.mean([f["p25_power_kw"] for f in features_list])),
                "std": float(np.std([f["p25_power_kw"] for f in features_list])),
            },
            "cv_stability": {
                "mean": float(np.mean([f["cv_stability"] for f in features_list])),
                "std": float(np.std([f["cv_stability"] for f in features_list])),
            },
        }
    
    return summary, vehicle_features


def predict_vehicle(features: Dict[str, float], summary: Dict) -> Tuple[str, float]:
    """
    Simple Euclidean distance classifier using seed summary statistics.
    
    Args:
        features: Extracted features from a charging session
        summary: Summary statistics from seed dataset
    
    Returns:
        (predicted_vehicle, confidence_0_to_1)
    """
    if not summary:
        return None, 0.0
    
    mean_power = features["mean_power_kw"]
    
    # For each vehicle, compute distance from mean power
    distances = {}
    for vehicle, stats in summary.items():
        vehicle_mean = stats["mean_power"]["mean"]
        vehicle_std = stats["mean_power"]["std"]
        
        # Standardized distance
        if vehicle_std > 0:
            distances[vehicle] = abs(mean_power - vehicle_mean) / vehicle_std
        else:
            distances[vehicle] = abs(mean_power - vehicle_mean)
    
    # Predict as vehicle with smallest distance
    best_vehicle = min(distances, key=distances.get)
    worst_distance = max(distances.values())
    best_distance = distances[best_vehicle]
    
    # Confidence: how much better is best vs worst
    if worst_distance > 0:
        confidence = (worst_distance - best_distance) / worst_distance
    else:
        confidence = 0.0
    
    return best_vehicle, float(confidence)


def main():
    if len(sys.argv) > 1:
        sessions_dir = sys.argv[1]
    else:
        sessions_dir = "data/sessions"
    
    print("🔧 Analyzing seed dataset for vehicle classification...\n")
    
    summary, vehicle_features = analyze_seed_dataset(sessions_dir)
    
    print("\n📊 Summary Statistics by Vehicle:\n")
    for vehicle, stats in summary.items():
        print(f"{vehicle.upper()}:")
        print(f"  Samples: {stats['count']}")
        print(f"  Mean Power: {stats['mean_power']['mean']:.2f} ± {stats['mean_power']['std']:.2f} kW")
        print(f"  P25 Power:  {stats['p25_power']['mean']:.2f} ± {stats['p25_power']['std']:.2f} kW")
        print(f"  Stability:  {stats['cv_stability']['mean']:.3f} ± {stats['cv_stability']['std']:.3f} CV")
        print()
    
    # Save summary for runtime use
    summary_file = Path(sessions_dir).parent / "classifier_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Classifier summary saved to {summary_file}\n")
    
    # Test predictions on seed data
    print("🧪 Testing predictions on seed data:\n")
    for vehicle, features_list in vehicle_features.items():
        print(f"{vehicle.upper()}:")
        for i, features in enumerate(features_list, 1):
            pred, conf = predict_vehicle(features, summary)
            status = "✓" if pred == vehicle else "✗"
            print(f"  {status} Sample {i}: predicted={pred}, confidence={conf:.2%}")
        print()


if __name__ == "__main__":
    main()
