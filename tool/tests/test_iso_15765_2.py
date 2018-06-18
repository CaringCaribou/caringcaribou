from __future__ import print_function
from .mock_ecu import MockEcuIsoTp
from lib import iso15765_2
import can
import unittest


class IsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x100A
    ARB_ID_RESPONSE = 0x100B

    TIMEOUT_SECONDS = 1

    def setUp(self):
        # Initialize virtual CAN bus
        can_bus = can.interface.Bus("test", bustype="virtual")
        mock_ecu_can_bus = can.interface.Bus("test", bustype="virtual")
        # Initialize mock ECU
        self.ecu = MockEcuIsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=mock_ecu_can_bus)
        self.ecu.add_listener(self.ecu.message_handler)
        # Setup ISO-TP layer
        self.tp = iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=can_bus)

    def tearDown(self):
        if isinstance(self.tp, iso15765_2.IsoTp):
            self.tp.__exit__(None, None, None)
        if isinstance(self.ecu, MockEcuIsoTp):
            self.ecu.__exit__(None, None, None)

    def test_create_iso_15765_2(self):
        self.assertIsInstance(self.tp, iso15765_2.IsoTp, "Failed to initialize ISO-TP")

    def test_single_frame(self):
        # Send request
        self.tp.request(MockEcuIsoTp.MOCK_SINGLE_FRAME_REQUEST)
        # Receive response
        response = self.tp.indication(self.TIMEOUT_SECONDS)
        # Validate response
        self.assertIsNotNone(response, "No SF response received")
        self.assertEqual(list(response), MockEcuIsoTp.MOCK_SINGLE_FRAME_RESPONSE[1:])

    def test_multi_frame_two_frames(self):
        # Send request
        self.tp.request(MockEcuIsoTp.MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST)
        # Receive response
        response = self.tp.indication(self.TIMEOUT_SECONDS)
        self.assertIsNotNone(response, "No multi-frame response received")
        # TODO Compare to actual value from MockEcu class
        self.assertEqual(list(response), list(range(13)))
