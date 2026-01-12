"""
Session Label Manager

Manages session-to-vehicle mapping stored in session_vehicle_map.json.
Provides CRUD operations for session labels and batch processing capabilities.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple


class SessionLabelManager:
    """Manages session-to-vehicle label mappings."""
    
    def __init__(self, map_file: str = "data/session_vehicle_map.json"):
        """Initialize session label manager.
        
        Args:
            map_file: Path to session_vehicle_map.json file
        """
        self.map_file = Path(map_file)
        self._map = None
        self.load()
    
    def load(self) -> None:
        """Load session vehicle map from file."""
        if self.map_file.exists():
            with open(self.map_file, "r") as f:
                self._map = json.load(f)
        else:
            self._map = {
                "sessions": {},
                "unknown_sessions": [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "statistics": {
                    "total_sessions": 0,
                    "labeled_sessions": 0,
                    "unknown": 0
                }
            }
    
    def save(self) -> None:
        """Save session vehicle map to file."""
        self._update_statistics()
        self._map["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # Ensure directory exists
        self.map_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write atomically
        temp_file = self.map_file.with_suffix(".json.tmp")
        with open(temp_file, "w") as f:
            json.dump(self._map, f, indent=2)
        temp_file.replace(self.map_file)
    
    def _update_statistics(self) -> None:
        """Update statistics in the map."""
        stats = {}
        for sid, entry in self._map.get("sessions", {}).items():
            vehicle = entry.get("vehicle", "unknown")
            stats[vehicle] = stats.get(vehicle, 0) + 1
        stats["unknown"] = len(self._map.get("unknown_sessions", []))
        
        self._map["statistics"] = {
            "total_sessions": len(self._map.get("sessions", {})) + len(self._map.get("unknown_sessions", [])),
            "labeled_sessions": len(self._map.get("sessions", {})),
            **stats
        }
    
    def label_session(
        self,
        session_id: str,
        vehicle_id: str,
        confidence: Optional[float] = None,
        source: str = "manual"
    ) -> None:
        """Label a session with a vehicle.
        
        Args:
            session_id: ChargePoint session ID
            vehicle_id: Vehicle identifier (or None to mark as unknown)
            confidence: Confidence score 0-1 (optional, typically None for manual)
            source: Source of label ("manual", "classifier", "batch", etc.)
        """
        if vehicle_id:
            # Add to labeled sessions
            self._map.setdefault("sessions", {})[session_id] = {
                "vehicle": vehicle_id,
                "confidence": confidence,
                "source": source,
                "labeled_at": datetime.now(timezone.utc).isoformat()
            }
            # Remove from unknown_sessions if present
            if session_id in self._map.get("unknown_sessions", []):
                self._map["unknown_sessions"].remove(session_id)
        else:
            # Mark as unknown
            if session_id in self._map.get("sessions", {}):
                del self._map["sessions"][session_id]
            if session_id not in self._map.get("unknown_sessions", []):
                self._map.setdefault("unknown_sessions", []).append(session_id)
    
    def unlabel_session(self, session_id: str) -> None:
        """Remove label from a session (mark as unknown).
        
        Args:
            session_id: ChargePoint session ID
        """
        if session_id in self._map.get("sessions", {}):
            del self._map["sessions"][session_id]
        if session_id not in self._map.get("unknown_sessions", []):
            self._map.setdefault("unknown_sessions", []).append(session_id)
    
    def get_label(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get label for a session.
        
        Args:
            session_id: ChargePoint session ID
            
        Returns:
            Label dict with vehicle, confidence, source, labeled_at, or None if unknown
        """
        if session_id in self._map.get("sessions", {}):
            return self._map["sessions"][session_id].copy()
        return None
    
    def get_vehicle(self, session_id: str) -> Optional[str]:
        """Get vehicle ID for a session.
        
        Args:
            session_id: ChargePoint session ID
            
        Returns:
            Vehicle ID or None if unknown
        """
        label = self.get_label(session_id)
        return label.get("vehicle") if label else None
    
    def is_labeled(self, session_id: str) -> bool:
        """Check if a session is labeled.
        
        Args:
            session_id: ChargePoint session ID
            
        Returns:
            True if labeled (not unknown)
        """
        return session_id in self._map.get("sessions", {})
    
    def is_unknown(self, session_id: str) -> bool:
        """Check if a session is marked as unknown.
        
        Args:
            session_id: ChargePoint session ID
            
        Returns:
            True if marked as unknown
        """
        return session_id in self._map.get("unknown_sessions", [])
    
    def get_unknown_sessions(self) -> List[str]:
        """Get list of unknown session IDs.
        
        Returns:
            List of session IDs marked as unknown
        """
        return self._map.get("unknown_sessions", []).copy()
    
    def get_labeled_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all labeled sessions.
        
        Returns:
            Dictionary of session_id -> label dict
        """
        return self._map.get("sessions", {}).copy()
    
    def get_sessions_by_vehicle(self, vehicle_id: str) -> List[str]:
        """Get all session IDs labeled with a specific vehicle.
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            List of session IDs
        """
        return [
            sid for sid, entry in self._map.get("sessions", {}).items()
            if entry.get("vehicle") == vehicle_id
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about labeled sessions.
        
        Returns:
            Statistics dictionary
        """
        self._update_statistics()
        return self._map.get("statistics", {}).copy()
    
    def batch_label(self, labels: List[Tuple[str, str, Optional[float], str]]) -> int:
        """Batch label multiple sessions.
        
        Args:
            labels: List of (session_id, vehicle_id, confidence, source) tuples
            
        Returns:
            Number of sessions labeled
        """
        count = 0
        for session_id, vehicle_id, confidence, source in labels:
            self.label_session(session_id, vehicle_id, confidence, source)
            count += 1
        return count
    
    def get_map(self) -> Dict[str, Any]:
        """Get the full map dictionary.
        
        Returns:
            Full map dict
        """
        return self._map.copy()
