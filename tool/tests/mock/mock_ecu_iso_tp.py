import multiprocessing
import time

from lib import iso15765_2
from tests.mock.mock_ecu import MockEcu


class MockEcuIsoTp(MockEcu):
    """ISO-15765-2 (ISO-TP) mock ECU handler"""

    MOCK_SINGLE_FRAME_REQUEST = [0x01, 0xAA, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF]
    MOCK_SINGLE_FRAME_RESPONSE = list(range(0, 0x07))

    MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST = [0xC0, 0xFF, 0xEE, 0x00, 0x02, 0x00, 0x00]
    MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE = list(range(0, 0x0D))

    MOCK_MULTI_FRAME_LONG_MESSAGE_REQUEST = [0x02, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
    MOCK_MULTI_FRAME_LONG_MESSAGE_RESPONSE = list(range(0, 34))

    def __init__(self, arb_id_request, arb_id_response, bus=None):
        MockEcu.__init__(self, bus)
        self.ARBITRATION_ID_REQUEST = arb_id_request
        self.ARBITRATION_ID_RESPONSE = arb_id_response
        self.iso_tp = iso15765_2.IsoTp(arb_id_request=self.ARBITRATION_ID_REQUEST,
                                       arb_id_response=self.ARBITRATION_ID_RESPONSE,
                                       bus=self.bus)

    def __enter__(self):
        """
        Run server when entering a "with" statement.

        :return: self
        """
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanup when leaving a "with" statement.

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return: None
        """
        MockEcu.__exit__(self, None, None, None)
        self.stop_server()

    def start_server(self):
        """
        Starts a server process, listening for and responding to incoming ISO-TP messages.

        Since the server runs in a separate process, this function is non-blocking.

        :return: None
        """
        self.message_process = multiprocessing.Process(target=self._serve_forever)
        self.message_process.start()

    def stop_server(self):
        """
        Stops the server process.

        :return: None
        """
        MockEcu.__exit__(self, None, None, None)
        if isinstance(self.message_process, multiprocessing.Process):
            self.message_process.terminate()
            self.message_process.join()
        else:
            print("stop_server: No server was running")

    def _serve_forever(self):
        """
        Listens for incoming ISO-TP messages and responds to them. This function is blocking.

        :return: None
        """
        while True:
            msg = self.iso_tp.indication()
            if msg is not None:
                # ISO-TP message received
                self.message_handler(msg)

    def message_handler(self, data):
        """
        Logic for responding to incoming messages

        :param data: list of data bytes in incoming message
        :return: None
        """
        # Simulate a small delay before responding
        time.sleep(self.DELAY_BEFORE_RESPONSE)
        if data == self.MOCK_SINGLE_FRAME_REQUEST:
                self.iso_tp.send_response(self.MOCK_SINGLE_FRAME_RESPONSE)
        elif data == self.MOCK_MULTI_FRAME_TWO_MESSAGES_REQUEST:
                self.iso_tp.send_response(self.MOCK_MULTI_FRAME_TWO_MESSAGES_RESPONSE)
        elif data == self.MOCK_MULTI_FRAME_LONG_MESSAGE_REQUEST:
                self.iso_tp.send_response(self.MOCK_MULTI_FRAME_LONG_MESSAGE_RESPONSE)
        else:
            print("Unmapped message in {0}.message_handler:\n  {1}".format(self.__class__.__name__, data))
