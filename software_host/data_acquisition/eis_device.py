"""
EIS (Electrochemical Impedance Spectroscopy) Device Interface.
Handles communication and data parsing from STM32-based EIS measurement system.
"""

import threading
import time
import logging
from typing import Callable, Optional, Dict, List, Tuple
from dataclasses import dataclass
from collections import deque
import numpy as np

from .serial_manager import SerialManager

logger = logging.getLogger(__name__)


@dataclass
class EISMeasurement:
    """Single EIS measurement point."""
    frequency: float      # Hz
    impedance_real: float # Ohms
    impedance_imag: float # Ohms
    magnitude: float      # Ohms
    phase: float          # Degrees
    timestamp: float      # Unix timestamp


class EISDevice:
    """Interface for STM32-based EIS device."""

    def __init__(self, port: str, baudrate: int = 115200):
        """
        Initialize EIS device interface.

        Args:
            port: Serial port
            baudrate: Communication speed
        """
        self.serial = SerialManager(port, baudrate)
        self.running = False
        self.measurement_thread: Optional[threading.Thread] = None

        # Data storage
        self.current_measurement: Optional[EISMeasurement] = None
        self.measurement_history: deque = deque(maxlen=1000)  # Keep last 1000 points
        self.callbacks: List[Callable[[EISMeasurement], None]] = []

        # Measurement state
        self.is_measuring = False
        self.measurement_count = 0

    def connect(self) -> bool:
        """Connect to the EIS device."""
        if not self.serial.connect():
            return False

        self.running = True
        self.measurement_thread = threading.Thread(
            target=self._measurement_loop, daemon=True
        )
        self.measurement_thread.start()
        logger.info("EIS Device connected")
        return True

    def disconnect(self):
        """Disconnect from the EIS device."""
        self.running = False
        self.serial.disconnect()
        logger.info("EIS Device disconnected")

    def start_measurement(self):
        """Start EIS measurements."""
        self.is_measuring = True
        self.measurement_count = 0
        self.measurement_history.clear()
        self.serial.send_command("START_EIS")
        logger.info("EIS measurement started")

    def stop_measurement(self):
        """Stop EIS measurements."""
        self.is_measuring = False
        self.serial.send_command("STOP_EIS")
        logger.info("EIS measurement stopped")

    def register_callback(self, callback: Callable[[EISMeasurement], None]):
        """
        Register callback for new measurements.

        Args:
            callback: Function to call with each new EISMeasurement
        """
        self.callbacks.append(callback)

    def _measurement_loop(self):
        """Background thread for processing incoming data."""
        while self.running:
            try:
                data = self.serial.get_data(timeout=0.1)
                if data:
                    measurement = self._parse_measurement(data)
                    if measurement:
                        self.current_measurement = measurement
                        self.measurement_history.append(measurement)
                        self.measurement_count += 1

                        # Call all registered callbacks
                        for callback in self.callbacks:
                            try:
                                callback(measurement)
                            except Exception as e:
                                logger.error(f"Error in measurement callback: {e}")

            except Exception as e:
                logger.error(f"Error in measurement loop: {e}")
                time.sleep(0.1)

    def _parse_measurement(self, data: str) -> Optional[EISMeasurement]:
        """
        Parse measurement data from serial string.

        Supported formats:
        1. STM32 New Format: "Index, Magnitude, Phase, AccMagnitude, AccPhase"
           Example: "0,150.450,45.123,150.400,45.100"
        2. Legacy key-value format: "FREQ:10.5,REAL:1000.5,IMAG:-500.2"
        3. Legacy CSV format: "10.5,1000.5,-500.2"

        Args:
            data: Data string from device

        Returns:
            EISMeasurement object or None if parsing fails
        """
        try:
            # Try STM32 new format first (Index, Magnitude, Phase, ...)
            # Format: "0,150.450,45.123,150.400,45.100"
            parts = data.split(',')
            if len(parts) >= 3:
                # Check if this is STM32 new format or legacy format
                # STM32 new format: Index (0-19), Magnitude, Phase, AccMagnitude, AccPhase
                # Legacy format: Frequency, Z_real, Z_imag
                
                try:
                    first_val = float(parts[0])
                    second_val = float(parts[1])
                    third_val = float(parts[2])
                    
                    # Try to determine format:
                    # If first value is 0-19 (index), this is likely STM32 new format
                    # If first value is 10-100000 (frequency), this is legacy format
                    
                    if 0 <= first_val <= 25 and second_val > 100 and 180 > third_val > -180:
                        # STM32 New Format: Index, Magnitude, Phase, AccMagnitude, AccPhase
                        index = int(first_val)
                        magnitude = second_val
                        phase = third_val
                        
                        # Extract Accumulated (Acc) values for higher accuracy
                        # Acc values are averaged/filtered over multiple measurements
                        acc_magnitude = float(parts[3]) if len(parts) > 3 else magnitude
                        acc_phase = float(parts[4]) if len(parts) > 4 else phase
                        
                        # Map index (0-19) to frequency logarithmically (10 Hz - 100 kHz)
                        # Using 20 points logarithmically spaced
                        frequency = 10 * (10000 ** (index / 19)) if index < 20 else 10

                        # Convert Accumulated Magnitude + Phase to Z_real, Z_imag
                        # Z = M * e^(j*θ) = M * (cos(θ) + j*sin(θ))
                        # Z_real = M * cos(θ), Z_imag = M * sin(θ)
                        phase_rad = np.radians(acc_phase)  # Use Acc Phase for accuracy
                        z_real = acc_magnitude * np.cos(phase_rad)  # Use Acc Magnitude for accuracy
                        z_imag = acc_magnitude * np.sin(phase_rad)  # Use Acc Magnitude for accuracy
                        
                        logger.debug(f"STM32 Format: Index={index}, Freq={frequency:.2f}Hz, "
                                   f"Mag={magnitude:.2f}Ω→AccMag={acc_magnitude:.2f}Ω, Phase={phase:.2f}°→AccPhase={acc_phase:.2f}°, "
                                   f"Z_real={z_real:.2f}, Z_imag={z_imag:.2f}")
                        
                        return EISMeasurement(
                            frequency=frequency,
                            impedance_real=z_real,
                            impedance_imag=z_imag,
                            magnitude=acc_magnitude,  # Use Acc Magnitude
                            phase=acc_phase,  # Use Acc Phase
                            timestamp=time.time(),
                        )
                    else:
                        # Legacy CSV format: Frequency, Z_real, Z_imag
                        freq = first_val
                        z_real = second_val
                        z_imag = third_val

                        # Calculate magnitude and phase from Z_real, Z_imag
                        magnitude = np.sqrt(z_real**2 + z_imag**2)
                        phase = np.degrees(np.arctan2(z_imag, z_real))

                        logger.debug(f"Legacy CSV Format: Freq={freq:.2f}Hz, "
                                   f"Z_real={z_real:.2f}, Z_imag={z_imag:.2f}")

                        return EISMeasurement(
                            frequency=freq,
                            impedance_real=z_real,
                            impedance_imag=z_imag,
                            magnitude=magnitude,
                            phase=phase,
                            timestamp=time.time(),
                        )
                except (ValueError, IndexError):
                    pass

            # Try key-value format (legacy)
            if 'FREQ:' in data and 'REAL:' in data and 'IMAG:' in data:
                values = {}
                for item in data.split(','):
                    if ':' in item:
                        key, value = item.split(':')
                        values[key.strip()] = float(value.strip())

                if 'FREQ' in values and 'REAL' in values and 'IMAG' in values:
                    freq = values['FREQ']
                    z_real = values['REAL']
                    z_imag = values['IMAG']

                    magnitude = np.sqrt(z_real**2 + z_imag**2)
                    phase = np.degrees(np.arctan2(z_imag, z_real))

                    logger.debug(f"Key-value Format: Freq={freq:.2f}Hz, "
                               f"Z_real={z_real:.2f}, Z_imag={z_imag:.2f}")

                    return EISMeasurement(
                        frequency=freq,
                        impedance_real=z_real,
                        impedance_imag=z_imag,
                        magnitude=magnitude,
                        phase=phase,
                        timestamp=time.time(),
                    )

        except Exception as e:
            logger.debug(f"Failed to parse measurement data '{data}': {e}")

        return None

    def get_nyquist_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get Nyquist plot data (Real vs Imaginary impedance).

        Returns:
            Tuple of (real_impedance, imaginary_impedance) arrays
        """
        if not self.measurement_history:
            return np.array([]), np.array([])

        real = np.array([m.impedance_real for m in self.measurement_history])
        imag = np.array([m.impedance_imag for m in self.measurement_history])
        return real, imag

    def get_bode_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get Bode plot data (Frequency vs Magnitude and Phase).

        Returns:
            Tuple of (frequency, magnitude, phase) arrays
        """
        if not self.measurement_history:
            return np.array([]), np.array([]), np.array([])

        frequencies = np.array([m.frequency for m in self.measurement_history])
        magnitudes = np.array([m.magnitude for m in self.measurement_history])
        phases = np.array([m.phase for m in self.measurement_history])
        return frequencies, magnitudes, phases

    def get_statistics(self) -> Dict[str, float]:
        """
        Get current measurement statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.measurement_history:
            return {}

        mags = [m.magnitude for m in self.measurement_history]
        freqs = [m.frequency for m in self.measurement_history]

        return {
            'frequency_min': min(freqs),
            'frequency_max': max(freqs),
            'frequency_avg': sum(freqs) / len(freqs),
            'magnitude_min': min(mags),
            'magnitude_max': max(mags),
            'magnitude_avg': sum(mags) / len(mags),
            'measurement_count': len(self.measurement_history),
        }
