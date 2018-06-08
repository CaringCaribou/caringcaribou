from __future__ import print_function
import can
import time


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    virtual_test_bus = can.interface.Bus("test", bustype="virtual")
    DELAY_BEFORE_RESPONSE = 0.03

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


class MockEcuIsoTp(MockEcu):
    """ISO-15765-2 (ISO-TP) mock ECU handler"""

    MOCK_SINGLE_FRAME_REQUEST = [0x07, 0x01, 0x02, 0x03, 0x04, 0xAA, 0xAB]
    MOCK_SINGLE_FRAME_RESPONSE = [0x01, 0x11, 0x22, 0x33, 0x44]

    def __init__(self, arb_id_request, arb_id_response, bus=MockEcu.virtual_test_bus):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_REQUEST = arb_id_request
        self.ARBITRATION_ID_RESPONSE = arb_id_response

    def message_handler(self, message):
        """
        Logic for responding to incoming messages.

        :param message: Incoming can.Message
        :return: None
        """
        assert isinstance(message, can.Message)
        if message.arbitration_id == self.ARBITRATION_ID_REQUEST:
            # Simulate a small delay before responding
            time.sleep(self.DELAY_BEFORE_RESPONSE)
            if list(message.data)[1:] == self.MOCK_SINGLE_FRAME_REQUEST:
                msg = can.Message(arbitration_id=self.ARBITRATION_ID_RESPONSE, data=self.MOCK_SINGLE_FRAME_RESPONSE)
                self.bus.send(msg)
            else:
                # TODO Add more cases here
                print("Unmapped")


class MockEcuIso14229(MockEcu):
    """ISO-14229-1 (Unified Diagnostic Services) mock ECU handler"""

    def __init__(self, arb_id_request, arb_id_response, bus=MockEcu.virtual_test_bus):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_ISO_14229_REQUEST = arb_id_request
        self.ARBITRATION_ID_ISO_14229_RESPONSE = arb_id_response

    def message_handler(self, message):
        """
        Logic for responding to incoming messages.

        :param message: Incoming can.Message
        :return: None
        """
        assert isinstance(message, can.Message)
        # TODO Implement logic to actually respond to requests
        if message.arbitration_id == self.ARBITRATION_ID_ISO_14229_REQUEST:
            print(message)
