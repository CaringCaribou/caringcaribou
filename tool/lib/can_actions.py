from __future__ import print_function
from sys import stdout, version_info
import can
import time

# Handle large ranges efficiently in both python 2 and 3
if version_info[0] == 2:
    range = xrange


MESSAGE_DELAY = 0.1
DELAY_STEP = 0.02
NOTIFIER_STOP_DURATION = 0.5

ARBITRATION_ID_MIN = 0x0
ARBITRATION_ID_MAX = 0x7FF
ARBITRATION_ID_MAX_EXTENDED = 0x1FFFFFFF

BYTE_MIN = 0x0
BYTE_MAX = 0xFF

# Global CAN interface setting, which can be set through the -i flag to cc.py
# The value None corresponds to the default CAN interface (typically can0)
DEFAULT_INTERFACE = None


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


def str_to_int_list(s):
    """
    Converts a string representing CAN message data into a list of ints.

    E.g. "0102c0ffee" -> [01, 02, 0xc0, 0xff, 0xee]

    :param s: str representing hex data
    :return: list of ints
    :rtype: list
    """
    return [int(s[i * 2:i * 2 + 2], 16) for i in range(len(s) // 2)]


def int_from_byte_list(byte_values, start_index=0, length=None):
    """
    Parses a range of unsigned-up-to-8-bit-ints (bytes) from a list into a single int

    E.g. int_from_byte_list([0x11, 0x22, 0x33, 0x44], 1, 2) = 0x2233 = 8755

    :param byte_values: List of ints
    :param start_index: Index of first byte in 'byte_values' to parse
    :param length: Number of bytes to parse
    :return: int of parsed bytes
    """
    if length is None:
        length = len(byte_values)
    value = 0
    for i in (range(start_index, start_index+length)):
        value = value << 8
        value += byte_values[i]
    return value


def msg_to_candump_format(msg):
    """
    Converts a CAN message to a string on candump format.

    E.g. msg_to_candump_format(can.Message(arbitration_id=0x7ff, data=[

    :param msg: CAN message
    :return: str on candump format
    """
    if msg.is_extended_id:
        output = "({0:.6f}) {1} {2:08X}#{3}"
    else:
        output = "({0:.6f}) {1} {2:03X}#{3}"
    data = "".join(["{0:02X}".format(x) for x in msg.data])
    candump = output.format(msg.timestamp, msg.channel, msg.arbitration_id, data)
    return candump


def insert_message_length(data, pad=False):
    """
    Inserts a message length byte before data

    :param data: Message data
    :param pad: If True, pads returned data to 8 bytes
    :return:
    """
    length = len(data)
    if length > 7:
        raise IndexError("Data can only contain up to 7 bytes: {0}".format(len(data)))
    full_data = [length] + data
    if pad:
        full_data += [0x00] * (7-length)
    return full_data


def auto_blacklist(bus, duration, classifier_function, print_results):
    """Listens for false positives on the CAN bus and generates an arbitration ID blacklist.

    Finds all can.Message <msg> on 'bus' where 'classifier_function(msg)' evaluates to True.
    Terminates after 'duration' seconds and returns a set of all matching arbitration IDs.
    Prints progress, time countdown and list of results if 'print_results' is True.

    :param bus: CAN bus instance
    :param duration: duration in seconds
    :param classifier_function: function which, when called upon a can.Message instance,
                                returns a bool indicating if it should be blacklisted
    :param print_results: whether progress and results should be printed to stdout
    :type bus: can.Bus
    :type duration: float
    :type classifier_function: function
    :type print_results: bool
    :return set of matching arbitration IDs to blacklist
    :rtype set(int)
    """
    if print_results:
        print("Scanning for arbitration IDs to blacklist")
    blacklist = set()
    start_time = time.time()
    end_time = start_time + duration
    while time.time() < end_time:
        if print_results:
            time_left = end_time - time.time()
            num_matches = len(blacklist)
            print("\r{0:> 5.1f} seconds left, {1} found".format(time_left, num_matches), end="")
            stdout.flush()
        # Receive message
        msg = bus.recv(0.1)
        if msg is None:
            continue
        # Classify
        if classifier_function(msg):
            # Add to blacklist
            blacklist.add(msg.arbitration_id)
    if print_results:
        num_matches = len(blacklist)
        print("\r  0.0 seconds left, {0} found".format(num_matches), end="")
        print("\n  Detected IDs: {0}".format(" ".join(sorted(list(map(hex, blacklist))))))
    return blacklist


class CanActions:

    def __init__(self, arb_id=None, notifier_enabled=True):
        """
        CanActions constructor

        :param arb_id: int default arbitration ID for object or None
        :param notifier_enabled: bool indicating whether a notifier for incoming message callbacks should be enabled
        """
        self.bus = can.Bus(DEFAULT_INTERFACE, "socketcan")
        self.arb_id = arb_id
        self.bruteforce_running = False
        self.notifier = None
        if notifier_enabled:
            self.enable_notifier()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.notifier is not None:
            self.disable_notifier()
        self.bus.shutdown()

    def enable_notifier(self):
        self.notifier = can.Notifier(self.bus, listeners=[])

    def disable_notifier(self):
        self.clear_listeners()
        # Prevent threading errors by stopping notifier gracefully
        self.notifier.stop(NOTIFIER_STOP_DURATION)
        self.notifier = None

    def add_listener(self, listener):
        self.notifier.listeners.append(listener)

    def clear_listeners(self):
        self.notifier.listeners = []

    def set_listener(self, listener):
        self.clear_listeners()
        self.add_listener(listener)

    def send(self, data, arb_id=None, is_extended=None, is_error=False, is_remote=False):
        if len(data) > 8:
            raise IndexError("Invalid CAN message length: {0}".format(len(data)))
        # Fallback to default arbitration ID (self.arb_id) if no other ID is specified
        if arb_id is None:
            if self.arb_id is None:
                raise ValueError("Arbitration ID must be set through either 'arb_id' argument or self.arb_id")
            arb_id = self.arb_id
        # Force extended flag if it is unspecified and arbitration ID is larger than the standard format allows
        if is_extended is None:
            is_extended = arb_id > ARBITRATION_ID_MAX
        msg = can.Message(arbitration_id=arb_id,
                          data=data,
                          extended_id=is_extended,
                          is_error_frame=is_error,
                          is_remote_frame=is_remote)
        self.bus.send(msg)

    def bruteforce_arbitration_id(self, data, callback, min_id, max_id,
                                  callback_end=None):
        # Set limits
        if min_id is None:
            min_id = ARBITRATION_ID_MIN
        if max_id is None:
            if min_id <= ARBITRATION_ID_MAX:
                max_id = ARBITRATION_ID_MAX
            else:
                # If min_id is extended, use an extended default max_id as well
                max_id = ARBITRATION_ID_MAX_EXTENDED
        # Sanity checks
        if min_id > max_id:
            if callback_end:
                callback_end("Invalid range: min > max")
            return
        # Start bruteforce
        self.bruteforce_running = True
        for arb_id in range(min_id, max_id + 1):
            self.notifier.listeners = [callback(arb_id)]
            # Use standard addressing (11 bits arbitration ID) instead of extended (29 bits) when possible
            extended = False
            if arb_id > ARBITRATION_ID_MAX:
                extended = True
            msg = can.Message(arbitration_id=arb_id, data=data, extended_id=extended)
            self.bus.send(msg)
            time.sleep(MESSAGE_DELAY)
            # Return if stopped by calling module
            if not self.bruteforce_running:
                self.clear_listeners()
                return
        # Callback if bruteforce finished without being stopped
        if callback_end:
            self.clear_listeners()
            callback_end("Bruteforce of range 0x{0:x}-0x{1:x} completed".format(min_id, max_id))

    def bruteforce_data(self, data, bruteforce_index, callback, min_value=BYTE_MIN, max_value=BYTE_MAX,
                        callback_end=None):
        self.bruteforce_running = True
        for value in range(min_value, max_value + 1):
            self.notifier.listeners = [callback(value)]
            data[bruteforce_index] = value
            self.send(data)
            time.sleep(MESSAGE_DELAY)
            if not self.bruteforce_running:
                self.notifier.listeners = []
                return
        if callback_end:
            self.notifier.listeners = []
            callback_end()

    def bruteforce_data_new(self, data, bruteforce_indices, callback,
                            min_value=BYTE_MIN, max_value=BYTE_MAX,
                            callback_done=None):
        def send(msg_data, idxs):
            self.notifier.listeners = [callback(["{0:02x}".format(msg_data[a]) for a in idxs])]
            self.send(msg_data)
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
        for idx_i in bruteforce_indices:
            data[idx_i] = 0
        bruteforce(0)
        if callback_done:
            callback_done("Scan finished")

    def send_single_message_with_callback(self, data, callback):
        self.set_listener(callback)
        self.send(data)

    def bruteforce_stop(self):
        self.bruteforce_running = False
