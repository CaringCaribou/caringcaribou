from __future__ import print_function
from lib import iso15765_2
import can
import unittest


class IsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x2000
    ARB_ID_RESPONSE = 0x4000

    def test_create_iso_tp(self):
        bus = can.interface.Bus("test", bustype="virtual")
        with iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE, bus=bus) as tp:
            self.assertTrue(isinstance(tp, iso15765_2.IsoTp), "Failed to initialize ISO-15765-2")

    # TODO Write tests
