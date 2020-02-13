from modules import send
import unittest


class SendFileParserTestCase(unittest.TestCase):

    RESULT_DATA_C0FFEE = [0xc0, 0xff, 0xee]
    RESULT_DATA_DEAD_CAFE = [0xde, 0xad, 0xca, 0xfe]

    def test_parse_candump_line(self):
        line = "(1499197954.029156) can0 123#c0ffee"
        message, timestamp = send.parse_candump_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_20(self):
        # Parse message format for python-can 2.0
        line = "Timestamp:        0.000000        ID: 017a    000    DLC: 3    c0 ff ee"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_21(self):
        # Parse message format for python-can 2.1
        line = "Timestamp:        0.000000        ID: 0000    S          DLC: 3    c0 ff ee"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_21_flags(self):
        # Parse message format for python-can 2.1 with flags
        line = "Timestamp:        0.000000    ID: 00000000    X E R      DLC: 4    de ad ca fe"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_DEAD_CAFE)

    def test_parse_pythoncan_line_v_30_channel(self):
        # Parse message format for python-can 3.0 with channel
        line = "Timestamp:        0.000000    ID: 00000000    X                DLC:  3    c0 ff ee " \
               "                   Channel: vcan0"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_C0FFEE)

    def test_parse_pythoncan_line_v_30_flags(self):
        # Parse message format for python-can 3.0 with flags
        line = "Timestamp:        0.000000    ID: 00000000    X   R            DLC:  4    de ad ca fe"
        message, timestamp = send.parse_pythoncan_line(line, None, None)
        self.assertListEqual(message.data, self.RESULT_DATA_DEAD_CAFE)
