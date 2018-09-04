from lib.can_actions import DEFAULT_INTERFACE
import can
import datetime
import time


class IsoTp:
    """
    Implementation of ISO-15765-2, also known as ISO-TP. This is a multi-frame messaging protocol
    over CAN which allows message payloads of up to 4095 bytes.
    """

    MAX_SF_LENGTH = 7
    MAX_FF_LENGTH = 6
    MAX_CF_LENGTH = 7

    SF_PCI_LENGTH = 1
    CF_PCI_LENGTH = 1
    FF_PCI_LENGTH = 2
    FC_PCI_LENGTH = 3

    FC_FS_CTS = 0
    FC_FS_WAIT = 1

    SF_FRAME_ID = 0
    FF_FRAME_ID = 1
    CF_FRAME_ID = 2
    FC_FRAME_ID = 3

    N_BS_TIMEOUT = 1.5

    MAX_FRAME_LENGTH = 8
    MAX_MESSAGE_LENGTH = 4095

    def __init__(self, arb_id_request, arb_id_response, bus=None):
        # Setting default bus to None rather than the actual bus prevents a CanError when
        # called with a virtual CAN bus, while the OS is lacking a working CAN interface
        if bus is None:
            self.bus = can.Bus(DEFAULT_INTERFACE, "socketcan")
        else:
            self.bus = bus
        self.arb_id_request = arb_id_request
        self.arb_id_response = arb_id_response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bus.shutdown()

    def send_message(self, data, arbitration_id):
        """
        Transmits a message using 'arbitration_id' and 'data' on 'self.bus'

        :param data: Data to send
        :param arbitration_id: Arbitration ID to use
        :return: None
        """
        msg = can.Message(arbitration_id=arbitration_id, data=data)
        self.bus.send(msg)

    def decode_sf(self, frame):
        """
        Decodes a singe frame (SF) message

        :param frame: Frame to decode
        :return: Tuple of single frame data length (SF_DL) and data if valid,
                 Tuple of None, None otherwise
        """
        if len(frame) >= self.SF_PCI_LENGTH:
            sf_dl = frame[0] & 0xF
            data = frame[1:]
            return sf_dl, list(data)
        else:
            return None, None

    def decode_ff(self, frame):
        """
        Decodes a first frame (FF) message

        :param frame: Frame to decode
        :return: Tuple of first frame data length (FF_DL) and data if valid,
                 Tuple of None, None otherwise
        """
        if len(frame) >= self.FF_PCI_LENGTH:
            ff_dl = ((frame[0] & 0xF) << 8) | frame[1]
            data = frame[2:]
            return ff_dl, list(data)
        else:
            return None, None

    def decode_cf(self, frame):
        """
        Decodes a consecutive frame (CF) message

        :param frame: Frame to decode
        :return: Tuple of sequence number (SN) and data if valid,
                 Tuple of None, None otherwise
        """
        if len(frame) >= self.CF_PCI_LENGTH:
            sn = frame[0] & 0xF
            data = frame[1:]
            return sn, list(data)
        else:
            return None, None

    def decode_fc(self, frame):
        """
        Decodes a flow control (FC) frame

        :param frame: Frame to decode
        :return: Tuple of values flow status (FS), block size (BS) and separation time minimum (STmin) if valid,
                 Tuple of None, None, None otherwise
        """
        if len(frame) >= self.FC_PCI_LENGTH:
            fs = frame[0] & 0xF
            block_size = frame[1]
            st_min = frame[2]
            return fs, block_size, st_min
        else:
            return None, None, None

    def encode_fc(self, flow_status, block_size, st_min):
        """
        Encodes a flow control (FC) message

        :param flow_status: Flow status (FS)
        :param block_size: Block size (BS)
        :param st_min: Separation time minimum (STmin)
        :return: Encoded data for the flow control message
        """
        return [(self.FC_FRAME_ID << 4) | flow_status, block_size, st_min, 0, 0, 0, 0, 0]

    def send_request(self, message):
        """
        Wrapper for sending 'message' as a request

        :param message: The message to send
        :return: None
        """
        frames = self.get_frames_from_message(message)
        self.transmit(frames, self.arb_id_request, self.arb_id_response)

    def send_response(self, message):
        """
        Wrapper for sending 'message' as a response

        :param message: The message to send
        :return: None
        """
        frames = self.get_frames_from_message(message)
        self.transmit(frames, self.arb_id_response, self.arb_id_request)

    def indication(self, wait_window=None):
        """
        Receives an ISO-15765-2 message (one or more frames) and returns its content.

        :param wait_window: Max time (in seconds) to wait before timeout
        :return: A list of received data bytes if successful, None otherwise
        """
        message = []

        if wait_window is None:
            wait_window = self.N_BS_TIMEOUT
        start_time = datetime.datetime.now()
        sn = 0
        message_length = 0

        while True:
            msg = self.bus.recv(self.N_BS_TIMEOUT)
            if msg is not None:
                if msg.arbitration_id == self.arb_id_request:
                    flow_control_arbitration_id = self.arb_id_response
                elif msg.arbitration_id == self.arb_id_response:
                    flow_control_arbitration_id = self.arb_id_request
                else:
                    # Unknown arbitration ID - ignore message
                    continue
                frame = msg.data
                if len(frame) > 0:
                    frame_type = (frame[0] >> 4) & 0xF
                    if frame_type == self.SF_FRAME_ID:
                        # Single frame (SF)
                        dl, message = self.decode_sf(frame)
                        # Trim padding if length exceeds single frame data length (SF_DL)
                        message = message[:dl]
                        break
                    elif frame_type == self.FF_FRAME_ID:
                        # First frame (FF) of a multi-frame message
                        message_length, message = self.decode_ff(frame)
                        fc_frame = self.encode_fc(self.FC_FS_CTS, 0, 0)
                        sn = 0
                        # Respond with flow control (FC) message
                        self.send_message(fc_frame, flow_control_arbitration_id)
                    elif frame_type == self.CF_FRAME_ID:
                        # Consecutive frame (CF)
                        new_sn, data = self.decode_cf(frame)
                        if (sn + 1) % 16 == new_sn:
                            sn = new_sn
                            message += data
                            if len(message) == message_length:
                                break
                            elif len(message) > message_length:
                                # Trim padding if message length exceeds first frame data length (FF_DL)
                                message = message[:message_length]
                                break
                            else:
                                pass
                    else:
                        # Invalid frame type
                        return None
            stop_time = datetime.datetime.now()
            passed_time = stop_time - start_time
            if passed_time.total_seconds() > wait_window:
                # Timeout
                return None
        return list(message)

    def transmit(self, frames, arbitration_id, arbitration_id_flow_control):
        """
        Transmits 'frames' in order on self.bus according to ISO-15765-2

        :param frames: List of frames (which are in turn lists of values) to send
        :param arbitration_id: The arbitration ID used for sending
        :param arbitration_id_flow_control: The arbitration ID used for receiving flow control (FC)
        :return: None
        """
        if len(frames) == 0:
            # No data to send
            return None
        elif len(frames) == 1:
            # Single frame
            self.send_message(frames[0], arbitration_id)
        elif len(frames) > 1:
            # Multiple frames
            frame_index = 0
            # Send first frame (FF)
            self.send_message(frames[frame_index], arbitration_id)
            number_of_frames_left_to_send = len(frames) - 1
            number_of_frames_left_to_send_in_block = 0
            frame_index += 1
            st_min = 0
            while number_of_frames_left_to_send > 0:
                receiver_is_ready = False
                while not receiver_is_ready:
                    # Wait for receiver to send flow control (FC)
                    msg = self.bus.recv(self.N_BS_TIMEOUT)
                    if msg is None:
                        # Quit on timeout
                        return None
                    # Verify that msg uses the expected arbitration ID
                    elif msg.arbitration_id != arbitration_id_flow_control:
                        continue
                    fc_frame = msg.data

                    # Decode Flow Status (FS) from FC message
                    fs, block_size, st_min = self.decode_fc(fc_frame)
                    if fs == self.FC_FS_WAIT:
                        # Flow status (FS) wait (WT)
                        continue
                    elif fs == self.FC_FS_CTS:
                        # Continue to send (CTS)
                        receiver_is_ready = True
                        number_of_frames_left_to_send_in_block = block_size

                        if number_of_frames_left_to_send < number_of_frames_left_to_send_in_block or block_size == 0:
                            number_of_frames_left_to_send_in_block = number_of_frames_left_to_send
                        # If STmin is specified in microseconds (0x80-0xF0) or using reserved ranges (0x80-0xF0 and
                        # 0xFA-0xFF), round up to one millisecond
                        if st_min > 0x7F:
                            st_min = 1
                    else:
                        # Timeout - did not receive a CTS message in time
                        return None
                while number_of_frames_left_to_send_in_block > 0:
                    # Send more frames, until it is time to wait for flow control (FC) again
                    self.send_message(frames[frame_index], arbitration_id)
                    frame_index += 1
                    number_of_frames_left_to_send_in_block -= 1
                    number_of_frames_left_to_send -= 1
                    if number_of_frames_left_to_send_in_block > 0:
                        time.sleep(st_min / 1000)

    def get_frames_from_message(self, message):
        """
        Returns a copy of 'message' split into frames,
        :param message: Message to split
        :return: List of frames
        """
        frame_list = []
        message_length = len(message)
        if message_length > self.MAX_MESSAGE_LENGTH:
            error_msg = "Message too long for ISO-TP. Max allowed length is {0} bytes, received {1} bytes".format(
                self.MAX_MESSAGE_LENGTH, message_length)
            raise ValueError(error_msg)
        if message_length <= self.MAX_SF_LENGTH:
            # Single frame message
            frame = [0] * self.MAX_FRAME_LENGTH
            frame[0] = (self.SF_FRAME_ID << 4) | message_length
            for i in range(0, message_length):
                frame[1 + i] = message[i]
            frame_list.append(frame)
        else:
            # Multiple frame message
            bytes_left_to_copy = message_length
            frame = [0] * self.MAX_FRAME_LENGTH
            # Create first frame (FF)
            frame[0] = (self.FF_FRAME_ID << 4) | (message_length >> 8)
            frame[1] = message_length & 0xFF
            for i in range(0, self.MAX_FF_LENGTH):
                frame[2 + i] = message[i]
            frame_list.append(frame)
            # Create consecutive frames (CF)
            bytes_copied = self.MAX_FF_LENGTH
            bytes_left_to_copy -= bytes_copied
            sn = 0
            while bytes_left_to_copy > 0:
                sn = (sn + 1) % 16
                frame = [0] * self.MAX_FRAME_LENGTH
                frame[0] = (self.CF_FRAME_ID << 4) | sn
                # Fill current consecutive frame
                for i in range(0, self.MAX_CF_LENGTH):
                    if bytes_left_to_copy > 0:
                        frame[1 + i] = message[bytes_copied]
                        bytes_left_to_copy = bytes_left_to_copy - 1
                        bytes_copied = bytes_copied + 1
                frame_list.append(frame)
        return frame_list
