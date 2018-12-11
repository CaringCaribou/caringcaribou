from __future__ import print_function
from lib.iso14229_1 import Constants, Iso14229_1, NegativeResponseCodes, ServiceID, Services
from tests.mock.mock_ecu_uds import MockEcuIso14229
from modules import uds
import unittest


class UdsModuleTestCase(unittest.TestCase):
    ARB_ID_REQUEST = 0x300E
    ARB_ID_RESPONSE = 0x300F

    # Timeout (in seconds) when waiting for response during bruteforce
    BRUTEFORCE_TIMEOUT = 0.01

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
        timeout = self.BRUTEFORCE_TIMEOUT
        print_results = False
        # Perform UDS discovery
        result = uds.uds_discovery(start_arb_id, end_arb_id, blacklist, auto_blacklist_duration, timeout, print_results)
        expected_result = [(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)]
        self.assertListEqual(result, expected_result, "UDS discovery gave '{0}', expected '{1}'".format(
            result, expected_result))

    def test_uds_discovery_blacklist(self):
        # Discovery arguments
        start_arb_id = self.ARB_ID_REQUEST - 5
        end_arb_id = self.ARB_ID_REQUEST + 5
        # Blacklist the arbitration ID used for response
        blacklist = [self.ARB_ID_RESPONSE]
        auto_blacklist_duration = 0
        timeout = self.BRUTEFORCE_TIMEOUT
        print_results = False
        # Perform UDS discovery
        result = uds.uds_discovery(start_arb_id, end_arb_id, blacklist, auto_blacklist_duration, timeout, print_results)
        # No results expected due to blacklist
        expected_result = []
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
                                       timeout=self.BRUTEFORCE_TIMEOUT,
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
                                       timeout=self.BRUTEFORCE_TIMEOUT,
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

    def test_security_access_request_seed_send_key_success(self):
        level_seed = 0x01
        data_record = []
        timeout = None
        expected_response_id = Iso14229_1.get_service_response_id(Services.SecurityAccess.service_id)
        # Request seed
        seed_result = uds.request_seed(arb_id_request=self.ARB_ID_REQUEST,
                                       arb_id_response=self.ARB_ID_RESPONSE,
                                       level=level_seed,
                                       data_record=data_record,
                                       timeout=timeout)
        expected_seed = self.ecu.SECURITY_ACCESS_SEED
        expected_seed_result = [expected_response_id, level_seed] + expected_seed
        self.assertListEqual(seed_result,
                             expected_seed_result,
                             "Security Access: Request seed gave '{0}', expected '{1}'".format(
                                 seed_result, expected_seed_result))
        # Send key
        level_key = uds.Services.SecurityAccess.RequestSeedOrSendKey().get_send_key_for_request_seed(level_seed)
        key = self.ecu.SECURITY_ACCESS_KEY
        key_result = uds.send_key(arb_id_request=self.ARB_ID_REQUEST,
                                  arb_id_response=self.ARB_ID_RESPONSE,
                                  level=level_key,
                                  key=key,
                                  timeout=timeout)
        expected_key_result = [expected_response_id, level_key]
        self.assertListEqual(key_result,
                             expected_key_result,
                             "Security Access: Send key gave '{0}', expected '{1}'".format(
                                 key_result, expected_key_result))

    def test_security_access_request_seed_invalid_level(self):
        # Level 0x00 lies outside of allowed interval
        level = 0x00
        data_record = []
        timeout = None
        with self.assertRaises(ValueError):
            uds.request_seed(arb_id_request=self.ARB_ID_REQUEST,
                             arb_id_response=self.ARB_ID_RESPONSE,
                             level=level,
                             data_record=data_record,
                             timeout=timeout)
