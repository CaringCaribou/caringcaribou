import can
import time


MESSAGE_DELAY = 0.1

ARBITRATION_ID_MIN = 0x0
ARBITRATION_ID_MAX = 0x7FF

BYTE_MIN = 0x0
BYTE_MAX = 0xFF


def pad_data(data):
    return list(data) + [0] * ( 8 - len(data))

def insert_message_length(data):
    """
    Inserts a message length byte before data

    :param data: Message data
    :return:
    """
    if len(data) > 7:
        raise IndexError("send_with_auto_length: data can only contain up to 7 bytes: {0}".format(len(data)))
    full_data = [len(data)] + data
    return full_data


class CanActions():
    def __init__(self, arb_id=None):
        self.bus = can.interface.Bus()
        self.notifier = can.Notifier(self.bus, listeners=[])
        self.arb_id = arb_id
        self.bruteforce_running = False

    def send(self, data):
        if len(data) > 8:
            raise IndexError("Invalid CAN message length: {0}".format(len(data)))
        full_data = pad_data(data)
        msg = can.Message(arbitration_id=self.arb_id,
                          data=full_data, extended_id=False)
        self.bus.send(msg)

    def bruteforce_arbitration_id(self, data, callback, min_id=ARBITRATION_ID_MIN, max_id=ARBITRATION_ID_MAX):
        self.bruteforce_running = True
        for arb_id in range(min_id, max_id+1):
            self.notifier.listeners = [callback(arb_id)]
            msg = can.Message(arbitration_id=arb_id, data=pad_data(data), extended_id=False)
            self.bus.send(msg)
            time.sleep(MESSAGE_DELAY)
            if not self.bruteforce_running:
                break

    def bruteforce_data(self, arbitration_id, data, bruteforce_index, callback, min_value=BYTE_MIN, max_value=BYTE_MAX):
        self.bruteforce_running = True
        for value in range(min_value, max_value+1):
            self.notifier.listeners = [callback(value)]
            data[bruteforce_index] = value
            msg = can.Message(arbitration_id=arbitration_id, data=data, extended_id=False)
            self.bus.send(msg)
            time.sleep(MESSAGE_DELAY)
            if not self.bruteforce_running:
                break

    def send_single_message_with_callback(self, data, callback):
        self.notifier.listeners = [callback]
        self.send(data)

    def bruteforce_stop(self):
        self.bruteforce_running = False