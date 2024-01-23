from __future__ import print_function
from caringcaribou.utils.can_actions import DEFAULT_INTERFACE
from caringcaribou.tests.mock.mock_ecu_uds import MockEcuIso14229
from caringcaribou.utils import iso14229_1
from caringcaribou.utils import iso15765_2
import can
import unittest


class DiagnosticsOverIsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x200C
    ARB_ID_RESPONSE = 0x200D

    def setUp(self):
        # Initialize mock ECU
        self.ecu = MockEcuIso14229(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)
        self.ecu.start_server()
        # Initialize virtual CAN bus
        can_bus = can.Bus(DEFAULT_INTERFACE)
        # Setup diagnostics on top of ISO-TP layer
        self.tp = iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=can_bus)
        self.diagnostics = iso14229_1.Iso14229_1(self.tp)
        # Reduce timeout value to speed up testing
        self.diagnostics.P3_CLIENT = 0.5

    def tearDown(self):
        if isinstance(self.ecu, MockEcuIso14229):
            self.ecu.__exit__(None, None, None)
        if isinstance(self.diagnostics, iso14229_1.Iso14229_1):
            self.diagnostics.__exit__(None, None, None)
        if isinstance(self.tp, iso15765_2.IsoTp):
            self.tp.__exit__(None, None, None)

    def verify_positive_response(self, service_id, response, expected_data):
        """
        Verifies that 'response' is a valid positive response for 'service_id' with a payload matching 'expected_data'

        :param service_id: Service ID (SIDRQ) of the request
        :param response: Response data
        :param expected_data: Expected data payload in 'response'
        :return: None
        """
        self.assertIsInstance(response, list, "No response was received")
        self.assertGreater(len(response), 1, "Expected positive response length >1, got {0}".format(response))
        response_sid = response[0]
        response_data = response[1:]
        expected_response_sid = self.diagnostics.get_service_response_id(service_id)
        self.assertEqual(response_sid, expected_response_sid, "Response SID (SIDPR) '{0}' does not match expected "
                                                              "value '{1}'".format(hex(response_sid),
                                                                                   hex(expected_response_sid)))
        self.assertTrue(self.diagnostics.is_positive_response(response))
        self.assertListEqual(response_data, expected_data)

    def verify_negative_response(self, service_id, response, expected_nrc):
        """
        Verifies that 'response' is a valid negative response for 'service_id' matching 'expected_nrc'

        :param service_id: Service ID (SIDRQ) of the request
        :param response: Response data
        :param expected_nrc: Expected negative response code (NRC)
        :return: None
        """
        self.assertIsInstance(response, list, "No response was received")
        self.assertEqual(len(response), 3, "Negative response should have length '3', got {0}".format(response))
        request_sid = response[1]
        self.assertEqual(request_sid, service_id, "Request SID (SIDRQ) of response does not match expected value")
        self.assertFalse(self.diagnostics.is_positive_response(response))
        response_nrc = response[2]
        self.assertEqual(response_nrc, expected_nrc, "NRC of response does not match expected value")

    def test_create_iso_14229_1(self):
        self.assertIsInstance(self.diagnostics, iso14229_1.Iso14229_1, "Failed to initialize ISO-14229-1")

    def test_read_data_by_identifier_success(self):
        service_id = iso14229_1.ServiceID.READ_DATA_BY_IDENTIFIER
        identifier = [MockEcuIso14229.IDENTIFIER_REQUEST_POSITIVE]
        expected_response = [0x00,
                             MockEcuIso14229.IDENTIFIER_REQUEST_POSITIVE,
                             MockEcuIso14229.IDENTIFIER_REQUEST_POSITIVE_RESPONSE]
        result = self.diagnostics.read_data_by_identifier(identifier=identifier)

        # result looks like [0x62, DID_ADDR_UPPER, DID_ADDR_LOWER, RESULT]
        #rsp_pos = result[0]
        #rx_identifier = result[1:3]
        print(result)
        self.verify_positive_response(service_id, result, expected_response)

    def test_read_data_by_identifier_failure(self):
        service_id = iso14229_1.ServiceID.READ_DATA_BY_IDENTIFIER
        identifier = [MockEcuIso14229.IDENTIFIER_REQUEST_NEGATIVE]
        expected_nrc = iso14229_1.NegativeResponseCodes.CONDITIONS_NOT_CORRECT
        result = self.diagnostics.read_data_by_identifier(identifier=identifier)
        self.verify_negative_response(service_id, result, expected_nrc)

    def test_write_data_by_identifier_success(self):
        service_id = iso14229_1.ServiceID.WRITE_DATA_BY_IDENTIFIER
        request_identifier = MockEcuIso14229.REQUEST_IDENTIFIER_VALID
        request_data = MockEcuIso14229.REQUEST_VALUE
        expected_response = [(request_identifier >> 8) & 0xFF, request_identifier & 0xFF]
        result = self.diagnostics.write_data_by_identifier(identifier=request_identifier,
                                                           data=request_data)
        self.verify_positive_response(service_id, result, expected_response)

    def test_write_data_by_identifier_failure(self):
        service_id = iso14229_1.ServiceID.WRITE_DATA_BY_IDENTIFIER
        request_identifier = MockEcuIso14229.REQUEST_IDENTIFIER_INVALID
        request_data = MockEcuIso14229.REQUEST_VALUE
        expected_nrc = iso14229_1.NegativeResponseCodes.CONDITIONS_NOT_CORRECT
        result = self.diagnostics.write_data_by_identifier(identifier=request_identifier,
                                                           data=request_data)
        self.verify_negative_response(service_id, result, expected_nrc)

    def test_read_memory_by_address_success(self):
        service_id = iso14229_1.ServiceID.READ_MEMORY_BY_ADDRESS
        length_and_format = MockEcuIso14229.REQUEST_ADDRESS_LENGTH_AND_FORMAT
        start_address = MockEcuIso14229.REQUEST_ADDRESS
        request_data_size = MockEcuIso14229.REQUEST_DATA_SIZE
        end_address = start_address + request_data_size
        result = self.diagnostics.read_memory_by_address(address_and_length_format=length_and_format,
                                                         memory_address=start_address,
                                                         memory_size=request_data_size)
        expected_response = MockEcuIso14229.DATA[start_address:end_address]
        self.verify_positive_response(service_id, result, expected_response)

    def test_read_memory_by_address_failure_on_invalid_length(self):
        service_id = iso14229_1.ServiceID.READ_MEMORY_BY_ADDRESS
        expected_nrc = iso14229_1.NegativeResponseCodes.REQUEST_OUT_OF_RANGE
        length_and_format = MockEcuIso14229.REQUEST_ADDRESS_LENGTH_AND_FORMAT
        start_address = 0
        # Request memory outside the available address space, which should result in a failure
        request_data_size = len(MockEcuIso14229.DATA) + 1
        result = self.diagnostics.read_memory_by_address(address_and_length_format=length_and_format,
                                                         memory_address=start_address,
                                                         memory_size=request_data_size)
        self.verify_negative_response(service_id, result, expected_nrc)

    def test_ecu_reset_success(self):
        service_id = iso14229_1.ServiceID.ECU_RESET
        reset_type = iso14229_1.Services.EcuReset.ResetType.HARD_RESET
        expected_response = [reset_type]
        result = self.diagnostics.ecu_reset(reset_type=reset_type)
        self.verify_positive_response(service_id, result, expected_response)

    def test_ecu_reset_failure_on_invalid_reset_type(self):
        service_id = iso14229_1.ServiceID.ECU_RESET
        expected_nrc = iso14229_1.NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED
        # This reset type is ISO SAE Reserved and thus an invalid value
        reset_type = 0x00
        result = self.diagnostics.ecu_reset(reset_type=reset_type)
        self.verify_negative_response(service_id, result, expected_nrc)

    def test_ecu_reset_success_suppress_positive_response(self):
        reset_type = iso14229_1.Services.EcuReset.ResetType.SOFT_RESET
        # Suppress positive response
        reset_type |= 0x80
        result = self.diagnostics.ecu_reset(reset_type=reset_type)
        self.assertIsNone(result)

    def test_ecu_reset_failure_suppress_positive_response(self):
        service_id = iso14229_1.ServiceID.ECU_RESET
        expected_nrc = iso14229_1.NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED
        # ISO SAE Reserved reset type 0x00, with suppress positive response bit set
        reset_type = 0x80
        result = self.diagnostics.ecu_reset(reset_type=reset_type)
        self.verify_negative_response(service_id, result, expected_nrc)
