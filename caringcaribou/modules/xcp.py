from __future__ import print_function
from caringcaribou.utils.can_actions import CanActions, auto_blacklist
from caringcaribou.utils.common import list_to_hex_str, parse_int_dec_or_hex
from datetime import datetime, timedelta
from sys import stdout
import argparse
import time

# Dictionary of XCP error codes
XCP_ERROR_CODES = {
    0x00: ("ERR_CMD_SYNC", "Command processor synchronisation."),
    0x10: ("ERR_CMD_BUSY", "Command was not executed."),
    0x11: ("ERR_DAQ_ACTIVE", "Command rejected because DAQ is running."),
    0x12: ("ERR_PGM_ACTIVE", "Command rejected because PGM is running."),
    0x20: ("ERR_CMD_UNKNOWN", "Unknown command or not implemented optional command."),
    0x21: ("ERR_CMD_SYNTAX", "Command syntax invalid."),
    0x22: ("ERR_OUT_OF_RANGE", "Command syntax valid but command parameter(s) out of range."),
    0x23: ("ERR_WRITE_PROTECTED", "The memory location is write protected."),
    0x24: ("ERR_ACCESS_DENIED", "The memory location is not accessible."),
    0x25: ("ERR_ACCESS_LOCKED", "Access denied, Seed & Key is required."),
    0x26: ("ERR_PAGE_NOT_VALID", "Selected page not available."),
    0x27: ("ERR_MODE_NOT_VALID", "Selected page mode not available."),
    0x28: ("ERR_SEGMENT_NOT_VALID", "Selected segment not valid."),
    0x29: ("ERR_SEQUENCE", "Sequence error."),
    0x2A: ("ERR_DAQ_CONFIG", "DAQ configuration not valid."),
    0x30: ("ERR_MEMORY_OVERFLOW", "Memory overflow error."),
    0x31: ("ERR_GENERIC", "Generic error."),
    0x32: ("ERR_VERIFY", "The slave internal program verify routine detects an error.")
}

# List of XCP Command codes
XCP_COMMAND_CODES = [
    (0xFF, "CONNECT"),
    (0xFE, "DISCONNECT"),
    (0xFD, "GET_STATUS"),
    (0xFC, "SYNCH"),
    (0xFB, "GET_COMM_MODE_INFO"),
    (0xFA, "GET_ID"),
    (0xF9, "SET_REQUEST"),
    (0xF8, "GET_SEED"),
    (0xF7, "UNLOCK"),
    (0xF6, "SET_MTA"),
    (0xF5, "UPLOAD"),
    (0xF4, "SHORT_UPLOAD"),
    (0xF3, "BUILD_CHECKSUM"),
    (0xF2, "TRANSPORT_LAYER_CMD"),
    (0xF1, "USER_CMD"),
    (0xF0, "DOWNLOAD"),
    (0xEF, "DOWNLOAD_NEXT"),
    (0xEE, "DOWNLOAD_MAX"),
    (0xED, "SHORT_DOWNLOAD"),
    (0xEC, "MODIFY_BITS"),
    (0xEB, "SET_CAL_PAGE"),
    (0xEA, "GET_CAL_PAGE"),
    (0xE9, "GET_PAG_PROCESSOR_INFO"),
    (0xE8, "GET_SEGMENT_INFO"),
    (0xE7, "GET_PAGE_INFO"),
    (0xE6, "SET_SEGMENT_MODE"),
    (0xE5, "GET_SEGMENT_MODE"),
    (0xE4, "COPY_CAL_PAGE"),
    (0xE3, "CLEAR_DAQ_LIST"),
    (0xE2, "SET_DAQ_PTR"),
    (0xE1, "WRITE_DAQ"),
    (0xE0, "SET_DAQ_LIST_MODE"),
    (0xDF, "GET_DAQ_LIST_MODE"),
    (0xDE, "START_STOP_DAQ_LIST"),
    (0xDD, "START_STOP_SYNCH"),
    (0xDC, "GET_DAQ_CLOCK"),
    (0xDB, "READ_DAQ"),
    (0xDA, "GET_DAQ_PROCESSOR_INFO"),
    (0xD9, "GET_DAQ_RESOLUTION_INFO"),
    (0xD8, "GET_DAQ_LIST_INFO"),
    (0xD7, "GET_DAQ_EVENT_INFO"),
    (0xD6, "FREE_DAQ"),
    (0xD5, "ALLOC_DAQ"),
    (0xD4, "ALLOC_ODT"),
    (0xD3, "ALLOC_ODT_ENTRY"),
    (0xD2, "PROGRAM_START"),
    (0xD1, "PROGRAM_CLEAR"),
    (0xD0, "PROGRAM"),
    (0xCF, "PROGRAM_RESET"),
    (0xCE, "GET_PGM_PROCESSOR_INFO"),
    (0xCD, "GET_SECTOR_INFO"),
    (0xCC, "PROGRAM_PREPARE"),
    (0xCB, "PROGRAM_FORMAT"),
    (0xCA, "PROGRAM_NEXT"),
    (0xC9, "PROGRAM_MAX"),
    (0xC8, "PROGRAM_VERIFY")
]


def decode_xcp_error(error_message):
    """
    Decodes an XCP error message and prints a short description.

    :param error_message: The error message
    """
    data = error_message.data
    if not data[0] == 0xfe:
        print("Not a valid error message: {0}".format(error_message))
        return
    error_lookup = XCP_ERROR_CODES.get(data[1], ("UNKNOWN", "Unknown error"))
    print("Received error message:\n{0}".format(error_message))
    print("Error code (0x{0:02x}): {1}\nDescription: {2}".format(data[1], error_lookup[0], error_lookup[1]))


def decode_connect_response(response_message):
    """
    Decodes an XCP connect response and prints the response information.

    :param response_message: The connect response message
    """
    print("> DECODE CONNECT RESPONSE")
    print(response_message)
    data = response_message.data
    if len(data) != 8:
        print("Invalid response length: {0} (expected: 8)".format(len(data)))
        return
    print("-" * 20)
    print("Resource protection status\n")  # Note: sometimes referred to as RESSOURCE (sic) in specification
    resource_bits = ["CAL/PAG", "X (bit 1)", "DAQ", "STIM", "PGM", "X (bit 5)", "X (bit 6)", "X (bit 7)"]
    for i in range(8):
        print("{0:<12}{1}".format(resource_bits[i], bool(data[1] & 2 ** i)))
    print("-" * 20)
    print("COMM_MODE_BASIC\n")
    comm_mode_bits = ["BYTE_ORDER", "ADDRESS_GRANULARITY_0", "ADDRESS_GRANULARITY_1", "X (bit 3)",
                      "X (bit 4)", "X (bit 5)", "SLAVE_BLOCK_MODE", "OPTIONAL"]
    for i in range(8):
        print("{0:<24}{1}".format(comm_mode_bits[i], int(bool(data[2] & 2 ** i))))
    print("\nAddress granularity: {0} byte(s) per address".format(2 ** ((data[2] & 4) * 2 + data[2] & 2)))
    print("-" * 20)
    print("Max CTO message length: {0} bytes".format(data[3]))
    print("Max DTO message length: {0} bytes".format(data[5] * 16 + data[4]))
    print("Protocol layer version: {0}".format(data[6]))
    print("Transport layer version: {0}".format(data[7]))


def decode_get_comm_mode_info_response(response_message):
    """
    Decodes an XCP GET_COMM_MODE_INFO response and prints the response information.

    :param response_message: The response message
    """
    print("> DECODE GET COMM MODE INFO")
    print(response_message)
    data = response_message.data
    print("Reserved: 0x{0:02x}".format(data[1]))
    print("-" * 20)
    print("COMM_MODE_OPTIONAL")
    comm_mode_optional_bits = ["MASTER_BLOCK_MODE", "INTERLEAVED_MODE"] + ["X (bit {0})".format(i) for i in range(2, 8)]
    for i in range(8):
        print("{0:<20}{1}".format(comm_mode_optional_bits[i], bool(data[2] & 2 ** i)))
    print("-" * 20)
    print("Reserved: 0x{0:02x}".format(data[3]))
    print("MAX_BS (master block mode): {0} command packets".format(data[4]))
    print("MIN_ST (minimum separation time): {0} * 100 us".format(data[5]))
    print("QUEUE_SIZE (interleaved mode): {0} command packets".format(data[6]))
    print("XCP Driver version: 0x{0:02x}".format(data[7]))


def decode_get_status_response(response_message):
    print("> DECODE GET STATUS")
    print(response_message)
    data = response_message.data
    print("-" * 20)
    print("CURRENT_SESSION_STATUS")
    current_session_status_bits = ["STORE_CAL_REQ", "X (bit 1)", "STORE_DAQ_REQ", "CLEAR_DAQ_REQ",
                                   "X (bit 4)", "X (bit 5)", "DAQ_RUNNING", "RESUME"]
    for i in range(8):
        print("{0:<16}{1}".format(current_session_status_bits[i], int(bool(data[1] & 2 ** i))))
    print("-" * 20)
    print("RESOURCE PROTECTION STATUS | Seed/key required")
    resource_protection_bits = ["CAL/PAG", "X (bit 1)", "DAQ", "STIM", "PGM", "X (bit 5)", "X (bit 6)", "X (bit 7)"]
    for i in range(8):
        print("{0:<27}| {1}".format(resource_protection_bits[i], bool(data[2] & 2 ** i)))
    print("-" * 20)
    print("Reserved: 0x{0:02x}".format(data[3]))
    print("Session configuration ID: {0}".format(2 ** ((data[5] & 4) * 2 + data[4] & 2)))


def xcp_arbitration_id_discovery(args):
    """Scans for XCP support by brute forcing XCP connect messages against different arbitration IDs."""
    global hit_counter
    min_id = args.min
    max_id = args.max
    blacklist = set(args.blacklist)
    blacklist_duration = args.autoblacklist
    hit_counter = 0

    def is_valid_response(msg):
        """
        Returns a bool indicating whether 'data' is a valid XCP response

        :param data: list of message data bytes
        :return: True if data is a valid XCP response,
                 False otherwise
        """
        data = msg.data
        return (len(data) > 1 and data[0] == 0xff and any(data[1:])) or \
               (len(data) > 0 and data[0] == 0xfe)

    if blacklist_duration > 0:
        # Perform automatic blacklist scanning
        with CanActions(notifier_enabled=False) as blacklist_wrap:
            blacklist |= auto_blacklist(blacklist_wrap.bus, blacklist_duration, is_valid_response, True)

    with CanActions() as can_wrap:
        print("Starting XCP discovery")

        def response_analyser_wrapper(arb_id):
            print("\rSending XCP connect to 0x{0:04x}".format(arb_id), end="")
            stdout.flush()

            def response_analyser(msg):
                global hit_counter
                # Ignore blacklisted arbitration IDs
                if msg.arbitration_id in blacklist:
                    return
                # Handle positive response
                if msg.data[0] == 0xff and any(msg.data[1:]):
                    hit_counter += 1
                    decode_connect_response(msg)
                    print("Found XCP at arb ID 0x{0:04x}, reply at 0x{1:04x}".format(arb_id, msg.arbitration_id))
                    print("#" * 20)
                    print("\n")
                # Handle negative response
                elif msg.data[0] == 0xfe:
                    print("\nFound XCP (with a bad reply) at arbitration ID 0x{0:03x}, reply at 0x{1:04x}".format(
                        arb_id, msg.arbitration_id))
                    decode_xcp_error(msg)

            return response_analyser

        def discovery_end(s):
            print("\r{0}: Found {1} possible matches.".format(s, hit_counter))

        can_wrap.bruteforce_arbitration_id([0xff], response_analyser_wrapper,
                                           min_id=min_id, max_id=max_id, callback_end=discovery_end)


def xcp_command_discovery(args):
    """Attempts to call all XCP commands and lists which ones are supported."""
    global connect_reply, command_reply
    send_arb_id = args.src
    rcv_arb_id = args.dst
    connect_message = [0xff, 0, 0, 0, 0, 0, 0, 0]

    def connect_callback_handler(msg):
        global connect_reply
        if msg.arbitration_id == rcv_arb_id:
            connect_reply = True

    print("XCP command discovery\n")
    print("COMMAND{0}SUPPORTED".format(" " * 17))
    print("-" * 33)
    with CanActions(send_arb_id) as can_wrap:
        # Bruteforce against list of commands (excluding connect)
        for cmd_code, cmd_desc in XCP_COMMAND_CODES[1:]:
            # Connect
            connect_reply = False
            can_wrap.send_single_message_with_callback(connect_message, connect_callback_handler)
            connect_timestamp = datetime.now()
            while not connect_reply and datetime.now() - connect_timestamp < timedelta(seconds=3):
                pass
            if not connect_reply:
                print("ERROR: Connect timeout")
                exit()

            # Build message for current command
            cmd_msg = [cmd_code, 0, 0, 0, 0, 0, 0, 0]

            # Callback handler for current command
            def callback_handler(msg):
                global command_reply
                if msg.arbitration_id == rcv_arb_id:
                    print("{0:<23} {1}".format(cmd_desc, msg.data[0] != 0xfe))
                    command_reply = True

            command_reply = False
            # Send, wait for reply, clear listeners and move on
            can_wrap.send_single_message_with_callback(cmd_msg, callback=callback_handler)
            command_timestamp = datetime.now()
            while not command_reply and datetime.now() - command_timestamp < timedelta(seconds=3):
                pass
            if not command_reply:
                print("ERROR: Command timeout")
                exit()
            can_wrap.clear_listeners()
    print("\nDone!")


def xcp_get_basic_information(args):
    send_arb_id = args.src
    rcv_arb_id = args.dst

    def callback_wrapper(callback):
        """
        Adds handling of uninteresting or error messages to a callback function.

        :param callback: The callback function to run on successful messages
        :return: A callback function with extended message handling
        """

        def c(msg):
            if msg.arbitration_id != rcv_arb_id:
                return
            if msg.data[0] == 0xfe:
                return
            if msg.data[0] == 0xff:
                callback(msg)
            else:
                print("Unexpected reply:\n{0}\n".format(msg))

        return c

    class ProbeMessage:
        """Wrapper class for probe messages"""

        def __init__(self, message_data, callback):
            self.message_data = message_data
            self.callback = callback_wrapper(callback)

        def __str__(self):
            return "[{0}]".format(list_to_hex_str(self.message_data, ", "))

    # Callback handler for GetId messages
    def print_msg_as_text(msg):
        print(list_to_hex_str(msg.data[1:], ""))

    def handle_get_id_reply(msg):
        can_wrap.send_single_message_with_callback([0xf5, msg.data[4]], callback_wrapper(print_msg_as_text))

    # Define probe messages
    probe_msgs = [ProbeMessage([0xff], decode_connect_response),  # Connect
                  ProbeMessage([0xfb], decode_get_comm_mode_info_response),  # GetCommMode
                  ProbeMessage([0xfd], decode_get_status_response),  # GetStatus
                  ProbeMessage([0xfa, 0x00], handle_get_id_reply),  # GetId ASCII text
                  ProbeMessage([0xfa, 0x01], handle_get_id_reply),  # GetId ASAM-MC2 filename w/o path/ext
                  ProbeMessage([0xfa, 0x02], handle_get_id_reply),  # GetId ASAM-MC2 filename with path/ext
                  ProbeMessage([0xfa, 0x03], handle_get_id_reply),  # GetId ASAM-MC2 URL
                  ProbeMessage([0xfa, 0x04], handle_get_id_reply)]  # GetId ASAM-MC2 fileToUpload

    # Initiate probing
    with CanActions(arb_id=send_arb_id) as can_wrap:
        print("Probing for XCP info")
        for probe in probe_msgs:
            print("Sending probe message: {0}".format(probe))
            can_wrap.send_single_message_with_callback(probe.message_data, probe.callback)
            time.sleep(2)
        print("Probing finished")


def xcp_memory_dump(args):
    """
    Performs a memory dump to file or stdout via XCP.

    :param args: A namespace containing src, dst, start, length and f
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst
    start_address = args.start
    length = args.length
    dump_file = args.f
    # TODO Implement support for larger segments against ECUs which support this (e.g. 0xfc for test board)
    max_segment_size = 0x7

    global byte_counter, bytes_left, dump_complete, segment_counter, timeout_start
    # Timeout timer
    dump_complete = False
    # Counters for data length
    byte_counter = 0
    segment_counter = 0

    def handle_upload_reply(msg):
        global byte_counter, bytes_left, dump_complete, timeout_start, segment_counter
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            # Reset timeout timer
            timeout_start = datetime.now()
            # Calculate end index of data to handle
            end_index = min(8, bytes_left + 1)

            if dump_file:
                with open(dump_file, "ab") as outfile:
                    outfile.write(bytearray(msg.data[1:end_index]))
            else:
                print(list_to_hex_str(msg.data[1:end_index], " "))
            # Update counters
            byte_counter += max_segment_size
            bytes_left -= max_segment_size
            if bytes_left < 1:
                if dump_file:
                    print("\rDumping segment {0} ({1} b, 0 b left)".format(segment_counter, length), end="")
                print("Dump complete!")
                dump_complete = True
            elif byte_counter > max_segment_size - 1:
                # Dump another segment
                segment_counter += 1
                if dump_file:
                    # Print progress
                    print("\rDumping segment {0} ({1} b, {2} b left)".format(
                        segment_counter, ((segment_counter + 1) * max_segment_size + byte_counter), bytes_left), end="")
                    stdout.flush()

                byte_counter = 0
                can_wrap.send_single_message_with_callback([0xf5, min(max_segment_size, bytes_left)],
                                                           handle_upload_reply)

    def handle_set_mta_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("Set MTA acked")
            print("Dumping data:")
            # Initiate dumping
            if dump_file:
                print("\rDumping segment 0", end="")
            can_wrap.send_single_message_with_callback([0xf5, min(max_segment_size, bytes_left)], handle_upload_reply)
        else:
            print("Unexpected reply: {0}\n".format(msg))

    def handle_connect_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("Connected: Using", end=" ")
            # Check connect reply to see whether to reverse byte order for MTA
            msb_format = msg.data[2] & 1
            if msb_format:
                print("Motorola format (MSB lower)")
            else:
                print("Intel format (LSB lower)")
                r.reverse()
            can_wrap.send_single_message_with_callback(
                [0xf6, 0x00, 0x00, 0x00, r[0], r[1], r[2], r[3]],
                handle_set_mta_reply)
        else:
            print("Unexpected connect reply: {0}\n".format(msg))

    # Calculate address bytes (4 bytes, least significant first)
    r = []
    n = start_address
    bytes_left = length
    # Calculate start address (r is automatically reversed after connect if needed)
    n &= 0xffffffff
    for i in range(4):
        r.append(n & 0xff)
        n >>= 8
    # Make sure dump_file can be opened if specified (clearing it if it already exists)
    if dump_file:
        try:
            with open(dump_file, "w") as _:
                pass
        except IOError as e:
            print("Error when opening dump file:\n\n{0}".format(e))
            return
    # Initialize
    with CanActions(arb_id=send_arb_id) as can_wrap:
        print("Attempting XCP memory dump")
        # Connect and prepare for dump
        can_wrap.send_single_message_with_callback([0xff, 0, 0, 0, 0, 0, 0, 0], handle_connect_reply)
        # Idle timeout handling
        timeout_start = datetime.now()
        while not dump_complete and datetime.now() - timeout_start < timedelta(seconds=3):
            pass
        if not dump_complete:
            print("\nERROR: Dump ended due to idle timeout")


def parse_args(args):
    """
    Parser for XCP module arguments.

    :return: Namespace containing action and action-specific arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="ccn.py xcp",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""XCP module for CaringCaribouNext""",
                                     epilog="""Example usage:
  ccn.py xcp discovery
  ccn.py xcp discovery -blacklist 0x100 0xabc
  ccn.py xcp discovery -autoblacklist 10
  ccn.py xcp commands 0x3e8 0x3e9
  ccn.py xcp info 1000 1001
  ccn.py xcp dump 0x3e8 0x3e9 0x1fffb000 0x4800 -f bootloader.hex""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for XCP discovery
    parser_disc = subparsers.add_parser("discovery")
    parser_disc.add_argument("-min", type=parse_int_dec_or_hex, default=None)
    parser_disc.add_argument("-max", type=parse_int_dec_or_hex, default=None)
    parser_disc.add_argument("-blacklist", metavar="B", type=parse_int_dec_or_hex, default=[], nargs="+",
                             help="arbitration IDs to ignore")
    parser_disc.add_argument("-autoblacklist", metavar="N", type=float, default=0,
                             help="scan for interfering signals for N seconds and blacklist matching arbitration IDs")
    parser_disc.set_defaults(func=xcp_arbitration_id_discovery)

    # Parser for XCP commands discovery
    parser_comm = subparsers.add_parser("commands")
    parser_comm.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_comm.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_comm.set_defaults(func=xcp_command_discovery)

    # Parser for XCP info
    parser_info = subparsers.add_parser("info")
    parser_info.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_info.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_info.set_defaults(func=xcp_get_basic_information)

    # Parser for XCP data dump
    parser_dump = subparsers.add_parser("dump")
    parser_dump.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_dump.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_dump.add_argument("start", type=parse_int_dec_or_hex, help="start address")
    # TODO: use length OR end address as mutually exclusive group?
    parser_dump.add_argument("length", type=parse_int_dec_or_hex, help="dump length")
    parser_dump.add_argument("-f", "-file", help="output file", default=None)
    parser_dump.set_defaults(func=xcp_memory_dump)

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    """
    Module main wrapper.

    :param arg_list: Module argument list
    """
    try:
        args = parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
