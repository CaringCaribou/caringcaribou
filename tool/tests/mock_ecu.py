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
        self.bus.shutdown()


class MockEcuIsoTp(MockEcu):
    """ISO-15765-2 (ISO-TP) mock ECU handler"""

    MOCK_SINGLE_FRAME_REQUEST = [0xC0, 0xFF, 0xEE, 0x01, 0xAA, 0xAB, 0xAC]
    MOCK_SINGLE_FRAME_RESPONSE = [0x01, 0x00, 0x02, 0x03]

    MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST = [0xC0, 0xFF, 0xEE, 0x00, 0x02, 0x00, 0x00]
    MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE = [
        [0x10, 0x0d, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05],
        [0x21, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c]
    ]

    FLOW_CONTROL_FRAME = [0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    MAX_WAIT_FLOW_CONTROL = 0.3

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
                msg = can.Message(arbitration_id=self.ARBITRATION_ID_RESPONSE,
                                  data=self.MOCK_SINGLE_FRAME_RESPONSE)
                self.bus.send(msg)
            elif list(message.data[1:]) == self.MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST:
                msg = can.Message(arbitration_id=self.ARBITRATION_ID_RESPONSE,
                                  data=self.MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE[0])
                self.bus.send(msg)
                # Receive flow control message
                flow_control = self.receive_flow_control()
                if not flow_control:
                    return
                msg = can.Message(arbitration_id=self.ARBITRATION_ID_RESPONSE,
                                  data=self.MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE[1])
                self.bus.send(msg)
            else:
                # TODO Add more cases here
                print("Unmapped message:", message)

    def receive_flow_control(self):
        """
        Listens for a flow control frame.

        :return: True if flow control message was received and False otherwise
        """
        msg = self.bus.recv(self.MAX_WAIT_FLOW_CONTROL)
        if msg is None:
            return False
        return list(msg.data) == self.FLOW_CONTROL_FRAME


class MockEcuIso14229(MockEcu, MockEcuIsoTp):
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
