from __future__ import print_function
import can
import time


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    virtual_test_bus = can.interface.Bus("test", bustype="virtual")

    def __init__(self, bus=virtual_test_bus):
        self.bus = bus
        self.notifier = can.Notifier(self.bus, listeners=[])

    def __enter__(self):
        return self

    def add_listener(self, listener):
        self.notifier.listeners.append(listener)

    def clear_listeners(self):
        self.notifier.listeners = []

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear_listeners()
        # Prevent threading errors during shutdown
        self.notifier.running.clear()
        time.sleep(0.1)


class MockEcuIso14229(MockEcu):
    """ISO-14229-1 (Unified Diagnostic Services) mock ECU handler"""

    def __init__(self, arb_id_request, arb_id_response, bus=MockEcu.virtual_test_bus):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_ISO_14229_REQUEST = arb_id_request
        self.ARBITRATION_ID_ISO_14229_RESPONSE = arb_id_response

    def message_handler(self, message):
        assert isinstance(message, can.Message)
        # TODO Implement logic to actually respond to requests
        if message.arbitration_id == self.ARBITRATION_ID_ISO_14229_REQUEST:
            print(message)
