from __future__ import print_function
from tests.mock_ecu import MockEcuIsoTp
from lib import iso15765_2
from lib.can_actions import DEFAULT_INTERFACE
import can
import unittest


class IsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x100A
    ARB_ID_RESPONSE = 0x100B

    def setUp(self):
        # Initialize mock ECU
        self.ecu = MockEcuIsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)
        self.ecu.start_server()
        # Initialize virtual CAN bus
        can_bus = can.Bus(DEFAULT_INTERFACE, bustype="socketcan")
        # Setup ISO-TP layer
        self.tp = iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=can_bus)

    def tearDown(self):
        if isinstance(self.ecu, MockEcuIsoTp):
            self.ecu.__exit__(None, None, None)
        if isinstance(self.tp, iso15765_2.IsoTp):
            self.tp.__exit__(None, None, None)

    def test_create_iso_15765_2(self):
        self.assertIsInstance(self.tp, iso15765_2.IsoTp, "Failed to initialize ISO-TP")

    def test_single_frame(self):
        # Send request
        self.tp.send_request(MockEcuIsoTp.MOCK_SINGLE_FRAME_REQUEST)
        # Receive response
        response = self.tp.indication()
        # Validate response
        self.assertIsInstance(response, list, "No SF response received")
        self.assertEqual(response, MockEcuIsoTp.MOCK_SINGLE_FRAME_RESPONSE)

    def test_multi_frame_two_frames(self):
        # Send request
        self.tp.send_request(MockEcuIsoTp.MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST)
        # Receive response
        response = self.tp.indication()
        # Validate response
        self.assertIsInstance(response, list, "No multi-frame response received")
        self.assertEqual(response, MockEcuIsoTp.MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE)

    def test_multi_frame_long_message(self):
        # Send request
        self.tp.send_request(MockEcuIsoTp.MOCK_MULTI_FRAME_LONG_MESSAGE_REQUEST)
        # Receive response
        response = self.tp.indication()
        # Validate response
        self.assertIsInstance(response, list, "No multi-frame response received")
        self.assertEqual(response, MockEcuIsoTp.MOCK_MULTI_FRAME_LONG_MESSAGE_RESPONSE)

    def test_fail_too_long_message(self):
        with self.assertRaises(ValueError):
            max_allowed_length = iso15765_2.IsoTp.MAX_MESSAGE_LENGTH
            too_long_message = [0x0] * (max_allowed_length + 1)
            self.tp.send_request(too_long_message)
