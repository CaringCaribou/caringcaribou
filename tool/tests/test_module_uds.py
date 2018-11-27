from __future__ import print_function
from lib.iso14229_1 import Constants, Iso14229_1, NegativeResponseCodes, ServiceID, Services
from tests.mock.mock_ecu_uds import MockEcuIso14229
from modules import uds
import unittest


class UdsModuleTestCase(unittest.TestCase):
    ARB_ID_REQUEST = 0x300E
    ARB_ID_RESPONSE = 0x300F

    # Delay (in seconds) to wait for response during bruteforce
    BRUTEFORCE_DELAY = 0.01

    def setUp(self):
        # Initialize mock ECU
        self.ecu = MockEcuIso14229(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)
        # Remove response delay
        self.ecu.DELAY_BEFORE_RESPONSE = 0.0
        self.ecu.start_server()

    def tearDown(self):
        if isinstance(self.ecu, MockEcuIso14229):
            self.ecu.__exit__(None, None, None)

    def test_uds_discovery(self):
        # Discovery arguments
        start_arb_id = self.ARB_ID_REQUEST - 5
        end_arb_id = self.ARB_ID_REQUEST + 5
        blacklist = []
        auto_blacklist_duration = 0
        delay = self.BRUTEFORCE_DELAY
        print_results = False
        # Perform UDS discovery
        result = uds.uds_discovery(start_arb_id, end_arb_id, blacklist, auto_blacklist_duration, delay, print_results)
        expected_result = [(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)]
        self.assertListEqual(result, expected_result, "UDS discovery gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_service_discovery(self):
        # Service discovery arguments
        range_start = 0x09
        range_end = 0x13
        print_results = False
        # Perform service discovery
        result = uds.service_discovery(arb_id_request=self.ARB_ID_REQUEST,
                                       arb_id_response=self.ARB_ID_RESPONSE,
                                       request_delay=self.BRUTEFORCE_DELAY,
                                       min_id=range_start,
                                       max_id=range_end,
                                       print_results=print_results)
        # Supported services within specified range
        expected_result = [ServiceID.DIAGNOSTIC_SESSION_CONTROL, ServiceID.ECU_RESET]
        self.assertListEqual(result, expected_result, "UDS service discovery gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_service_discovery_empty_range(self):
        # Service discovery arguments
        range_start = 0x00
        range_end = 0x05
        print_results = False
        # Perform service discovery
        result = uds.service_discovery(arb_id_request=self.ARB_ID_REQUEST,
                                       arb_id_response=self.ARB_ID_RESPONSE,
                                       request_delay=self.BRUTEFORCE_DELAY,
                                       min_id=range_start,
                                       max_id=range_end,
                                       print_results=print_results)
        # No services should be found within range
        expected_result = []
        self.assertListEqual(result, expected_result, "UDS service discovery gave '{0}', expected no hits".format(
            result))

    def test_ecu_reset_hard_reset_success(self):
        # ECU Reset arguments
        reset_type = Services.EcuReset.ResetType.HARD_RESET
        timeout = None
        # Perform ECU Reset
        result = uds.ecu_reset(arb_id_request=self.ARB_ID_REQUEST,
                               arb_id_response=self.ARB_ID_RESPONSE,
                               reset_type=reset_type,
                               timeout=timeout)
        # Expected response format for successful request
        expected_response_id = Iso14229_1.get_service_response_id(Services.EcuReset.service_id)
        expected_result = [expected_response_id, reset_type]
        self.assertListEqual(result, expected_result, "ECU Reset gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_ecu_reset_unsupported_reset_type_failure(self):
        # Invalid reset type
        reset_type = 0x00
        timeout = None
        # Perform ECU Reset
        result = uds.ecu_reset(arb_id_request=self.ARB_ID_REQUEST,
                               arb_id_response=self.ARB_ID_RESPONSE,
                               reset_type=reset_type,
                               timeout=timeout)
        # Expected response format for invalid request
        expected_response_id = Services.EcuReset.service_id
        expected_nrc = NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED
        expected_result = [Constants.NR_SI, expected_response_id, expected_nrc]
        self.assertListEqual(result, expected_result, "ECU Reset gave '{0}', expected '{1}'".format(
            result, expected_result))
