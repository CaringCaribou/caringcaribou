from __future__ import print_function
from lib import iso14229_1, iso15765_2
import can
import time


class MockEcu:
    """Mock ECU base class, used for running tests over a virtual CAN bus"""

    # TODO Remove this and require it to be passed explicitly?
    virtual_test_bus = can.interface.Bus("test", bustype="virtual")
    DELAY_BEFORE_RESPONSE = 0.05

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
        self.iso_tp = iso15765_2.IsoTp(arb_id_request=self.ARBITRATION_ID_REQUEST,
                                       arb_id_response=self.ARBITRATION_ID_RESPONSE,
                                       bus=bus)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear_listeners()

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

    REQUEST_POSITIVE = 0x01
    REQUEST_NEGATIVE = 0x02

    REQUEST_IDENTIFIER_VALID = 0xA001
    REQUEST_IDENTIFIER_INVALID = 0xA002
    REQUEST_VALUE = [0xC0, 0xFF, 0xEE]

    REQUEST_ADDRESS_LENGTH_AND_FORMAT = 0x22
    REQUEST_ADDRESS = 0x0001
    REQUEST_DATA_SIZE = 0x10
    DATA = list(range(0x14))

    def __init__(self, arb_id_request, arb_id_response, bus=MockEcu.virtual_test_bus):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_ISO_14229_REQUEST = arb_id_request
        self.ARBITRATION_ID_ISO_14229_RESPONSE = arb_id_response
        self.iso_tp = iso15765_2.IsoTp(arb_id_request=self.ARBITRATION_ID_ISO_14229_REQUEST,
                                       arb_id_response=self.ARBITRATION_ID_ISO_14229_RESPONSE,
                                       bus=bus)
        self.diagnostics = iso14229_1.Iso14229_1(tp=self.iso_tp)

    def message_handler(self, message):
        """
        Logic for responding to incoming messages.

        :param message: Incoming can.Message
        :return: None
        """
        assert isinstance(message, can.Message)
        if message.arbitration_id == self.ARBITRATION_ID_ISO_14229_REQUEST:
            # Hack to decode data without running full indication
            _, data = self.iso_tp.decode_sf(message.data)
            iso14229_service = data[0]
            # Simulate a small delay before responding
            time.sleep(self.DELAY_BEFORE_RESPONSE)
            # Handle different services
            response_data = None
            if iso14229_service == iso14229_1.Iso14229_1_id.READ_DATA_BY_IDENTIFIER:
                # Read data by identifier
                request = data[2]
                if request == self.REQUEST_POSITIVE:
                    # Request for positive response
                    response_data = [iso14229_1.Iso14229_1_nrc.POSITIVE_RESPONSE]
                elif request == self.REQUEST_NEGATIVE:
                    # Request for negative response
                    response_data = [iso14229_1.Iso14229_1_id.NEGATIVE_RESPONSE]
                else:
                    # Unmatched request - use a general reject response
                    response_data = [iso14229_1.Iso14229_1_nrc.GENERAL_REJECT]
            elif iso14229_service == iso14229_1.Iso14229_1_id.WRITE_DATA_BY_IDENTIFIER:
                # Write data by identifier
                identifier_start_position = 1
                identifier_length = 2
                identifier = iso14229_1.int_from_byte_list(data,
                                                           identifier_start_position,
                                                           identifier_length)
                request_data = data[3:]
                if identifier == self.REQUEST_IDENTIFIER_VALID:
                    # Request for positive response
                    response_data = [iso14229_1.Iso14229_1_nrc.POSITIVE_RESPONSE]
                elif identifier == self.REQUEST_IDENTIFIER_INVALID:
                    # Request for negative response
                    response_data = [iso14229_1.Iso14229_1_id.NEGATIVE_RESPONSE]
                else:
                    # Unmatched request - use a general reject response
                    response_data = [iso14229_1.Iso14229_1_nrc.GENERAL_REJECT]
            elif iso14229_service == iso14229_1.Iso14229_1_id.READ_MEMORY_BY_ADDRESS:
                address_field_size = (data[1] >> 4) & 0xF
                data_length_field_size = (data[1] & 0xF)
                address_start_position = 2
                data_length_start_position = 4
                start_address = iso14229_1.int_from_byte_list(data,
                                                              address_start_position,
                                                              address_field_size)
                data_length = iso14229_1.int_from_byte_list(data,
                                                            data_length_start_position,
                                                            data_length_field_size)
                end_address = start_address + data_length
                if 0 <= start_address <= end_address <= len(self.DATA):
                    memory_data = self.DATA[start_address:end_address]
                    response_data = [iso14229_1.Iso14229_1_nrc.POSITIVE_RESPONSE] + memory_data
                else:
                    response_data = [iso14229_1.Iso14229_1_nrc.GENERAL_REJECT]
            if response_data:
                self.diagnostics.send_response(response_data)
            else:
                print("Unmapped message in {0}.message_handler:\n  {1}".format(self.__class__.__name__, message))
