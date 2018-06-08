import can
import datetime
import time


class IsoTp:

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

    def __init__(self, arb_id_request, arb_id_response, bus=None):
        # Setting default bus to None rather than the actual bus prevents a CanError when
        # called with a virtual CAN bus, while the OS is lacking a working CAN interface
        if bus is None:
            self.bus = can.interface.Bus()
        else:
            self.bus = bus
        self.arb_id_request = arb_id_request
        self.arb_id_response = arb_id_response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def send_request(self, data):
        msg = can.Message(arbitration_id=self.arb_id_request, data=data)
        self.bus.send(msg)

    def decode_sf(self, frame):
        if len(frame) >= self.SF_PCI_LENGTH:
            dl = frame[0] & 0xF
            data = frame[1:]
            return dl, data
        else:
            return None, None

    def decode_ff(self, frame):
        if len(frame) >= self.FF_PCI_LENGTH:
            ml = ((frame[0] & 0xF) << 8) | frame[1]
            data = frame[2:]
            return ml, data
        else:
            return None, None

    def decode_cf(self, frame):
        if len(frame) >= self.CF_PCI_LENGTH:
            sn = frame[0] & 0xF
            data = frame[1:]
            return sn, data
        else:
            return None, None

    def decode_fc(self, frame):
        if len(frame) >= self.FC_PCI_LENGTH:
            fs = frame[0] & 0xF
            block_size = frame[1]
            st_min = frame[2]
            return fs, block_size, st_min
        else:
            return None, None, None

    def encode_fc(self, flow_status, block_size, st_min):
        return [(self.FC_FRAME_ID << 4) | flow_status, block_size, st_min, 0, 0, 0, 0, 0]

    def request(self, message):
        frames = self.get_frames_from_message(message)
        self.transmit(frames)

    def indication(self, wait_window):
        message = []

        start_time = datetime.datetime.now()
        sn = 0
        message_length = 0

        while True:

            msg = self.bus.recv(self.N_BS_TIMEOUT)
            if msg is not None and msg.arbitration_id == self.arb_id_response:
                frame = msg.data

                if len(frame) > 0:
                    frame_type = (frame[0] >> 4) & 0xF
                    if frame_type == self.SF_FRAME_ID:
                        dl, message = self.decode_sf(frame)
                        break
                    elif frame_type == self.FF_FRAME_ID:
                        message_length, message = self.decode_ff(frame)
                        fc_frame = self.encode_fc(self.FC_FS_CTS, 0, 0)
                        sn = 0
                        self.send_request(fc_frame)
                    elif frame_type == self.CF_FRAME_ID:
                        new_sn, data = self.decode_cf(frame)
                        if (sn + 1) % 16 == new_sn:
                            sn = new_sn
                            message += data
                            if len(message) == message_length:
                                break
                            elif len(message) > message_length:
                                message = message[:message_length]
                                break
                            else:
                                pass
                    else:
                        return None

            stop_time = datetime.datetime.now()
            passed_time = stop_time - start_time
            if passed_time.total_seconds() > wait_window:
                return None

        return message

    def transmit(self, frames):
        if len(frames) == 1:
            self.send_request(frames[0])

        elif len(frames) > 1:

            frame_index = 0
            self.send_request(frames[frame_index])
            number_of_frames_left_to_send = len(frames) - 1

            num_frames_left_to_send_in_block = 0
            frame_index += 1
            st_min = 0
            while number_of_frames_left_to_send > 0:
                receiver_is_ready = False
                while not receiver_is_ready:

                    msg = self.bus.recv(self.N_BS_TIMEOUT)
                    if msg is None:
                        return None
                    # TODO Keep check?
                    elif msg.arbitration_id == self.arb_id_response:
                        continue
                    fc_frame = msg.data

                    fs, block_size, st_min = self.decode_fc(fc_frame)
                    if fs == self.FC_FS_WAIT:
                        continue
                    elif fs == self.FC_FS_CTS:
                        receiver_is_ready = True
                        num_frames_left_to_send_in_block = block_size

                        if number_of_frames_left_to_send < num_frames_left_to_send_in_block or block_size == 0:
                            num_frames_left_to_send_in_block = number_of_frames_left_to_send

                        # count microseconds as one millisecond
                        if st_min > 0x7F:
                            st_min = 1
                    else:
                        return None

                while num_frames_left_to_send_in_block > 0:
                    self.send_request(frames[frame_index])
                    frame_index += 1
                    num_frames_left_to_send_in_block -= 1
                    number_of_frames_left_to_send -= 1
                    if num_frames_left_to_send_in_block > 0:
                        time.sleep(st_min / 1000)

        else:
            # nothing to send
            pass

    def get_frames_from_message(self, message):

        frame_list = []
        message_length = len(message)

        if message_length <= self.MAX_SF_LENGTH:
            # Create single frame
            frame = [0] * self.MAX_FRAME_LENGTH
            frame[0] = (self.SF_FRAME_ID << 4) | message_length
            for i in range(0, message_length):
                frame[1 + i] = message[i]
            frame_list.append(frame)

        else:
            # Create first frame
            bytes_left_to_copy = message_length
            frame = [0] * self.MAX_FRAME_LENGTH

            # create FF
            frame[0] = (self.FF_FRAME_ID << 4) | (message_length >> 8)
            frame[1] = message_length & 0xFF
            for i in range(0, self.MAX_FF_LENGTH):
                frame[2 + i] = message[i]

            frame_list.append(frame)

            # create CF's
            bytes_copied = self.MAX_FF_LENGTH
            bytes_left_to_copy -= bytes_copied

            sn = 0
            while bytes_left_to_copy > 0:
                sn = (sn + 1) % 16
                frame = [0] * self.MAX_FRAME_LENGTH
                frame[0] = (self.CF_FRAME_ID << 4) | sn

                for i in range(0, self.MAX_CF_LENGTH):
                    if bytes_left_to_copy > 0:
                        frame[1 + i] = message[bytes_copied]
                        bytes_left_to_copy = bytes_left_to_copy - 1
                        bytes_copied = bytes_copied + 1

                frame_list.append(frame)

        return frame_list
