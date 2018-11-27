from __future__ import print_function
from lib.iso14229_1 import ServiceID
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
