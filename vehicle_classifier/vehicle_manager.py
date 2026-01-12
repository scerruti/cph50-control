"""
Vehicle Configuration Manager

Manages vehicle metadata stored in vehicle_config.json.
Provides CRUD operations for vehicles and ensures consistency with classifier data.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class VehicleManager:
    """Manages vehicle configuration data."""
    
    def __init__(self, config_file: str = "data/vehicle_config.json"):
        """Initialize vehicle manager.
        
        Args:
            config_file: Path to vehicle_config.json file
        """
        self.config_file = Path(config_file)
        self._config = None
        self.load()
    
    def load(self) -> None:
        """Load vehicle configuration from file."""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                self._config = json.load(f)
        else:
            self._config = {
                "vehicles": {},
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
    
    def save(self) -> None:
        """Save vehicle configuration to file."""
        self._config["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write atomically
        temp_file = self.config_file.with_suffix(".json.tmp")
        with open(temp_file, "w") as f:
            json.dump(self._config, f, indent=2)
        temp_file.replace(self.config_file)
    
    def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get vehicle configuration by ID.
        
        Args:
            vehicle_id: Vehicle identifier (e.g., "serenity_equinox_2024")
            
        Returns:
            Vehicle configuration dict or None if not found
        """
        return self._config.get("vehicles", {}).get(vehicle_id)
    
    def get_all_vehicles(self) -> Dict[str, Dict[str, Any]]:
        """Get all vehicles.
        
        Returns:
            Dictionary of vehicle_id -> vehicle_config
        """
        return self._config.get("vehicles", {}).copy()
    
    def list_vehicle_ids(self) -> List[str]:
        """Get list of all vehicle IDs.
        
        Returns:
            List of vehicle IDs
        """
        return list(self._config.get("vehicles", {}).keys())
    
    def add_vehicle(
        self,
        vehicle_id: str,
        nickname: str,
        make: str,
        model: str,
        year: int,
        **kwargs
    ) -> None:
        """Add a new vehicle.
        
        Args:
            vehicle_id: Unique vehicle identifier (e.g., "serenity_equinox_2024")
            nickname: Display name (e.g., "Serenity")
            make: Manufacturer (e.g., "Chevrolet")
            model: Model name (e.g., "Equinox EV")
            year: Model year
            **kwargs: Additional optional fields:
                - trim: Trim level
                - battery_capacity_kwh: Battery capacity
                - max_charge_rate_kw: Max charging power
                - paint_color: Paint color name
                - paint_color_hex: Hex color code
                - display_color: Display color name
                - efficiency_mi_per_kwh: Efficiency
                - characteristics: Description
        """
        if vehicle_id in self._config.get("vehicles", {}):
            raise ValueError(f"Vehicle {vehicle_id} already exists")
        
        vehicle = {
            "nickname": nickname,
            "make": make,
            "model": model,
            "year": year,
        }
        
        # Add optional fields
        optional_fields = [
            "trim", "battery_capacity_kwh", "max_charge_rate_kw",
            "paint_color", "paint_color_hex", "display_color",
            "efficiency_mi_per_kwh", "characteristics"
        ]
        for field in optional_fields:
            if field in kwargs:
                vehicle[field] = kwargs[field]
        
        if "vehicles" not in self._config:
            self._config["vehicles"] = {}
        self._config["vehicles"][vehicle_id] = vehicle
    
    def update_vehicle(self, vehicle_id: str, **kwargs) -> None:
        """Update vehicle configuration.
        
        Args:
            vehicle_id: Vehicle identifier
            **kwargs: Fields to update (same as add_vehicle)
        """
        if vehicle_id not in self._config.get("vehicles", {}):
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        vehicle = self._config["vehicles"][vehicle_id]
        
        # Update allowed fields
        allowed_fields = [
            "nickname", "make", "model", "year", "trim",
            "battery_capacity_kwh", "max_charge_rate_kw",
            "paint_color", "paint_color_hex", "display_color",
            "efficiency_mi_per_kwh", "characteristics"
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                vehicle[field] = value
            else:
                raise ValueError(f"Invalid field: {field}")
    
    def delete_vehicle(self, vehicle_id: str) -> None:
        """Delete a vehicle.
        
        Args:
            vehicle_id: Vehicle identifier to delete
        """
        if vehicle_id not in self._config.get("vehicles", {}):
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        del self._config["vehicles"][vehicle_id]
    
    def vehicle_exists(self, vehicle_id: str) -> bool:
        """Check if vehicle exists.
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            True if vehicle exists
        """
        return vehicle_id in self._config.get("vehicles", {})
    
    def get_display_name(self, vehicle_id: str) -> str:
        """Get display name for vehicle (nickname or fallback to vehicle_id).
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            Display name
        """
        vehicle = self.get_vehicle(vehicle_id)
        if vehicle and "nickname" in vehicle:
            return vehicle["nickname"]
        return vehicle_id
    
    def validate_vehicle_ids(self, classifier_summary: Dict[str, Any]) -> List[str]:
        """Validate that vehicle IDs in classifier_summary exist in config.
        
        Args:
            classifier_summary: Classifier summary dictionary
            
        Returns:
            List of missing vehicle IDs
        """
        config_ids = set(self.list_vehicle_ids())
        classifier_ids = set(classifier_summary.keys())
        return list(classifier_ids - config_ids)
    
    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary.
        
        Returns:
            Full configuration dict
        """
        return self._config.copy()
