"""
Classifier Trainer

Trains the vehicle classifier from labeled session data.
Generates/updates classifier_summary.json based on collected session power samples.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

from vehicle_classifier.session_label_manager import SessionLabelManager


class ClassifierTrainer:
    """Trains classifier from labeled session data."""
    
    def __init__(
        self,
        sessions_dir: str = "data/sessions",
        label_manager: Optional[SessionLabelManager] = None
    ):
        """Initialize classifier trainer.
        
        Args:
            sessions_dir: Directory containing session JSON files (YYYY/MM/DD structure)
            label_manager: Optional SessionLabelManager instance
        """
        self.sessions_dir = Path(sessions_dir)
        self.label_manager = label_manager or SessionLabelManager()
    
    @staticmethod
    def extract_features(power_samples: List[float]) -> Optional[Dict[str, float]]:
        """
        Extract robust statistical features from power samples.
        
        Args:
            power_samples: List of power_kw values
            
        Returns:
            Dictionary with extracted features, or None if insufficient data
        """
        if not power_samples or len(power_samples) < 2:
            return None
        
        arr = np.array(power_samples)
        
        # Filter to active charging (>= 0.5 kW)
        active = arr[arr >= 0.5]
        
        if len(active) < 2:
            active = arr[arr > 0]
        
        if len(active) < 1:
            return None
        
        mean_power = float(np.mean(active))
        std_power = float(np.std(active))
        p25 = float(np.percentile(active, 25))
        p75 = float(np.percentile(active, 75))
        iqr = p75 - p25
        cv = std_power / mean_power if mean_power > 0 else 0.0
        
        return {
            "mean_power_kw": mean_power,
            "p25_power_kw": p25,
            "p75_power_kw": p75,
            "iqr_power_kw": iqr,
            "cv_stability": float(cv),
            "sample_count": len(active),
        }
    
    def load_session_power_samples(self, session_file: Path) -> Optional[List[float]]:
        """Load power samples from a session JSON file.
        
        Args:
            session_file: Path to session JSON file
            
        Returns:
            List of power_kw values, or None if file cannot be loaded
        """
        try:
            with open(session_file, "r") as f:
                data = json.load(f)
            
            # Extract power samples from the samples array
            samples = data.get("samples", [])
            power_samples = [
                s["power_kw"] for s in samples
                if s.get("power_kw") is not None
            ]
            
            return power_samples if power_samples else None
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None
    
    def find_session_files(self) -> List[Path]:
        """Find all session JSON files in the sessions directory.
        
        Returns:
            List of paths to session JSON files
        """
        session_files = []
        
        # Walk through YYYY/MM/DD structure
        for year_dir in sorted(self.sessions_dir.iterdir()):
            if not year_dir.is_dir():
                continue
            for month_dir in sorted(year_dir.iterdir()):
                if not month_dir.is_dir():
                    continue
                for day_dir in sorted(month_dir.iterdir()):
                    if not day_dir.is_dir():
                        continue
                    for session_file in sorted(day_dir.glob("*.json")):
                        session_files.append(session_file)
        
        return session_files
    
    def train_from_labeled_sessions(
        self,
        output_file: str = "data/classifier_summary.json"
    ) -> Dict[str, Any]:
        """
        Train classifier from labeled sessions.
        
        Uses session_vehicle_map.json to get labels, then processes session files
        to extract features and generate classifier_summary.json.
        
        Args:
            output_file: Path to save classifier_summary.json
            
        Returns:
            Classifier summary dictionary
        """
        session_files = self.find_session_files()
        
        # Group sessions by vehicle
        vehicle_features: Dict[str, List[Dict[str, float]]] = {}
        
        processed = 0
        skipped = 0
        
        for session_file in session_files:
            # Extract session_id from filename
            session_id = session_file.stem
            
            # Get vehicle label from session_vehicle_map
            vehicle_id = self.label_manager.get_vehicle(session_id)
            if not vehicle_id:
                skipped += 1
                continue
            
            # Load power samples
            power_samples = self.load_session_power_samples(session_file)
            if not power_samples:
                skipped += 1
                continue
            
            # Extract features
            features = self.extract_features(power_samples)
            if not features:
                skipped += 1
                continue
            
            # Add to vehicle's feature list
            if vehicle_id not in vehicle_features:
                vehicle_features[vehicle_id] = []
            vehicle_features[vehicle_id].append(features)
            processed += 1
        
        # Compute summary statistics per vehicle
        summary = {}
        for vehicle_id, features_list in vehicle_features.items():
            if not features_list:
                continue
            
            summary[vehicle_id] = {
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
        
        # Save summary
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        return {
            "summary": summary,
            "processed": processed,
            "skipped": skipped,
            "vehicles": list(summary.keys())
        }
