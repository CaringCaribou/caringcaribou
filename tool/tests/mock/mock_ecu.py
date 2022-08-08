from __future__ import print_function
from lib.can_actions import DEFAULT_INTERFACE, pcan
import can
from can.interfaces.pcan import PcanBus


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    DELAY_BEFORE_RESPONSE = 0.01

    def __init__(self, bus=None):
        self.message_process = None
        if pcan:
            self.bus = PcanBus()
        elif bus is None:
            self.bus = can.Bus(DEFAULT_INTERFACE)
        else:
            self.bus = bus

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bus.shutdown()
