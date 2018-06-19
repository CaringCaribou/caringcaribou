from __future__ import print_function
from lib import iso15765_2
import can
import time


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    virtual_test_bus = can.interface.Bus("test", bustype="virtual")
    DELAY_BEFORE_RESPONSE = 0.001

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
        self.bus.shutdown()


class MockEcuIsoTp(MockEcu):
    """ISO-15765-2 (ISO-TP) mock ECU handler"""

    MOCK_SINGLE_FRAME_REQUEST = [0x01, 0xAA, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF]
    MOCK_SINGLE_FRAME_RESPONSE = list(range(0, 0x07))

    MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST = [0xC0, 0xFF, 0xEE, 0x00, 0x02, 0x00, 0x00]
    MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE = list(range(0, 0x0D))

    MOCK_MULTI_FRAME_LONG_MESSAGE_REQUEST = [0x02, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
    MOCK_MULTI_FRAME_LONG_MESSAGE_RESPONSE = list(range(0, 34))

    def __init__(self, arb_id_request, arb_id_response, bus=MockEcu.virtual_test_bus):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_REQUEST = arb_id_request
        self.ARBITRATION_ID_RESPONSE = arb_id_response
        self.iso_tp = iso15765_2.IsoTp(self.ARBITRATION_ID_REQUEST, self.ARBITRATION_ID_RESPONSE, bus=bus)

    def message_handler(self, message):
        """
        Logic for responding to incoming messages.

        :param message: Incoming can.Message
        :return: None
        """
        assert isinstance(message, can.Message)
        if message.arbitration_id == self.ARBITRATION_ID_REQUEST:
            # Hack to decode data without running full indication
            _, data = self.iso_tp.decode_sf(message.data)
            data = list(data)
            # Simulate a small delay before responding
            time.sleep(self.DELAY_BEFORE_RESPONSE)
            if data == self.MOCK_SINGLE_FRAME_REQUEST:
                self.iso_tp.send_response(self.MOCK_SINGLE_FRAME_RESPONSE)
            elif data == self.MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST:
                self.iso_tp.send_response(self.MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE)
            elif data == self.MOCK_MULTI_FRAME_LONG_MESSAGE_REQUEST:
                self.iso_tp.send_response(self.MOCK_MULTI_FRAME_LONG_MESSAGE_RESPONSE)
            else:
                print("Unmapped message:", message)


class MockEcuIso14229(MockEcuIsoTp, MockEcu):
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
