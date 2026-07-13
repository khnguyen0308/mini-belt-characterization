"""
Data storage and export functionality for EIS measurements.
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from data_acquisition.eis_device import EISMeasurement

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles data storage and export for EIS measurements."""

    def __init__(self, data_directory: str = "./data"):
        """
        Initialize data storage.

        Args:
            data_directory: Directory for storing exported data
        """
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)

    def export_to_csv(
        self, measurements: List[EISMeasurement], filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Export measurements to CSV file.

        Args:
            measurements: List of EISMeasurement objects
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file or None if failed
        """
        if not measurements:
            logger.warning("No measurements to export")
            return None

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eis_data_{timestamp}.csv"

        filepath = self.data_directory / filename

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "Timestamp",
                    "Frequency (Hz)",
                    "Real (Ω)",
                    "Imaginary (Ω)",
                    "Magnitude (Ω)",
                    "Phase (°)",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for measurement in measurements:
                    writer.writerow(
                        {
                            "Timestamp": datetime.fromtimestamp(
                                measurement.timestamp
                            ).isoformat(),
                            "Frequency (Hz)": f"{measurement.frequency:.2f}",
                            "Real (Ω)": f"{measurement.impedance_real:.4f}",
                            "Imaginary (Ω)": f"{measurement.impedance_imag:.4f}",
                            "Magnitude (Ω)": f"{measurement.magnitude:.4f}",
                            "Phase (°)": f"{measurement.phase:.4f}",
                        }
                    )

            logger.info(f"Exported {len(measurements)} measurements to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return None

    def export_to_json(
        self, measurements: List[EISMeasurement], filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Export measurements to JSON file.

        Args:
            measurements: List of EISMeasurement objects
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file or None if failed
        """
        if not measurements:
            logger.warning("No measurements to export")
            return None

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eis_data_{timestamp}.json"

        filepath = self.data_directory / filename

        try:
            data = [
                {
                    "timestamp": datetime.fromtimestamp(
                        m.timestamp
                    ).isoformat(),
                    "frequency_hz": m.frequency,
                    "impedance_real_ohm": m.impedance_real,
                    "impedance_imag_ohm": m.impedance_imag,
                    "magnitude_ohm": m.magnitude,
                    "phase_degree": m.phase,
                }
                for m in measurements
            ]

            with open(filepath, "w", encoding="utf-8") as jsonfile:
                json.dump(
                    {
                        "measurements": data,
                        "count": len(measurements),
                        "export_time": datetime.now().isoformat(),
                    },
                    jsonfile,
                    indent=2,
                )

            logger.info(f"Exported {len(measurements)} measurements to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            return None

    def load_from_csv(self, filepath: str) -> List[Dict]:
        """
        Load measurements from CSV file.

        Args:
            filepath: Path to CSV file

        Returns:
            List of measurement dictionaries
        """
        measurements = []

        try:
            with open(filepath, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    measurements.append(
                        {
                            "frequency": float(row["Frequency (Hz)"]),
                            "impedance_real": float(row["Real (Ω)"]),
                            "impedance_imag": float(row["Imaginary (Ω)"]),
                            "magnitude": float(row["Magnitude (Ω)"]),
                            "phase": float(row["Phase (°)"]),
                        }
                    )

            logger.info(f"Loaded {len(measurements)} measurements from {filepath}")
            return measurements

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return []

    def get_export_formats(self) -> List[str]:
        """Get available export formats."""
        return ["csv", "json"]

    def list_data_files(self) -> List[str]:
        """
        List all data files in the storage directory.

        Returns:
            List of file paths
        """
        files = []
        for pattern in ["*.csv", "*.json"]:
            files.extend([str(f) for f in self.data_directory.glob(pattern)])
        return sorted(files)
