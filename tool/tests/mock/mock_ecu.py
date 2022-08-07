from __future__ import print_function
from lib.can_actions import DEFAULT_INTERFACE, pcan, global_bus
import can
from can.interfaces.pcan import PcanBus


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    DELAY_BEFORE_RESPONSE = 0.01

    def __init__(self, bus=None):
        self.bus = global_bus

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bus.shutdown()
