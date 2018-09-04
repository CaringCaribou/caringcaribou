from lib.can_actions import CanActions, int_from_str_base, str_to_int_list
from time import sleep
from sys import exit
import argparse
import re


class CanMessage:
    """
    Message wrapper class used by file parsers.
    """

    def __init__(self, arb_id, data, delay, is_extended=False, is_error=False, is_remote=False):
        """
        :param arb_id: int - arbitration ID
        :param data: list of ints - data bytes
        :param delay: float - delay in seconds
        """
        self.arb_id = arb_id
        self.data = data
        self.delay = delay
        self.is_extended = is_extended
        self.is_error = is_error
        self.is_remote = is_remote


def parse_messages(msgs, delay):
    """
    Parses a list of message strings.

    :param delay: Delay between each message
    :param msgs: list of message strings
    :return: list of CanMessage instances
    """
    message_list = []
    msg = None
    try:
        for msg in msgs:
            msg_parts = msg.split("#", 1)
            arb_id = int_from_str_base(msg_parts[0])
            if arb_id is None:
                raise ValueError("Invalid arbitration ID: '{0}'".format(msg_parts[0]))
            msg_data = []
            # Check data length
            byte_list = msg_parts[1].split(".")
            if not 0 < len(byte_list) <= 8:
                raise ValueError("Invalid data length: {0}".format(len(byte_list)))
            # Validate data bytes
            for byte in byte_list:
                byte_int = int(byte, 16)
                if not 0x00 <= byte_int <= 0xff:
                    raise ValueError("Invalid byte value: '{0}'".format(byte))
                msg_data.append(byte_int)
            fixed_msg = CanMessage(arb_id, msg_data, delay)
            message_list.append(fixed_msg)
        # No delay before sending first message
        return message_list
    except ValueError as e:
        print("Invalid message at position {0}: '{1}'\nFailure reason: {2}".format(len(message_list), msg, e))
        exit()


def parse_file(filename, force_delay):
    """
    Parses a file containing CAN traffic logs.

    :param filename: Path to file
    :param force_delay: Delay value between each message (if omitted, the delays specified by log file are used)
    :return: list of CanMessage instances
    """

    def parse_candump_line(curr_line, prev_timestamp=None):
        """
        Parses a line on candump log format, e.g.
        (1499197954.029156) can0 123#c0ffee

        :param curr_line: str to parse
        :param prev_timestamp: datetime object containing timestamp of previous message (to calculate delay)
        :return: CanMessage representing 'curr_line', datetime.datetime timestamp of 'curr_line'
        """
        segments = curr_line.strip().split(" ")
        time_stamp = float(segments[0][1:-1])
        msg_segs = segments[2].split("#")
        arb_id = int(msg_segs[0], 16)
        data = str_to_int_list(msg_segs[1])
        if prev_timestamp is None:
            delay = 0
        elif force_delay is not None:
            delay = force_delay
        else:
            delay = time_stamp - prev_timestamp
        message = CanMessage(arb_id, data, delay)
        return message, time_stamp

    def parse_pythoncan_line(curr_line, prev_timestamp=None):
        """
        Parses a line on python-can log format.

        Example on format used by older python-can versions:
        Timestamp:        0.000000        ID: 017a    000    DLC: 3    c0 ff ee
        Examples on format used by python-can 2.1.0+:
        Timestamp:        0.000000        ID: 0000    S          DLC: 3    c0 ff ee
        Timestamp:        0.000000    ID: 00000000    X E R      DLC: 4    de ad ca fe

        :param curr_line: str to parse
        :param prev_timestamp: datetime object containing timestamp of previous message (to calculate delay)
        :return: CanMessage representing 'curr_line', datetime.datetime timestamp of 'curr_line'
        """
        line_regex = re.compile(r"Timestamp: (?P<timestamp>\d+\.\d+) +ID: (?P<arb_id>[0-9a-fA-F]+) +"
                                r"((\d+)|(?P<is_extended>[SX]) (?P<is_error>[E ]) (?P<is_remote>[R ])) +"
                                r"DLC: [0-8] +(?P<data>(?:[0-9a-fA-F]{2} ?){0,8})")
        parsed_msg = line_regex.match(curr_line)
        arb_id = int(parsed_msg.group("arb_id"), 16)
        time_stamp = float(parsed_msg.group("timestamp"))
        data = list(int(a, 16) for a in parsed_msg.group("data").split(" "))
        if prev_timestamp is None:
            delay = 0
        elif force_delay is not None:
            delay = force_delay
        else:
            delay = time_stamp - prev_timestamp
        # TODO Parse flags for old format as well
        is_extended = parsed_msg.group("is_extended") == "X"
        is_error = parsed_msg.group("is_error") == "E"
        is_remote = parsed_msg.group("is_remote") == "R"
        message = CanMessage(arb_id, data, delay, is_extended, is_error, is_remote)
        return message, time_stamp

    try:
        messages = []
        with open(filename, "r") as f:
            first_line = f.readline()
            # Simple pattern matching to identify log format
            if first_line.startswith("("):
                line_parser = parse_candump_line
            elif first_line.startswith("Timestamp:"):
                line_parser = parse_pythoncan_line
            else:
                raise IOError("Unrecognized file type - could not parse file")

            msg, timestamp = line_parser(first_line)
            messages.append(msg)
            for line in f.readlines():
                msg, timestamp = line_parser(line, timestamp)
                messages.append(msg)
            return messages
    except IOError as e:
        print("IOError: {0}".format(e))
        return None


def send_messages(messages, loop):
    """
    Sends a list of messages separated by a given delay.

    :param loop: bool indicating whether the message sequence should be looped (re-sent over and over)
    :param messages: List of messages, where a message has the format (arb_id, [data_byte])
    """
    with CanActions() as can_wrap:
        loop_counter = 0
        while True:
            for i in range(len(messages)):
                msg = messages[i]
                if i != 0 or loop_counter != 0:
                    sleep(msg.delay)
                print("  Arb_id: 0x{0:03x}, data: {1}".format(msg.arb_id, ["{0:02x}".format(a) for a in msg.data]))
                can_wrap.send(msg.data, msg.arb_id, msg.is_extended, msg.is_error, msg.is_remote)
            if not loop:
                break
            loop_counter += 1


def parse_args(args):
    """
    Argument parser for the send module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py send",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Raw message transmission module for CaringCaribou.\n"
                                                 "Messages can be passed as command line arguments or through a file.",
                                     epilog="""Example usage:
  cc.py send message 0x7a0#c0.ff.ee.00.11.22.33.44
  cc.py send message -d 0.5 123#de.ad.be.ef 124#01.23.45
  cc.py send file can_dump.txt
  cc.py send file -d 0.2 can_dump.txt""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True
    
    # Parser for sending messages from command line
    cmd_msgs = subparsers.add_parser("message")
    cmd_msgs.add_argument("data", metavar="msg", nargs="+",
                          help="message on format ARB_ID#DATA where ARB_ID is interpreted "
                               "as hex if it starts with 0x and decimal otherwise. DATA "
                               "consists of 1-8 bytes written in hex and separated by dots.")
    cmd_msgs.add_argument("--delay", "-d", metavar="D", type=float, default=0,
                          help="delay between messages in seconds")
    cmd_msgs.add_argument("--loop", "-l", action="store_true", help="loop message sequence (re-send over and over)")
    cmd_msgs.set_defaults(func=parse_messages)

    # Parser for sending messages from file
    file_msg = subparsers.add_parser("file")
    file_msg.add_argument("data", metavar="filename", type=str, help="path to file")
    file_msg.add_argument("--delay", "-d", metavar="D", type=float, default=None,
                          help="delay between messages in seconds (overrides timestamps in file)")
    file_msg.add_argument("--loop", "-l", action="store_true", help="loop message sequence (re-send over and over)")
    file_msg.set_defaults(func=parse_file)

    args = parser.parse_args(args)
    return args


def module_main(args):
    """
    Send module main wrapper.

    :param args: List of module arguments
    """
    args = parse_args(args)
    print("Parsing messages")
    messages = args.func(args.data, args.delay)
    if not messages:
        print("No messages parsed")
    else:
        print("Sending messages")
        send_messages(messages, args.loop)
