from lib.iso15765_2 import IsoTp
from lib.iso14229_1 import *
from lib.can_actions import int_from_byte_list
from tests.mock.mock_ecu import MockEcu
from tests.mock.mock_ecu_iso_tp import MockEcuIsoTp


class MockEcuIso14229(MockEcuIsoTp, MockEcu):
    """ISO-14229-1 (Unified Diagnostic Services) mock ECU handler"""

    IDENTIFIER_REQUEST_POSITIVE = 0x01
    IDENTIFIER_REQUEST_POSITIVE_RESPONSE = 0x72
    IDENTIFIER_REQUEST_NEGATIVE = 0x02

    REQUEST_IDENTIFIER_VALID = 0xA001
    REQUEST_IDENTIFIER_INVALID = 0xA002
    REQUEST_VALUE = [0xC0, 0xFF, 0xEE]

    REQUEST_ADDRESS_LENGTH_AND_FORMAT = 0x22
    REQUEST_ADDRESS = 0x0001
    REQUEST_DATA_SIZE = 0x10
    DATA = list(range(0x14))

    # TODO Use dynamic seed value and verify keys using a simple algorithm
    SECURITY_ACCESS_SEED = [0x36, 0x57]
    SECURITY_ACCESS_KEY = [0xC9, 0xA9]

    def __init__(self, arb_id_request, arb_id_response, bus=None):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_ISO_14229_REQUEST = arb_id_request
        self.ARBITRATION_ID_ISO_14229_RESPONSE = arb_id_response
        # Set CAN filter to only listen to incoming requests on the correct arbitration ID
        arbitration_id_filter = [{"can_id": arb_id_request, "can_mask": 0x1fffffff}]
        self.bus.set_filters(arbitration_id_filter)
        # Setup ISO-TP using the filtered bus
        self.iso_tp = IsoTp(arb_id_request=self.ARBITRATION_ID_ISO_14229_REQUEST,
                            arb_id_response=self.ARBITRATION_ID_ISO_14229_RESPONSE,
                            bus=self.bus)
        # Setup diagnostics on top of ISO-TP
        self.diagnostics = Iso14229_1(tp=self.iso_tp)

    def __exit__(self, exc_type, exc_val, exc_tb):
        MockEcuIsoTp.__exit__(self, None, None, None)

    @staticmethod
    def create_positive_response(request_service_id, response_data=None):
        """
        Returns data for a positive response of 'request_service_id' with an optional 'response_data' payload

        :param request_service_id: Service ID (SIDRQ) of the incoming request
        :param response_data: List of data bytes to transmit in the response
        :return: List of bytes to be sent as data payload in the response
        """
        # Positive response uses a response service ID (SIDPR) based on the request service ID (SIDRQ)
        service_response_id = Iso14229_1.get_service_response_id(request_service_id)
        response = [service_response_id]
        # Append payload
        if response_data is not None:
            response += response_data
        return response

    @staticmethod
    def create_negative_response(request_service_id, nrc):
        """
        Returns data for a negative response of 'request_service_id' with negative response code 'nrc'

        :param request_service_id: Service ID (SIDRQ) of the incoming request
        :param nrc: Negative response code (NRC_)
        :return: List of bytes to be sent as data payload in the response
        """
        response = [Constants.NR_SI,
                    request_service_id,
                    nrc]
        return response

    def message_handler(self, data):
        """
        Logic for responding to incoming messages

        :param data: list of data bytes in incoming message
        :return: None
        """
        assert isinstance(data, list)
        try:
            service_id = data[0]
            # Handle different services
            if service_id == ServiceID.DIAGNOSTIC_SESSION_CONTROL:
                # 0x10 Diagnostic session control
                response_data = self.handle_diagnostic_session_control(data)
            elif service_id == ServiceID.ECU_RESET:
                # 0x11 ECU reset
                response_data = self.handle_ecu_reset(data)
            elif service_id == ServiceID.READ_DATA_BY_IDENTIFIER:
                # 0x22 Read data by identifier
                response_data = self.handle_read_data_by_identifier(data)
            elif service_id == ServiceID.READ_MEMORY_BY_ADDRESS:
                # 0x23 Read memory by address
                response_data = self.handle_read_memory_by_address(data)
            elif service_id == ServiceID.SECURITY_ACCESS:
                # 0x27 Security access
                response_data = self.handle_security_access(data)
            elif service_id == ServiceID.WRITE_DATA_BY_IDENTIFIER:
                # 0x2E Write data by identifier
                response_data = self.handle_write_data_by_identifier(data)
            else:
                # Unsupported service
                response_data = self.handle_unsupported_service(data)
        except IndexError:
            # Parsing failed due to invalid message structure
            response_data = self.handle_service_error(data)

        # This check makes it possible to support services where a response should not be sent
        if response_data is not None:
            # Simulate a small delay before responding
            time.sleep(self.DELAY_BEFORE_RESPONSE)
            self.diagnostics.send_response(response_data)

    def handle_unsupported_service(self, data):
        """Provides a standard response for unmapped services, by responding with NRC Service Not Supported"""
        service_id = data[0]
        nrc = NegativeResponseCodes.SERVICE_NOT_SUPPORTED
        response_data = self.create_negative_response(service_id, nrc)
        return response_data

    def handle_service_error(self, data):
        """Provides a standard response for failed service requests"""
        service_id = data[0]
        nrc = NegativeResponseCodes.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT
        response_data = self.create_negative_response(service_id, nrc)
        return response_data

    def handle_diagnostic_session_control(self, data):
        """Evaluates a diagnostic session control request and returns a response"""
        service_id = data[0]
        # TODO Handle different values?
        session_type = data[1]
        response_data = self.create_positive_response(service_id)
        return response_data

    def handle_read_data_by_identifier(self, data):
        """
        Evaluates a read data by identifier request and returns the appropriate response

        :param data: Data from incoming request
        :return: Response to be sent
        """
        service_id = data[0]
        request = data[2]

        if request == self.IDENTIFIER_REQUEST_POSITIVE:
            # Request for positive response
            # TODO Actually read a parameter from memory
            payload = [self.IDENTIFIER_REQUEST_POSITIVE_RESPONSE]
            response_data = self.create_positive_response(service_id, payload)
        elif request == self.IDENTIFIER_REQUEST_NEGATIVE:
            # Request for negative response - use Conditions Not Correct
            nrc = NegativeResponseCodes.CONDITIONS_NOT_CORRECT
            response_data = self.create_negative_response(service_id, nrc)
        else:
            # Unmatched request - use a general reject response
            nrc = NegativeResponseCodes.GENERAL_REJECT
            response_data = self.create_negative_response(service_id, nrc)
        return response_data

    def handle_write_data_by_identifier(self, data):
        """
        Evaluates a write data by identifier request and returns the appropriate response

        :param data: Data from incoming request
        :return: Response to be sent
        """
        service_id = data[0]

        identifier_start_position = 1
        identifier_length = 2
        identifier = int_from_byte_list(data,
                                        identifier_start_position,
                                        identifier_length)
        request_data = data[3:]
        # TODO Actually write data to memory
        if identifier == self.REQUEST_IDENTIFIER_VALID:
            # Request for positive response
            # Standard specifies the response payload to be an echo of the data identifier from the request
            payload = data[identifier_start_position:identifier_start_position + identifier_length]
            response_data = self.create_positive_response(service_id, payload)
        elif identifier == self.REQUEST_IDENTIFIER_INVALID:
            # Request for negative response - use Conditions Not Correct
            nrc = NegativeResponseCodes.CONDITIONS_NOT_CORRECT
            response_data = self.create_negative_response(service_id, nrc)
        else:
            # Unmatched request - use a general reject response
            nrc = NegativeResponseCodes.GENERAL_REJECT
            response_data = self.create_negative_response(service_id, nrc)
        return response_data

    def handle_read_memory_by_address(self, data):
        """
        Evaluates a read memory by address request and returns the appropriate response

        :param data: Data from incoming request
        :return: Response to be sent
        """
        service_id = data[0]
        address_field_size = (data[1] >> 4) & 0xF
        data_length_field_size = (data[1] & 0xF)
        address_start_position = 2
        data_length_start_position = 4

        start_address = int_from_byte_list(data, address_start_position, address_field_size)
        data_length = int_from_byte_list(data, data_length_start_position, data_length_field_size)
        end_address = start_address + data_length
        if 0 <= start_address <= end_address <= len(self.DATA):
            memory_data = self.DATA[start_address:end_address]
            response_data = self.create_positive_response(service_id, memory_data)
        else:
            nrc = NegativeResponseCodes.REQUEST_OUT_OF_RANGE
            response_data = self.create_negative_response(service_id, nrc)
        return response_data

    def handle_ecu_reset(self, data):
        """
        Evaluates an ECU reset request and returns the appropriate response

        :param data: Data from incoming request
        :return: Response to be sent
        """
        service_id = data[0]
        subfunction = data[1]
        reset_type = subfunction & 0x7F
        suppress_positive_response = subfunction >> 7

        reset_types = Services.EcuReset.ResetType

        if reset_type in [reset_types.HARD_RESET, reset_types.KEY_OFF_ON_RESET, reset_types.SOFT_RESET]:
            if suppress_positive_response:
                response_data = None
            else:
                response_data = self.create_positive_response(service_id, [reset_type])
        else:
            nrc = NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED
            response_data = self.create_negative_response(service_id, nrc)
        return response_data

    def handle_security_access(self, data):
        """
        Evaluates security access requests (both "Request seed" and "Send key") and returns the appropriate response

        :param data: Data from incoming request
        :return: Response to be sent
        """
        service_id = data[0]
        subfunction = data[1]
        level = subfunction & 0x7F

        service_handler = Services.SecurityAccess.RequestSeedOrSendKey()
        if service_handler.is_valid_request_seed_level(level):
            # Request seed handling
            payload = [level]
            payload.extend(self.SECURITY_ACCESS_SEED)
            response_data = self.create_positive_response(service_id, payload)
        elif service_handler.is_valid_send_key_level(level):
            # Send key handling
            expected_key = self.SECURITY_ACCESS_KEY
            received_key = data[2:]
            if received_key == expected_key:
                # Correct key
                response_data = self.create_positive_response(service_id, [level])
            else:
                # Invalid key
                nrc = NegativeResponseCodes.INVALID_KEY
                response_data = self.create_negative_response(service_id, nrc)
        else:
            # Unsupported subfunction
            nrc = NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED
            response_data = self.create_negative_response(service_id, nrc)
        return response_data
