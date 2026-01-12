"""
EV Vehicle Classification Library

A library for classifying electric vehicles based on charging power curve analysis.
Includes vehicle configuration management for training, labeling, and classification workflows.
"""

from vehicle_classifier.classifier import VehicleClassifier
from vehicle_classifier.vehicle_manager import VehicleManager
from vehicle_classifier.session_label_manager import SessionLabelManager
from vehicle_classifier.classifier_trainer import ClassifierTrainer

__version__ = "0.1.0"
__all__ = [
    "VehicleClassifier",
    "VehicleManager",
    "SessionLabelManager",
    "ClassifierTrainer"
]
