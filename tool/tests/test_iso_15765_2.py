from __future__ import print_function
from .mock_ecu import MockEcuIsoTp
from lib import iso15765_2
import can
import datetime  # TODO remove
import unittest


class IsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x100A
    ARB_ID_RESPONSE = 0x100B

    TIMEOUT_SECONDS = 3

    def setUp(self):
        # Initialize virtual CAN bus
        can_bus = can.interface.Bus("test", bustype="virtual")
        # Initialize mock ECU
        self.ecu = MockEcuIsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=can_bus)
        self.ecu.add_listener(self.ecu.message_handler)
        # Setup ISO-TP layer
        self.tp = iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=can_bus)

    def tearDown(self):
        if isinstance(self.tp, iso15765_2.IsoTp):
            self.tp.__exit__(None, None, None)

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
