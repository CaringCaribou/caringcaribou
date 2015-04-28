import can
import time


MESSAGE_DELAY = 0.1
DELAY_STEP = 0.02

ARBITRATION_ID_MIN = 0x0
ARBITRATION_ID_MAX = 0x7FF

BYTE_MIN = 0x0
BYTE_MAX = 0xFF


def pad_data(data):
    return list(data) + [0] * ( 8 - len(data))


def int_from_str_base(s):
    """
    Converts a str to an int, supporting both base 10 and base 16 literals.

    :param s: str representing an int in base 10 or 16
    :return: int version of s on success, None otherwise
    :rtype: int
    """
    try:
        if s.startswith("0x"):
            return int(s, base=16)
        else:
            return int(s)
    except (AttributeError, ValueError):
        return None


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

    def __enter__(self):
        return self  # FIXME correct?

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear_listeners()
        time.sleep(0.5)

    def add_listener(self, listener):
        self.notifier.listeners.append(listener)

    def clear_listeners(self):
        self.notifier.listeners = []

    def set_listener(self, listener):
        self.clear_listeners()
        self.add_listener(listener)

    def send(self, data):
        if len(data) > 8:
            raise IndexError("Invalid CAN message length: {0}".format(len(data)))
        full_data = pad_data(data)
        msg = can.Message(arbitration_id=self.arb_id,
                          data=full_data, extended_id=False)
        self.bus.send(msg)

    def bruteforce_arbitration_id(self, data, callback, min_id, max_id,
                                  callback_not_found=None):
        # Sanity checks
        if min_id is None:
            min_id = ARBITRATION_ID_MIN
        if max_id is None:
            max_id = ARBITRATION_ID_MAX
        if min_id > max_id:
            if callback_not_found:
                callback_not_found("Invalid range: min > max")
            return
        # Start bruteforce
        self.bruteforce_running = True
        for arb_id in range(min_id, max_id+1):
            self.notifier.listeners = [callback(arb_id)]
            msg = can.Message(arbitration_id=arb_id, data=pad_data(data), extended_id=False)
            self.bus.send(msg)
            time.sleep(MESSAGE_DELAY)
            # Return if stopped by calling module
            if not self.bruteforce_running:
                self.notifier.listeners = []
                return
        # Callback if bruteforce finished without being stopped
        if callback_not_found:
            self.notifier.listeners = []
            callback_not_found("Finished without reply")

    def bruteforce_data(self, data, bruteforce_index, callback, min_value=BYTE_MIN, max_value=BYTE_MAX,
                        callback_not_found=None):
        # TODO: Add reason to callback_not_found?
        self.bruteforce_running = True
        for value in range(min_value, max_value+1):
            self.notifier.listeners = [callback(value)]
            data[bruteforce_index] = value
            self.send(data)
            time.sleep(MESSAGE_DELAY)
            if not self.bruteforce_running:
                self.notifier.listeners = []
                return
        if callback_not_found:
            self.notifier.listeners = []
            callback_not_found()

    def bruteforce_data_new(self, data, bruteforce_indices, callback,
                            min_value=BYTE_MIN, max_value=BYTE_MAX,
                            callback_done=None):
        def send(data, idxs):
            #global current_delay
            self.notifier.listeners = [callback(["{0:02x}".format(data[a]) for a in idxs])]
            self.send(data)
            self.current_delay = 0.2
            while self.current_delay > 0.0:
                time.sleep(DELAY_STEP)
                self.current_delay -= DELAY_STEP
            if not self.bruteforce_running:
                self.notifier.listeners = []
                return

        def bruteforce(idx):
            if idx >= len(bruteforce_indices):
                send(data, bruteforce_indices)
                return
            for i in range(min_value, max_value + 1):
                data[bruteforce_indices[idx]] = i
                bruteforce(idx + 1)
        # Make sure that the data array is correctly initialized for the bruteforce
        for idx in bruteforce_indices:
            data[idx] = 0
        bruteforce(0)
        if callback_done:
            callback_done("Scan finished")



    def send_single_message_with_callback(self, data, callback):
        self.notifier.listeners = [callback]
        self.send(data)


    def bruteforce_stop(self):
        self.bruteforce_running = False
