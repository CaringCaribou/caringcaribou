from lib import iso14229_1
from lib import iso15765_2
import unittest


class DiagnosticsOverIsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x2000
    ARB_ID_RESPONSE = 0x4000

    def setUp(self):
        # Setup diagnostics on top of ISO-TP layer
        self.tp = iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE)
        self.diagnostics = iso14229_1.Iso14229_1(self.tp)

    def tearDown(self):
        pass

    def test_create_iso_14229_1(self):
        with iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE) as tp:
            with iso14229_1.Iso14229_1(tp) as diagnostics:
                self.assertTrue(isinstance(diagnostics, iso14229_1.Iso14229_1), "Failed to initialize ISO-14229-1")

    def test_read_data_by_identifier(self):
        self.diagnostics.read_data_by_identifier([0xa4])

    def test_write_data_by_identifier(self):
        self.diagnostics.write_data_by_identifier(0xa4, [0x11, 0x22])
