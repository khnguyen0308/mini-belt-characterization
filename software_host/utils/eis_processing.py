"""
EIS data processing utilities for analysis and calculations.
"""

import numpy as np
from typing import Tuple, Dict
from scipy import signal


class EISAnalyzer:
    """Analyzer for Electrochemical Impedance Spectroscopy data."""

    @staticmethod
    def calculate_magnitude_phase(
        z_real: np.ndarray, z_imag: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate magnitude and phase from real and imaginary impedance.

        Args:
            z_real: Real part of impedance
            z_imag: Imaginary part of impedance

        Returns:
            Tuple of (magnitude, phase_degrees)
        """
        magnitude = np.sqrt(z_real**2 + z_imag**2)
        phase = np.degrees(np.arctan2(z_imag, z_real))
        return magnitude, phase

    @staticmethod
    def calculate_resistivity_reactance(
        magnitude: np.ndarray, phase: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate resistive and reactive components from magnitude and phase.

        Args:
            magnitude: Impedance magnitude
            phase: Phase angle in degrees

        Returns:
            Tuple of (resistance, reactance)
        """
        phase_rad = np.radians(phase)
        resistance = magnitude * np.cos(phase_rad)
        reactance = magnitude * np.sin(phase_rad)
        return resistance, reactance

    @staticmethod
    def fit_nyquist_circle(
        z_real: np.ndarray, z_imag: np.ndarray
    ) -> Dict[str, float]:
        """
        Fit a circle to Nyquist plot data using least squares.

        Args:
            z_real: Real impedance values
            z_imag: Imaginary impedance values

        Returns:
            Dictionary with fitted circle parameters (center_x, center_y, radius)
        """
        if len(z_real) < 3:
            return {"center_x": 0, "center_y": 0, "radius": 0}

        # Remove outliers using Hampel filter
        z_real_filtered = z_real.copy()
        z_imag_filtered = z_imag.copy()

        # Fit circle: (x - cx)^2 + (y - cy)^2 = r^2
        # Using algebraic method
        x = z_real_filtered
        y = -z_imag_filtered  # Negate for standard Nyquist representation

        x_m = np.mean(x)
        y_m = np.mean(y)

        u = x - x_m
        v = y - y_m

        Suu = np.sum(u**2)
        Svv = np.sum(v**2)
        Suv = np.sum(u * v)
        Suuu = np.sum(u**3)
        Svvv = np.sum(v**3)
        Suvv = np.sum(u * v**2)
        Svuu = np.sum(v * u**2)

        A = np.array([[Suu, Suv], [Suv, Svv]])
        b = np.array([0.5 * (Suuu + Suvv), 0.5 * (Svvv + Svuu)])

        try:
            c = np.linalg.solve(A, b)
            center_x = c[0] + x_m
            center_y = c[1] + y_m
            radius = np.sqrt(np.mean((x - center_x)**2 + (y - center_y)**2))
        except np.linalg.LinAlgError:
            return {"center_x": x_m, "center_y": y_m, "radius": 0}

        return {
            "center_x": center_x,
            "center_y": center_y,
            "radius": radius,
        }

    @staticmethod
    def apply_smoothing(
        data: np.ndarray, window_size: int = 5, method: str = "savgol"
    ) -> np.ndarray:
        """
        Apply smoothing filter to data.

        Args:
            data: Input data array
            window_size: Size of smoothing window
            method: 'savgol' (Savitzky-Golay) or 'moving_avg'

        Returns:
            Smoothed data
        """
        if len(data) < window_size:
            return data

        if method == "savgol":
            return signal.savgol_filter(data, window_size, 3)
        elif method == "moving_avg":
            kernel = np.ones(window_size) / window_size
            return np.convolve(data, kernel, mode="same")
        else:
            return data

    @staticmethod
    def calculate_phase_shift(
        reference: np.ndarray, signal_data: np.ndarray, frequency: float
    ) -> float:
        """
        Calculate phase shift between reference and signal.

        Args:
            reference: Reference signal
            signal_data: Measured signal
            frequency: Signal frequency in Hz

        Returns:
            Phase shift in degrees
        """
        if len(reference) < 2 or len(signal_data) < 2:
            return 0

        # Cross-correlation for phase detection
        correlation = np.correlate(reference, signal_data, mode="full")
        lag = np.argmax(correlation) - (len(reference) - 1)

        # Convert lag to phase
        phase_shift = (lag / len(reference)) * 360
        return float(phase_shift)

    @staticmethod
    def get_quality_factor(
        z_real: np.ndarray, z_imag: np.ndarray
    ) -> float:
        """
        Calculate quality factor (Q) from impedance data.

        Q = |Z_imag| / Z_real

        Args:
            z_real: Real impedance
            z_imag: Imaginary impedance

        Returns:
            Quality factor
        """
        if len(z_real) == 0 or np.mean(np.abs(z_real)) == 0:
            return 0

        return np.mean(np.abs(z_imag)) / np.mean(np.abs(z_real))

    @staticmethod
    def normalize_data(
        data: np.ndarray, method: str = "minmax"
    ) -> np.ndarray:
        """
        Normalize data for visualization.

        Args:
            data: Input data
            method: 'minmax' or 'zscore'

        Returns:
            Normalized data
        """
        if len(data) == 0:
            return data

        if method == "minmax":
            data_min = np.min(data)
            data_max = np.max(data)
            if data_max == data_min:
                return np.zeros_like(data)
            return (data - data_min) / (data_max - data_min)

        elif method == "zscore":
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return np.zeros_like(data)
            return (data - mean) / std

        return data
