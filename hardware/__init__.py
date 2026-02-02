"""
Hardware Module for UFO Galaxy

Hardware-level monitoring and control for 24/7 operation:
- Temperature monitoring
- Power management
- Hardware watchdog
- UPS monitoring
"""

from .hardware_monitor import (
    HardwareMonitor,
    TemperatureReading,
    PowerStatus,
    HardwareMetrics,
    HardwareState,
    start_hardware_monitor
)

__all__ = [
    "HardwareMonitor",
    "TemperatureReading",
    "PowerStatus",
    "HardwareMetrics",
    "HardwareState",
    "start_hardware_monitor"
]
