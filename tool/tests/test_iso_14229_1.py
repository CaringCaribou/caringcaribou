from __future__ import print_function
from .mock_ecu import MockEcuIso14229
from lib import iso14229_1
from lib import iso15765_2
import can
import unittest


class DiagnosticsOverIsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x200C
    ARB_ID_RESPONSE = 0x200D

    def setUp(self):
        # Initialize virtual CAN bus
        can_bus = can.interface.Bus("test", bustype="virtual")
        mock_ecu_can_bus = can.interface.Bus("test", bustype="virtual")
        # Initialize mock ECU
        self.ecu = MockEcuIso14229(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=mock_ecu_can_bus)
        self.ecu.add_listener(self.ecu.message_handler)
        # Setup diagnostics on top of ISO-TP layer
        self.tp = iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=can_bus)
        self.diagnostics = iso14229_1.Iso14229_1(self.tp)
        # Reduce timeout value to speed up testing
        self.diagnostics.P3_CLIENT = 0.5

    def tearDown(self):
        if isinstance(self.diagnostics, iso14229_1.Iso14229_1):
            self.diagnostics.__exit__(None, None, None)
        if isinstance(self.tp, iso15765_2.IsoTp):
            self.tp.__exit__(None, None, None)
        self.ecu.clear_listeners()

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
        self.assertEqual(response_sid, expected_response_sid, "Response SID (SIDPR) does not match expected value")
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
        service_id = iso14229_1.Iso14229_1_id.READ_DATA_BY_IDENTIFIER
        expected_response = [MockEcuIso14229.IDENTIFIER_REQUEST_POSITIVE_RESPONSE]
        result = self.diagnostics.read_data_by_identifier([MockEcuIso14229.IDENTIFIER_REQUEST_POSITIVE])
        self.verify_positive_response(service_id, result, expected_response)

    def test_read_data_by_identifier_failure(self):
        service_id = iso14229_1.Iso14229_1_id.READ_DATA_BY_IDENTIFIER
        expected_nrc = iso14229_1.Iso14229_1_nrc.CONDITIONS_NOT_CORRECT
        result = self.diagnostics.read_data_by_identifier([MockEcuIso14229.IDENTIFIER_REQUEST_NEGATIVE])
        self.verify_negative_response(service_id, result, expected_nrc)

    def test_write_data_by_identifier_success(self):
        service_id = iso14229_1.Iso14229_1_id.WRITE_DATA_BY_IDENTIFIER
        request_identifier = MockEcuIso14229.REQUEST_IDENTIFIER_VALID
        expected_response = [(request_identifier >> 8) & 0xFF, request_identifier & 0xFF]
        result = self.diagnostics.write_data_by_identifier(request_identifier,
                                                           MockEcuIso14229.REQUEST_VALUE)
        self.verify_positive_response(service_id, result, expected_response)

    def test_write_data_by_identifier_failure(self):
        service_id = iso14229_1.Iso14229_1_id.WRITE_DATA_BY_IDENTIFIER
        expected_nrc = iso14229_1.Iso14229_1_nrc.CONDITIONS_NOT_CORRECT
        result = self.diagnostics.write_data_by_identifier(MockEcuIso14229.REQUEST_IDENTIFIER_INVALID,
                                                           MockEcuIso14229.REQUEST_VALUE)
        self.verify_negative_response(service_id, result, expected_nrc)

    def test_read_memory_by_address_success(self):
        service_id = iso14229_1.Iso14229_1_id.READ_MEMORY_BY_ADDRESS
        address_length_and_format = MockEcuIso14229.REQUEST_ADDRESS_LENGTH_AND_FORMAT
        start_address = MockEcuIso14229.REQUEST_ADDRESS
        request_data_size = MockEcuIso14229.REQUEST_DATA_SIZE
        end_address = start_address + request_data_size
        result = self.diagnostics.read_memory_by_address(address_length_and_format,
                                                         start_address,
                                                         request_data_size)
        expected_response = MockEcuIso14229.DATA[start_address:end_address]
        self.verify_positive_response(service_id, result, expected_response)

    def test_read_memory_by_address_failure_on_invalid_length(self):
        service_id = iso14229_1.Iso14229_1_id.READ_MEMORY_BY_ADDRESS
        expected_nrc = iso14229_1.Iso14229_1_nrc.REQUEST_OUT_OF_RANGE
        address_length_and_format = MockEcuIso14229.REQUEST_ADDRESS_LENGTH_AND_FORMAT
        start_address = 0
        # Request memory outside of the available address space, which should result in a failure
        request_data_size = len(MockEcuIso14229.DATA) + 1
        result = self.diagnostics.read_memory_by_address(address_length_and_format,
                                                         start_address,
                                                         request_data_size)
        self.verify_negative_response(service_id, result, expected_nrc)
