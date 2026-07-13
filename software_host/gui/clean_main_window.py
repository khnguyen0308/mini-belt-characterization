"""
Clean and modern main window for Mini-Belt Characterization System.
Simplified from enhanced_main_window with better layout.
"""

import sys
import logging
import csv
import datetime
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QTextEdit, QFileDialog, QMessageBox, QLineEdit, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

import serial.tools.list_ports

from data_acquisition.serial_manager import SerialReaderThread
from gui.enhanced_plots import EnhancedPlotManager
from utils.data_storage import DataStorage
from config.settings import SERIAL_CONFIG, PLOT_CONFIG, GUI_CONFIG

logger = logging.getLogger(__name__)


class CleanMainWindow(QMainWindow):
    """Clean, modern main window with proper layout."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        self.serial_reader: Optional[SerialReaderThread] = None
        self.data_storage = DataStorage()
        self.is_recording = False
        self._record_file = None
        self._csv_writer = None
        self.measurement_count = 0

        self.setup_ui()
        self.apply_theme()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.on_update_plots)
        self.update_timer.start(100)

        self.setWindowTitle("EIS Mini-Belt Characterization - Real-time Analyzer")
        self.resize(1600, 900)

    def setup_ui(self):
        """Setup clean UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ============= LEFT PANEL (Control) =============
        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # --- Serial Group ---
        serial_group = QGroupBox("Serial Connection")
        serial_layout = QVBoxLayout()

        serial_row1 = QHBoxLayout()
        serial_row1.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(32)
        self._refresh_ports()
        serial_row1.addWidget(self.port_combo, 1)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(50)
        refresh_btn.clicked.connect(self._refresh_ports)
        serial_row1.addWidget(refresh_btn)
        serial_layout.addLayout(serial_row1)

        serial_row2 = QHBoxLayout()
        serial_row2.addWidget(QLabel("Baud:"))
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(9600, 3000000)
        self.baud_spin.setValue(115200)
        self.baud_spin.setMinimumHeight(32)
        serial_row2.addWidget(self.baud_spin, 1)
        serial_layout.addLayout(serial_row2)

        serial_row3 = QHBoxLayout()
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setMinimumHeight(40)
        self.connect_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00AA00;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #00DD00;
                border: 2px solid #006600;
            }
            QPushButton:pressed {
                background-color: #008800;
                border: 2px solid #003300;
                padding: 6px;
            }
            """
        )
        self.connect_btn.clicked.connect(self.on_connect)
        serial_row3.addWidget(self.connect_btn, 1)

        self.disconnect_btn = QPushButton("DISCONNECT")
        self.disconnect_btn.setMinimumHeight(40)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.disconnect_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #AA0000;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover:!disabled {
                background-color: #DD0000;
                border: 2px solid #660000;
            }
            QPushButton:pressed:!disabled {
                background-color: #880000;
                border: 2px solid #330000;
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
                border: 1px solid #444444;
            }
            """
        )
        self.disconnect_btn.clicked.connect(self.on_disconnect)
        serial_row3.addWidget(self.disconnect_btn, 1)

        serial_layout.addLayout(serial_row3)
        serial_group.setLayout(serial_layout)
        left_layout.addWidget(serial_group)

        # --- Plot Options Group ---
        plot_group = QGroupBox("Plot Options")
        plot_layout = QVBoxLayout()

        plot_row1 = QHBoxLayout()
        plot_row1.addWidget(QLabel("Plot Type:"))
        self.plot_type = QComboBox()
        self.plot_type.addItems([
            "Time Domain",
            "Nyquist",
            "Bode Magnitude", "Bode Phase",
            "Re(Z) vs Freq", "Im(Z) vs Freq",
            "Nyquist + Bode", "Nyquist + Re/Im(Z)"
        ])
        self.plot_type.setCurrentText("Nyquist")
        self.plot_type.setMinimumHeight(32)
        self.plot_type.currentTextChanged.connect(self.on_replot)
        plot_row1.addWidget(self.plot_type, 1)
        plot_layout.addLayout(plot_row1)

        plot_row2 = QHBoxLayout()
        plot_row2.addWidget(QLabel("Display:"))
        self.display_mode = QComboBox()
        self.display_mode.addItems(["Real-time", "Fading"])
        self.display_mode.setCurrentText("Fading")
        self.display_mode.setMinimumHeight(32)
        self.display_mode.currentTextChanged.connect(self.on_replot)
        plot_row2.addWidget(self.display_mode, 1)
        plot_layout.addLayout(plot_row2)

        plot_row3 = QHBoxLayout()
        self.pause_btn = QPushButton("⏸ PAUSE")
        self.pause_btn.setCheckable(True)
        self.pause_btn.setMinimumHeight(38)
        self.pause_btn.clicked.connect(self.on_pause_toggle)
        plot_row3.addWidget(self.pause_btn, 1)

        self.clear_btn = QPushButton("🗑 CLEAR")
        self.clear_btn.setMinimumHeight(38)
        self.clear_btn.clicked.connect(self.on_clear_data)
        plot_row3.addWidget(self.clear_btn, 1)

        plot_layout.addLayout(plot_row3)
        plot_group.setLayout(plot_layout)
        left_layout.addWidget(plot_group)

        # --- Data Management Group ---
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout()

        data_row1 = QHBoxLayout()
        self.record_btn = QPushButton("RECORD")
        self.record_btn.setCheckable(True)
        self.record_btn.setMinimumHeight(38)
        self.record_btn.clicked.connect(self.on_record_toggle)
        data_row1.addWidget(self.record_btn, 1)

        self.save_btn = QPushButton("SAVE")
        self.save_btn.setMinimumHeight(38)
        self.save_btn.clicked.connect(self.on_save_buffer)
        data_row1.addWidget(self.save_btn, 1)

        data_layout.addLayout(data_row1)

        data_row2 = QHBoxLayout()
        data_row2.addWidget(QLabel("Format:"))
        self.export_fmt = QComboBox()
        self.export_fmt.addItems(["CSV", "JSON"])
        self.export_fmt.setMinimumHeight(32)
        data_row2.addWidget(self.export_fmt, 1)

        self.export_btn = QPushButton("EXPORT")
        self.export_btn.setMinimumHeight(32)
        self.export_btn.clicked.connect(self.on_export_data)
        data_row2.addWidget(self.export_btn, 1)

        data_layout.addLayout(data_row2)
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)

        # # --- Status Info ---
        # info_layout = QHBoxLayout()
        # self.points_lbl = QLabel("Points: --")
        # self.points_lbl.setStyleSheet("color: #aaa; font-size: 10px;")
        # info_layout.addWidget(self.points_lbl)

        # self.sweeps_lbl = QLabel("Sweeps: 0")
        # self.sweeps_lbl.setStyleSheet("color: #aaa; font-size: 10px;")
        # info_layout.addWidget(self.sweeps_lbl)

        # self.rec_lbl = QLabel("")
        # self.rec_lbl.setStyleSheet("color: #ef5350; font-weight: bold;")
        # info_layout.addWidget(self.rec_lbl)

        # left_layout.addLayout(info_layout)

        # --- Status Info ---
        info_layout = QHBoxLayout()
        self.points_lbl = QLabel("Points: --")
        self.points_lbl.setStyleSheet("color: #aaa; font-size: 10px;")
        info_layout.addWidget(self.points_lbl)

        self.sweeps_lbl = QLabel("Sweeps: 0")
        self.sweeps_lbl.setStyleSheet("color: #aaa; font-size: 10px;")
        info_layout.addWidget(self.sweeps_lbl)

        # ← ADICIONE ESTAS LINHAS: Counter de medições
        self.measurement_lbl = QLabel("Measurements: 0")
        self.measurement_lbl.setStyleSheet("color: #4fc3f7; font-size: 10px; font-weight: bold;")
        info_layout.addWidget(self.measurement_lbl)

        reset_count_btn = QPushButton("↻")
        reset_count_btn.setMaximumWidth(35)
        reset_count_btn.setMaximumHeight(20)
        reset_count_btn.setStyleSheet("font-size: 10px; padding: 2px;")
        reset_count_btn.clicked.connect(self.on_reset_measurement_count)
        info_layout.addWidget(reset_count_btn)

        self.rec_lbl = QLabel("")
        self.rec_lbl.setStyleSheet("color: #ef5350; font-weight: bold;")
        info_layout.addWidget(self.rec_lbl)

        left_layout.addLayout(info_layout)

        # --- Console ---
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout()

        console_header = QHBoxLayout()
        console_header.addWidget(QLabel("Real-time Serial Data"))
        self.autoscroll_cb = QCheckBox("Auto-scroll")
        self.autoscroll_cb.setChecked(True)
        console_header.addWidget(self.autoscroll_cb)
        clear_console = QPushButton("Clear")
        clear_console.setMaximumWidth(70)
        clear_console.clicked.connect(self.on_clear_console)
        console_header.addWidget(clear_console)
        console_layout.addLayout(console_header)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Courier", 9))
        self.console.setStyleSheet(
            "background-color: #1a1a1a; color: #8c8; border: 1px solid #444; border-radius: 3px;"
        )
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        left_layout.addWidget(console_group, 1)

        left.setLayout(left_layout)
        left.setMinimumWidth(450)
        left.setMaximumWidth(650)

        # ============= RIGHT PANEL (Plot) =============
        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(0)

        self.plot_manager = EnhancedPlotManager()
        right_layout.addWidget(self.plot_manager, 1)

        right.setLayout(right_layout)

        # ============= MAIN SPLITTER =============
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter)
        central.setLayout(main_layout)

        self.statusBar().showMessage("Ready | Disconnected")

    def apply_theme(self):
        """Apply dark theme with enhanced button hover effects."""
        style = """
        QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; }
        QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 10px; padding-top: 10px; font-weight: bold; color: #e0e0e0; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QComboBox, QSpinBox, QLineEdit { background-color: #3c3c3c; color: #e0e0e0; border: 1px solid #555; border-radius: 3px; padding: 5px; }
        QComboBox QAbstractItemView { background-color: #3c3c3c; color: #e0e0e0; selection-background-color: #4fc3f7; }
        QPushButton { 
            background-color: #4fc3f7; 
            color: #1e1e1e; 
            border: none; 
            border-radius: 5px; 
            padding: 8px; 
            font-weight: bold;
            transition: all 0.2s;
        }
        QPushButton:hover { 
            background-color: #81d4fa;
            border: 2px solid #0288d1;
            transform: scale(1.02);
        }
        QPushButton:pressed { 
            background-color: #29b6f6;
            border: 2px solid #01579b;
            padding: 6px;
        }
        QPushButton:disabled { background-color: #555; color: #999; }
        QLabel { color: #e0e0e0; }
        QStatusBar { color: #aaa; border-top: 1px solid #555; }
        QCheckBox { color: #e0e0e0; }
        QCheckBox::indicator { border: 1px solid #555; background-color: #3c3c3c; width: 14px; height: 14px; border-radius: 2px; }
        QCheckBox::indicator:checked { background-color: #4fc3f7; }
        QTextEdit { background-color: #1a1a1a; color: #8c8; border: 1px solid #444; border-radius: 3px; }
        """
        self.setStyleSheet(style)

    def _refresh_ports(self):
        """Refresh COM ports."""
        self.port_combo.clear()
        ports = []
        for p in serial.tools.list_ports.comports():
            ports.append(p.device)
        if not ports:
            ports = ["COM3", "COM4", "COM5"]
        self.port_combo.addItems(ports)

    def on_connect(self):
        """Connect to serial device."""
        port = self.port_combo.currentText()
        baud = self.baud_spin.value()

        self.serial_reader = SerialReaderThread(port, baud)
        self.serial_reader.signal_frame.connect(self._on_signal_frame)
        self.serial_reader.impedance_sweep.connect(self._on_impedance_sweep)
        self.serial_reader.mode_detected.connect(self._on_mode_detected)
        self.serial_reader.raw_line.connect(self._on_raw_line)
        self.serial_reader.status_msg.connect(self._on_status)

        self.serial_reader.start()

        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.port_combo.setEnabled(False)
        self.baud_spin.setEnabled(False)

    def on_disconnect(self):
        """Disconnect from serial device."""
        if self.serial_reader:
            self.serial_reader.stop()
            self.serial_reader = None

        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.baud_spin.setEnabled(True)
        self.statusBar().showMessage("Disconnected")

    def _on_signal_frame(self, data):
        """Handle signal frame."""
        self.plot_manager.add_signal_frame(data)
        self.sweeps_lbl.setText(f"Frames: {len(self.plot_manager.signal_history)}")

    # def _on_impedance_sweep(self, data):
    #     """Handle impedance sweep."""
    #     self.plot_manager.add_impedance_sweep(data)
    #     self.sweeps_lbl.setText(f"Sweeps: {len(self.plot_manager.impedance_history)}")

    def _on_impedance_sweep(self, data):
        """Handle impedance sweep."""
        self.plot_manager.add_impedance_sweep(data)
        self.sweeps_lbl.setText(f"Sweeps: {len(self.plot_manager.impedance_history)}")
        
        self.measurement_count += 1
        self.measurement_lbl.setText(f"Measurements: {self.measurement_count}")

    def _on_mode_detected(self, mode: str, n_points: int):
        """Handle mode detection."""
        self.plot_manager.current_mode = mode
        self.points_lbl.setText(f"Points: {n_points}")
        self.console.append(f"Mode: {mode.upper()} ({n_points} points)")

    def _on_raw_line(self, line: str):
        """Handle raw serial line."""
        self.console.append(line)
        
        # Record if recording
        if self.is_recording and self._csv_writer:
            ts = datetime.datetime.now().isoformat()
            self._csv_writer.writerow([ts, line])
            self._record_file.flush()
        
        if self.autoscroll_cb.isChecked():
            self.console.verticalScrollBar().setValue(
                self.console.verticalScrollBar().maximum()
            )
        if len(self.console.toPlainText()) > 50000:
            self.on_clear_console()

    def _on_status(self, msg: str):
        """Handle status message."""
        self.statusBar().showMessage(msg)
        self.console.append(f"[{msg}]")

    def on_reset_measurement_count(self):
        """Reset measurement counter."""
        self.measurement_count = 0
        self.measurement_lbl.setText("Measurements: 0")
        self.console.append("✓ Measurement counter reset")

    def on_replot(self):
        """Redraw plot."""
        if self.pause_btn.isChecked():
            return
        plot_type = self.plot_type.currentText()
        fading = self.display_mode.currentText() == "Fading"
        self.plot_manager.plot(plot_type, fading=fading)

    def on_pause_toggle(self):
        """Toggle pause."""
        if self.pause_btn.isChecked():
            self.pause_btn.setText("▶ RESUME")
            self.pause_btn.setStyleSheet(
                "background-color: #ffa726; color: #1e1e1e; border-radius: 5px; font-weight: bold;"
            )
        else:
            self.pause_btn.setText("⏸ PAUSE")
            self.pause_btn.setStyleSheet("")
            self.on_replot()

    def on_clear_data(self):
        """Clear all data."""
        self.plot_manager.clear_buffers()
        self.sweeps_lbl.setText("Sweeps: 0")
        self.console.append("✓ Data cleared")

    def on_record_toggle(self):
        """Toggle recording."""
        if self.record_btn.isChecked():
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Recording", f"record_{ts}.csv", "CSV Files (*.csv)"
            )
            if not path:
                self.record_btn.setChecked(False)
                return

            self._record_file = open(path, "w", newline="")
            self._csv_writer = csv.writer(self._record_file)
            self._csv_writer.writerow(["timestamp", "data"])
            self.is_recording = True

            self.rec_lbl.setText("REC")
            self.record_btn.setText("STOP REC")
            self.record_btn.setStyleSheet(
                "background-color: #ef5350; color: white; border-radius: 5px; font-weight: bold;"
            )
            self.console.append(f"✓ Recording to {path}")
        else:
            if self._record_file:
                self._record_file.close()
            self.is_recording = False
            self.rec_lbl.setText("")
            self.record_btn.setText("RECORD")
            self.record_btn.setStyleSheet("")
            self.console.append("✓ Recording stopped")

    def on_save_buffer(self):
        """Save buffer to file."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Buffer", f"buffer_{ts}.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                if self.plot_manager.impedance_history:
                    writer.writerow(["sweep", "idx", "mag", "phase", "acc_mag", "acc_phase"])
                    for i, sweep in enumerate(self.plot_manager.impedance_history):
                        for row in sweep:
                            writer.writerow([i] + list(row))
            self.console.append(f"Buffer saved to {path}")
        except Exception as e:
            self.console.append(f"Error: {e}")

    def on_export_data(self):
        """Export data."""
        self.on_save_buffer()

    def on_clear_console(self):
        """Clear console."""
        self.console.clear()

    def on_update_plots(self):
        """Update plots periodically."""
        self.on_replot()

    def closeEvent(self, event):
        """Handle close."""
        if self.serial_reader:
            self.serial_reader.stop()
        self.update_timer.stop()
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = CleanMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
