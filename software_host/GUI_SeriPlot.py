#!/usr/bin/env python3


import sys
import logging
import argparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mini_belt_eis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Mini-Belt Characterization System - Real-time EIS GUI'
    )
    parser.add_argument(
        '--port',
        type=str,
        default='COM3',
        help='Serial port for EIS device (default: COM3)'
    )
    parser.add_argument(
        '--baudrate',
        type=int,
        default=115200,
        help='Serial communication baud rate (default: 115200)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
    '--mock',
    action='store_true',
    help='Run with mock data (simulated EIS device, no hardware needed)'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # logger.info("=" * 70)
    # logger.info("Mini-Belt Characterization System - Real-time EIS GUI")
    # logger.info("=" * 70)
    # logger.info(f"Serial Port: {args.port}")
    # logger.info(f"Baud Rate: {args.baudrate}")
    # logger.info("=" * 70)

    try:
        from PyQt6.QtWidgets import QApplication
        from gui.clean_main_window import CleanMainWindow as MainWindow
        from data_acquisition.eis_device import EISDevice
        import threading
        import numpy as np
        import time
    
        # If mock mode, patch EISDevice
        if args.mock:
            logger.info("MOCK MODE ENABLED - Using simulated data")
            
            original_connect = EISDevice.connect
            
            def mock_connect(self):
                self.running = True
                self.measurement_thread = threading.Thread(
                    target=self._mock_measurement_loop, daemon=True
                )
                self.measurement_thread.start()
                logger.info("✓ Mock EIS Device connected (simulated, no hardware)")
                return True
            
            def mock_measurement_loop(self):
                """
                Generate synthetic EIS data in STM32 format.
                
                Format: Index, Magnitude, Phase, AccMagnitude, AccPhase
                - Index: 0-19 (cycles through 20 frequency points)
                - Magnitude: Instantaneous measurement
                - Phase: Instantaneous measurement
                - AccMagnitude: Accumulated/Averaged Magnitude (more stable)
                - AccPhase: Accumulated/Averaged Phase (more stable)
                
                Note: AccMagnitude and AccPhase are used by GUI for plotting (more accurate)
                """
                R, C = 1000, 100e-9
                index = 0
                
                # Keep running averages for accumulated values
                acc_mag_buffer = []
                acc_phase_buffer = []
                buffer_size = 5  # Average over 5 measurements
                
                while self.running:
                    if self.is_measuring:
                        try:
                            # Cycle through 20 indices (0-19) like real STM32
                            idx = index % 20
                            
                            # Calculate frequency for this index (10 Hz - 100 kHz, 20 points)
                            freq = 10 * (10000 ** (idx / 19)) if idx < 20 else 10
                            omega = 2 * np.pi * freq
                            
                            # Calculate impedance (RC circuit)
                            z_real = R + np.random.normal(0, 10)
                            z_imag = -1/(omega*C) + np.random.normal(0, 5)
                            
                            # Calculate magnitude and phase (instantaneous)
                            magnitude = np.sqrt(z_real**2 + z_imag**2)
                            phase = np.degrees(np.arctan2(z_imag, z_real))
                            
                            # Simulate accumulated values (averaged/filtered)
                            acc_mag_buffer.append(magnitude)
                            acc_phase_buffer.append(phase)
                            
                            # Keep buffer size at buffer_size
                            if len(acc_mag_buffer) > buffer_size:
                                acc_mag_buffer.pop(0)
                                acc_phase_buffer.pop(0)
                            
                            # Calculate averages
                            acc_magnitude = np.mean(acc_mag_buffer) if acc_mag_buffer else magnitude
                            acc_phase = np.mean(acc_phase_buffer) if acc_phase_buffer else phase
                            
                            # Format as STM32: "Index,Magnitude,Phase,AccMagnitude,AccPhase"
                            data_str = f"{idx},{magnitude:.3f},{phase:.3f},{acc_magnitude:.3f},{acc_phase:.3f}"
                            
                            # Parse using the new format parser
                            from data_acquisition.eis_device import EISMeasurement
                            measurement = EISMeasurement(
                                frequency=freq,
                                impedance_real=z_real,
                                impedance_imag=z_imag,
                                magnitude=acc_magnitude,  # Use accumulated for storage
                                phase=acc_phase,  # Use accumulated for storage
                                timestamp=time.time()
                            )
                            
                            self.current_measurement = measurement
                            self.measurement_history.append(measurement)
                            self.measurement_count += 1
                            
                            for callback in self.callbacks:
                                try:
                                    callback(measurement)
                                except:
                                    pass
                            
                            index += 1
                            time.sleep(0.1)
                        except Exception as e:
                            logger.debug(f"Mock measurement error: {e}")
                            time.sleep(0.1)
                    else:
                        time.sleep(0.1)
            
            EISDevice.connect = mock_connect
            EISDevice._mock_measurement_loop = mock_measurement_loop
    
        # Create Qt application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
    
        logger.info("Launching GUI...")
        window = MainWindow()
    
        # Override serial port if provided
        if args.port:
            # Ensure the port exists in the combo box
            if window.port_combo.findText(args.port) == -1:
                # Port not found, add it
                window.port_combo.addItem(args.port)
                logger.info(f"Added {args.port} to available ports")
            
            window.port_combo.setCurrentText(args.port)
            logger.info(f"Selected port: {args.port}")
    
        window.show()
        logger.info("GUI window displayed")
    
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
    
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please ensure PyQt6 and pyqtgraph are installed:")
        logger.error("  pip install PyQt6 pyqtgraph numpy pyserial pandas scikit-learn scipy")
        return 1
    
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
