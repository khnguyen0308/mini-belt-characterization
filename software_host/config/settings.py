"""
Configuration and settings for Mini-Belt Characterization System GUI.

IMPORTANT - STM32 Configuration:
==================================
As of May 2026, the GUI is designed to RECEIVE real-time data from STM32.
STM32 measurement parameters (Frequency Start/End, AC Amplitude, Points per Decade)
should be configured DIRECTLY ON THE STM32 DEVICE, not through the GUI.

The GUI will:
- Display real-time Nyquist and Bode plots
- Show statistics and analysis
- Export data to CSV/JSON
- All Acc (Accumulated) values for higher accuracy

If you need to configure STM32 from GUI in the future, you can uncomment
the measurement settings section in gui/widgets.py and implement the
send_measurement_config_to_device() function in gui/main_window.py.
"""

# Serial Communication Settings
SERIAL_CONFIG = {
    'port': 'COM3',  # Change based on your STM32 device
    'baudrate': 115200,
    'timeout': 1,
    'write_timeout': 1,
}

# EIS Measurement Settings
EIS_CONFIG = {
    'frequency_start': 10,      # Hz
    'frequency_end': 100000,    # Hz
    'points_per_decade': 10,
    'ac_amplitude': 100,        # mV
    'settling_time': 0.5,       # seconds
}

# Plot Settings
PLOT_CONFIG = {
    'nyquist_points': 200,      # Keep last N points
    'bode_points': 200,
    'update_interval': 100,     # ms
    'grid_enabled': True,
    'legend_enabled': True,
}

# GUI Settings
GUI_CONFIG = {
    'window_width': 1400,
    'window_height': 900,
    'window_title': 'Mini-Belt Characterization System - Real-time EIS Analyzer',
    'theme': 'dark',  # 'light' or 'dark'
}

# Data Storage Settings
STORAGE_CONFIG = {
    'export_format': 'csv',  # 'csv' or 'json'
    'auto_save': True,
    'save_interval': 60,  # seconds
    'data_directory': './data',
}

# Plotting Colors and Styles
COLORS = {
    'nyquist': '#00FF00',  # Green
    'bode_magnitude': '#0099FF',  # Blue
    'bode_phase': '#FF6600',  # Orange
    'background': '#1a1a1a',
    'grid': '#333333',
}

# Frequency array for Multisine excitation
MULTISINE_CONFIG = {
    'enable': True,
    'frequency_resolution': 0.1,  # Hz
    'harmonics_count': 50,
}
