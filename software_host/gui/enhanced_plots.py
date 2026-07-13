"""
Enhanced plotting components integrating Matplotlib (like old_SeriPlot.py).
Supports multiple plot types: Nyquist, Bode, Time Domain, etc.
Modern dark theme with real-time visualization.
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from utils.eis_processing import EISAnalyzer


# ============================================================================
# Matplotlib Canvas Widget (Dark theme)
# ============================================================================

class PlotCanvas(FigureCanvas):
    """Matplotlib canvas with dark theme styling."""

    def __init__(self, parent=None):
        """Initialize plot canvas."""
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.fig.set_facecolor("#2b2b2b")
        super().__init__(self.fig)
        self.setParent(parent)
        self._setup_style()

    def _setup_style(self):
        """Setup dark theme styling."""
        self.fig.patch.set_facecolor("#2b2b2b")

    def clear(self):
        """Clear all axes and redraw."""
        self.fig.clear()
        self.draw_idle()

    @staticmethod
    def _style_ax(ax, title: str, xlabel: str, ylabel: str):
        """Apply dark theme styling to axis."""
        ax.set_facecolor("#1e1e1e")
        ax.set_title(title, color="white", fontsize=12, fontweight="bold")
        ax.set_xlabel(xlabel, color="white", fontsize=10)
        ax.set_ylabel(ylabel, color="white", fontsize=10)
        ax.tick_params(colors="white", labelsize=8)
        ax.grid(True, alpha=0.3, color="#666")
        for spine in ax.spines.values():
            spine.set_color("#555")


# ============================================================================
# Enhanced Plot Manager with All Plot Types
# ============================================================================

class EnhancedPlotManager(QWidget):
    """
    Unified plot manager supporting all visualization types.
    Inspired by old_SeriPlot.py with modern dark theme.
    """

    # Plot types constants
    SIGNAL_PLOTS = ["Time Domain"]
    IMPEDANCE_PLOTS = [
        "Nyquist", "Bode Magnitude", "Bode Phase",
        "Re(Z) vs Freq", "Im(Z) vs Freq",
        "Nyquist + Bode", "Nyquist + Re/Im(Z)"
    ]
    ALL_PLOTS = SIGNAL_PLOTS + IMPEDANCE_PLOTS

    # Display constants
    MAX_DISPLAY = 10
    MAX_BUFFER = 15

    def __init__(self, parent=None):
        """Initialize plot manager."""
        super().__init__(parent)

        # Data buffers
        self.signal_history: deque = deque(maxlen=self.MAX_BUFFER)
        self.impedance_history: deque = deque(maxlen=self.MAX_BUFFER)

        # Settings
        self.current_mode = None  # "signal" or "impedance"
        self.paused = False
        self.display_mode = "Fading"  # "Real-time" or "Fading"
        self.freq_filter = None
        self.autoscale = True
        self.saved_limits = {}

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout()
        self.canvas = PlotCanvas(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    # ========================================================================
    # Data Management
    # ========================================================================

    def add_signal_frame(self, data: np.ndarray):
        """
        Add signal frame (2-column array: ADC1, ADC2).

        Args:
            data: (N, 2) numpy array
        """
        self.signal_history.append(data)
        self.current_mode = "signal"

    def add_impedance_sweep(self, data: np.ndarray):
        """
        Add impedance sweep (5-column: idx, mag, phase, accMag, accPhase).

        Args:
            data: (M, 5) numpy array
        """
        self.impedance_history.append(data)
        self.current_mode = "impedance"

    def clear_buffers(self):
        """Clear all data buffers."""
        self.signal_history.clear()
        self.impedance_history.clear()
        self.canvas.clear()

    # ========================================================================
    # Frequency Filter
    # ========================================================================

    def set_freq_filter(self, filter_text: str):
        """
        Set frequency index filter.

        Args:
            filter_text: Filter string (e.g., "0-5,8,10-19" or "skip:3,7")
        """
        if not filter_text.strip():
            self.freq_filter = None
            return

        try:
            self.freq_filter = self._parse_freq_filter(filter_text)
        except ValueError as e:
            self.freq_filter = None
            raise

    @staticmethod
    def _parse_freq_filter(text: str) -> Tuple[str, set]:
        """Parse frequency filter string."""
        text = text.strip()
        skip_mode = text.lower().startswith("skip:")
        if skip_mode:
            text = text[5:]

        indices = set()
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                lo, hi = part.split("-", 1)
                indices.update(range(int(lo), int(hi) + 1))
            else:
                indices.add(int(part))

        return ("skip", indices) if skip_mode else ("keep", indices)

    def _filter_sweep(self, sweep: np.ndarray) -> np.ndarray:
        """Apply frequency filter to sweep."""
        if self.freq_filter is None:
            return sweep

        mode, indices = self.freq_filter
        freq_indices = sweep[:, 0].astype(int)

        if mode == "keep":
            mask = np.isin(freq_indices, list(indices))
        else:  # skip
            mask = ~np.isin(freq_indices, list(indices))

        return sweep[mask]

    # ========================================================================
    # Plotting Methods
    # ========================================================================

    def plot(self, plot_type: str, fading: bool = True):
        """
        Generate plot of specified type.

        Args:
            plot_type: Plot type name
            fading: Use fading display mode
        """
        if self.paused:
            return

        # Save current limits
        if not self.autoscale:
            for i, ax in enumerate(self.canvas.fig.get_axes()):
                self.saved_limits[i] = (ax.get_xlim(), ax.get_ylim())

        self.canvas.clear()

        if plot_type == "Time Domain":
            self._plot_time_domain(fading)
        elif plot_type == "Nyquist":
            self._plot_nyquist(fading)
        elif plot_type == "Bode Magnitude":
            self._plot_bode_mag(fading)
        elif plot_type == "Bode Phase":
            self._plot_bode_phase(fading)
        elif plot_type == "Re(Z) vs Freq":
            self._plot_re_z(fading)
        elif plot_type == "Im(Z) vs Freq":
            self._plot_im_z(fading)
        elif plot_type == "Nyquist + Bode":
            self._plot_nyquist_bode(fading)
        elif plot_type == "Nyquist + Re/Im(Z)":
            self._plot_nyquist_reim(fading)

        # Restore limits
        if not self.autoscale and self.saved_limits:
            for i, ax in enumerate(self.canvas.fig.get_axes()):
                if i in self.saved_limits:
                    ax.set_xlim(self.saved_limits[i][0])
                    ax.set_ylim(self.saved_limits[i][1])

        self.canvas.fig.tight_layout()
        self.canvas.draw_idle()

    # ========================================================================
    # Signal Plots
    # ========================================================================

    def _plot_time_domain(self, fading: bool):
        """Plot time domain signal (voltage/current)."""
        ax = self.canvas.fig.add_subplot(111)
        self.canvas._style_ax(ax, "Time Domain - Voltage / Current", "Sample", "ADC Value")

        if not self.signal_history:
            return

        alphas = self._get_alpha_list(len(self.signal_history))

        if fading:
            for frame, alpha in zip(self.signal_history, alphas):
                x = np.arange(len(frame))
                ax.plot(x, frame[:, 0], color="#4fc3f7", alpha=alpha, linewidth=0.7)
                ax.plot(x, frame[:, 1], color="#ef5350", alpha=alpha, linewidth=0.7)
            ax.plot([], [], color="#4fc3f7", label="ADC1 (Voltage)")
            ax.plot([], [], color="#ef5350", label="ADC2 (Current)")
        else:
            frame = list(self.signal_history)[-1]
            x = np.arange(len(frame))
            ax.plot(x, frame[:, 0], color="#4fc3f7", linewidth=0.8, label="ADC1 (Voltage)")
            ax.plot(x, frame[:, 1], color="#ef5350", linewidth=0.8, label="ADC2 (Current)")

        ax.legend(loc="upper right", fontsize=8, facecolor="#3c3c3c",
                  edgecolor="#555", labelcolor="white")

    # ========================================================================
    # Impedance Helper Methods
    # ========================================================================

    def _compute_z(self, sweep: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute impedance components from sweep."""
        s = self._filter_sweep(sweep)
        freq_idx = s[:, 0]
        mag = s[:, 1]
        phase_deg = s[:, 2]
        phase_rad = np.deg2rad(phase_deg)
        z_real = mag * np.cos(phase_rad)
        z_imag = mag * np.sin(phase_rad)
        return freq_idx, z_real, z_imag

    def _get_alpha_list(self, count: int) -> List[float]:
        """Get alpha values for fading mode."""
        if count <= 1:
            return [1.0]
        display_count = min(count, self.MAX_DISPLAY)
        return [0.15 + 0.85 * i / (display_count - 1) for i in range(display_count)]

    # ========================================================================
    # Nyquist Plot
    # ========================================================================

    def _plot_nyquist(self, fading: bool):
        """Plot Nyquist (Re(Z) vs -Im(Z))."""
        ax = self.canvas.fig.add_subplot(111)
        self.canvas._style_ax(ax, "Nyquist Plot", "Re(Z)", "-Im(Z)")
        ax.set_aspect("equal", adjustable="datalim")

        if not self.impedance_history:
            return

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                _, z_real, z_imag = self._compute_z(sweep)
                ax.plot(z_real, -z_imag, "o-", color="#ffa726", alpha=alpha,
                        markersize=4, linewidth=0.8)
        else:
            _, z_real, z_imag = self._compute_z(list(self.impedance_history)[-1])
            ax.plot(z_real, -z_imag, "o-", color="#ffa726", markersize=5,
                    linewidth=1.0, label="Z")
            ax.legend(loc="upper right", fontsize=8, facecolor="#3c3c3c",
                      edgecolor="#555", labelcolor="white")

    # ========================================================================
    # Bode Plots
    # ========================================================================

    def _plot_bode_mag(self, fading: bool):
        """Plot Bode magnitude."""
        ax = self.canvas.fig.add_subplot(111)
        self.canvas._style_ax(ax, "Bode - Magnitude", "Frequency Index", "|Z|")

        if not self.impedance_history:
            return

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                s = self._filter_sweep(sweep)
                ax.plot(s[:, 0], s[:, 1], "o-", color="#66bb6a",
                        alpha=alpha, markersize=4, linewidth=0.8)
                ax.plot(s[:, 0], s[:, 3], "s--", color="#4fc3f7",
                        alpha=alpha * 0.7, markersize=3, linewidth=0.6)
        else:
            s = self._filter_sweep(list(self.impedance_history)[-1])
            ax.plot(s[:, 0], s[:, 1], "o-", color="#66bb6a",
                    markersize=5, linewidth=1.0, label="|Z| instant")
            ax.plot(s[:, 0], s[:, 3], "s--", color="#4fc3f7",
                    markersize=4, linewidth=0.8, label="|Z| accumulated")
            ax.legend(loc="upper right", fontsize=8, facecolor="#3c3c3c",
                      edgecolor="#555", labelcolor="white")

    def _plot_bode_phase(self, fading: bool):
        """Plot Bode phase."""
        ax = self.canvas.fig.add_subplot(111)
        self.canvas._style_ax(ax, "Bode - Phase", "Frequency Index", "Phase (deg)")

        if not self.impedance_history:
            return

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                s = self._filter_sweep(sweep)
                ax.plot(s[:, 0], s[:, 2], "o-", color="#ce93d8",
                        alpha=alpha, markersize=4, linewidth=0.8)
                ax.plot(s[:, 0], s[:, 4], "s--", color="#ffcc80",
                        alpha=alpha * 0.7, markersize=3, linewidth=0.6)
        else:
            s = self._filter_sweep(list(self.impedance_history)[-1])
            ax.plot(s[:, 0], s[:, 2], "o-", color="#ce93d8",
                    markersize=5, linewidth=1.0, label="Phase instant")
            ax.plot(s[:, 0], s[:, 4], "s--", color="#ffcc80",
                    markersize=4, linewidth=0.8, label="Phase accumulated")
            ax.legend(loc="upper right", fontsize=8, facecolor="#3c3c3c",
                      edgecolor="#555", labelcolor="white")

    # ========================================================================
    # Single Component Plots
    # ========================================================================

    def _plot_re_z(self, fading: bool):
        """Plot Re(Z) vs Frequency."""
        ax = self.canvas.fig.add_subplot(111)
        self.canvas._style_ax(ax, "Re(Z) vs Frequency Index", "Frequency Index", "Re(Z)")

        if not self.impedance_history:
            return

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                freq_idx, z_real, _ = self._compute_z(sweep)
                ax.plot(freq_idx, z_real, "o-", color="#4fc3f7", alpha=alpha,
                        markersize=4, linewidth=0.8)
        else:
            freq_idx, z_real, _ = self._compute_z(list(self.impedance_history)[-1])
            ax.plot(freq_idx, z_real, "o-", color="#4fc3f7", markersize=5,
                    linewidth=1.0, label="Re(Z)")
            ax.legend(loc="upper right", fontsize=8, facecolor="#3c3c3c",
                      edgecolor="#555", labelcolor="white")

    def _plot_im_z(self, fading: bool):
        """Plot Im(Z) vs Frequency."""
        ax = self.canvas.fig.add_subplot(111)
        self.canvas._style_ax(ax, "Im(Z) vs Frequency Index", "Frequency Index", "Im(Z)")

        if not self.impedance_history:
            return

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                freq_idx, _, z_imag = self._compute_z(sweep)
                ax.plot(freq_idx, z_imag, "o-", color="#ef5350", alpha=alpha,
                        markersize=4, linewidth=0.8)
        else:
            freq_idx, _, z_imag = self._compute_z(list(self.impedance_history)[-1])
            ax.plot(freq_idx, z_imag, "o-", color="#ef5350", markersize=5,
                    linewidth=1.0, label="Im(Z)")
            ax.legend(loc="upper right", fontsize=8, facecolor="#3c3c3c",
                      edgecolor="#555", labelcolor="white")

    # ========================================================================
    # Combined Plots
    # ========================================================================

    def _plot_nyquist_bode(self, fading: bool):
        """Plot Nyquist + Bode (3-panel layout)."""
        ax1 = self.canvas.fig.add_subplot(131)
        ax2 = self.canvas.fig.add_subplot(132)
        ax3 = self.canvas.fig.add_subplot(133)
        
        self.canvas._style_ax(ax1, "Nyquist", "Re(Z)", "-Im(Z)")
        self.canvas._style_ax(ax2, "Bode |Z|", "Freq Index", "|Z|")
        self.canvas._style_ax(ax3, "Bode Phase", "Freq Index", "Phase (deg)")

        if not self.impedance_history:
            return

        ax1.set_aspect("equal", adjustable="datalim")

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                s = self._filter_sweep(sweep)
                freq_idx, z_real, z_imag = self._compute_z(sweep)
                ax1.plot(z_real, -z_imag, "o-", color="#ffa726", alpha=alpha,
                         markersize=3, linewidth=0.7)
                ax2.plot(s[:, 0], s[:, 1], "o-", color="#66bb6a", alpha=alpha,
                         markersize=3, linewidth=0.7)
                ax2.plot(s[:, 0], s[:, 3], "s--", color="#4fc3f7", alpha=alpha * 0.7,
                         markersize=2, linewidth=0.5)
                ax3.plot(s[:, 0], s[:, 2], "o-", color="#ce93d8", alpha=alpha,
                         markersize=3, linewidth=0.7)
                ax3.plot(s[:, 0], s[:, 4], "s--", color="#ffcc80", alpha=alpha * 0.7,
                         markersize=2, linewidth=0.5)
        else:
            s = self._filter_sweep(list(self.impedance_history)[-1])
            freq_idx, z_real, z_imag = self._compute_z(list(self.impedance_history)[-1])
            ax1.plot(z_real, -z_imag, "o-", color="#ffa726", markersize=4, linewidth=0.9)
            ax2.plot(s[:, 0], s[:, 1], "o-", color="#66bb6a", markersize=4, linewidth=0.9,
                     label="instant")
            ax2.plot(s[:, 0], s[:, 3], "s--", color="#4fc3f7", markersize=3, linewidth=0.7,
                     label="acc")
            ax3.plot(s[:, 0], s[:, 2], "o-", color="#ce93d8", markersize=4, linewidth=0.9,
                     label="instant")
            ax3.plot(s[:, 0], s[:, 4], "s--", color="#ffcc80", markersize=3, linewidth=0.7,
                     label="acc")
            ax2.legend(fontsize=7, facecolor="#3c3c3c", edgecolor="#555", labelcolor="white")
            ax3.legend(fontsize=7, facecolor="#3c3c3c", edgecolor="#555", labelcolor="white")

    def _plot_nyquist_reim(self, fading: bool):
        """Plot Nyquist (left) + Re/Im(Z) (right)."""
        gs = gridspec.GridSpec(2, 2, figure=self.canvas.fig)
        ax1 = self.canvas.fig.add_subplot(gs[:, 0])
        ax2 = self.canvas.fig.add_subplot(gs[0, 1])
        ax3 = self.canvas.fig.add_subplot(gs[1, 1])
        
        self.canvas._style_ax(ax1, "Nyquist", "Re(Z)", "-Im(Z)")
        self.canvas._style_ax(ax2, "Re(Z) vs Freq", "Freq Index", "Re(Z)")
        self.canvas._style_ax(ax3, "Im(Z) vs Freq", "Freq Index", "Im(Z)")

        if not self.impedance_history:
            return

        ax1.set_aspect("equal", adjustable="datalim")

        if fading:
            sweeps = list(self.impedance_history)[-self.MAX_DISPLAY:]
            alphas = self._get_alpha_list(len(sweeps))
            for sweep, alpha in zip(sweeps, alphas):
                freq_idx, z_real, z_imag = self._compute_z(sweep)
                ax1.plot(z_real, -z_imag, "o-", color="#ffa726", alpha=alpha,
                         markersize=3, linewidth=0.7)
                ax2.plot(freq_idx, z_real, "o-", color="#4fc3f7", alpha=alpha,
                         markersize=3, linewidth=0.7)
                ax3.plot(freq_idx, z_imag, "o-", color="#ef5350", alpha=alpha,
                         markersize=3, linewidth=0.7)
        else:
            freq_idx, z_real, z_imag = self._compute_z(list(self.impedance_history)[-1])
            ax1.plot(z_real, -z_imag, "o-", color="#ffa726", markersize=4, linewidth=0.9)
            ax2.plot(freq_idx, z_real, "o-", color="#4fc3f7", markersize=4, linewidth=0.9,
                     label="Re(Z)")
            ax3.plot(freq_idx, z_imag, "o-", color="#ef5350", markersize=4, linewidth=0.9,
                     label="Im(Z)")
            ax2.legend(fontsize=7, facecolor="#3c3c3c", edgecolor="#555", labelcolor="white")
            ax3.legend(fontsize=7, facecolor="#3c3c3c", edgecolor="#555", labelcolor="white")
