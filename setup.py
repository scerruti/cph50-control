"""
Setup script for vehicle-classifier library.
This allows local installation: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="vehicle-classifier",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
    ],
    python_requires=">=3.8",
)
