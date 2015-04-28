from can_actions import CanActions, int_from_str_base
from sys import stdout
import argparse
import time


# Dictionary of XCP error codes, mapping (code -> (error, description))
XCP_ERROR_CODES = dict([
    (0x00, ("ERR_CMD_SYNC", "Command processor synchronisation.")),
    (0x10, ("ERR_CMD_BUSY", "Command was not executed.")),
    (0x11, ("ERR_DAQ_ACTIVE", "Command rejected because DAQ is running.")),
    (0x12, ("ERR_PGM_ACTIVE", "Command rejected because PGM is running.")),
    (0x20, ("ERR_CMD_UNKNOWN", "Unknown command or not implemented optional command.")),
    (0x21, ("ERR_CMD_SYNTAX", "Command syntax invalid.")),
    (0x22, ("ERR_OUT_OF_RANGE", "Command syntax valid but command parameter(s) out of range.")),
    (0x23, ("ERR_WRITE_PROTECTED", "The memory location is write protected.")),
    (0x24, ("ERR_ACCESS_DENIED", "The memory location is not accessible.")),
    (0x25, ("ERR_ACCESS_LOCKED", "Access denied, Seed & Key is required.")),
    (0x26, ("ERR_PAGE_NOT_VALID", "Selected page not available.")),
    (0x27, ("ERR_MODE_NOT_VALID", "Selected page mode not available.")),
    (0x28, ("ERR_SEGMENT_NOT_VALID", "Selected segment not valid.")),
    (0x29, ("ERR_SEQUENCE", "Sequence error.")),
    (0x2A, ("ERR_DAQ_CONFIG", "DAQ configuration not valid.")),
    (0x30, ("ERR_MEMORY_OVERFLOW", "Memory overflow error.")),
    (0x31, ("ERR_GENERIC", "Generic error.")),
    (0x32, ("ERR_VERIFY", "The slave internal program verify routine detects an error."))
    ])


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

    :param data: The response message
    """
    print("> DECODE CONNECT RESPONSE")
    print(response_message)
    data = response_message.data
    print("-" * 20)
    print("Resource protection status\n")  # Note: sometimes referred to as RESSOURCE (sic) in specification
    resource_bits = ["CAL/PAG", "X (bit 1)", "DAQ", "STIM", "PGM", "X (bit 5)", "X (bit 6)", "X (bit 7)"]
    for i in range(8):
        print("{0:<12}{1}".format(resource_bits[i], bool(data[1] & 2**i)))
    print("-" * 20)
    print("COMM_MODE_BASIC\n")
    comm_mode_bits = ["BYTE_ORDER", "ADDRESS_GRANULARITY_0", "ADDRESS_GRANULARITY_1", "X (bit 3)",
                       "X (bit 4)", "X (bit 5)", "SLAVE_BLOCK_MODE", "OPTIONAL"]
    for i in range(8):
        print("{0:<24}{1}".format(comm_mode_bits[i], int(bool(data[2] & 2**i))))
    print("\nAddress granularity: {0} byte(s) per address".format(2 ** ((data[2] & 4) * 2 + data[2] & 2)))
    print("-" * 20)
    print("Max CTO message length: {0} bytes".format(data[3]))
    print("Max DTO message length: {0} bytes".format(data[5] * 16 + data[4]))
    print("Protocol layer version: {0}".format(data[6]))
    print("Transport layer version: {0}".format(data[7]))


def decode_get_comm_mode_info_response(response_message):
    """
    Decodes an XCP GET_COMM_MODE_INFO response and prints the response information.

    :param data: The response message
    """
    print("> DECODE GET COMM MODE INFO")
    print(response_message)
    data = response_message.data
    print("Reserved: 0x{0:02x}".format(data[1]))
    print("-" * 20)
    print("COMM_MODE_OPTIONAL")
    comm_mode_optional_bits = ["MASTER_BLOCK_MODE", "INTERLEAVED_MODE"] + ["X (bit {0})".format(i) for i in range(2,8)]
    for i in range(8):
        print("{0:<20}{1}".format(comm_mode_optional_bits[i], bool(data[2] & 2**i)))
    print("-" * 20)
    print("Reserved: 0x{0:02x}".format(data[3]))
    print("MAX_BS (master block mode): {0} command packets".format(data[4]))
    print("MIN_ST (minimum separation time): {0} * 100 us".format(data[5]))
    print("QUEUE_SIZE (interleaved mode): {0} command packets".format(data[6]))
    print("XCP Driver version: 0x{0:02x}\n".format(data[7]))


def decode_get_status_response(response_message):
    print("> DECODE GET STATUS")
    print(response_message)
    data = response_message.data
    print("-" * 20)
    print("CURRENT_SESSION_STATUS")
    current_session_status_bits = ["STORE_CAL_REQ", "X (bit 1)", "STORE_DAQ_REQ", "CLEAR_DAQ_REQ",
                                   "X (bit 4)", "X (bit 5)", "DAQ_RUNNING", "RESUME"]
    for i in range(8):
        print("{0:<16}{1}".format(current_session_status_bits[i], int(bool(data[1] & 2**i))))
    print("-" * 20)
    print("RESOURCE PROTECTION STATUS | Seed/key required")
    resource_protection_bits = ["CAL/PAG", "X (bit 1)", "DAQ", "STIM", "PGM", "X (bit 5)", "X (bit 6)", "X (bit 7)"]
    for i in range(8):
        print("{0:<27}| {1}".format(resource_protection_bits[i], bool(data[2] & 2**i)))
    print("-" * 20)
    print("Reserved: 0x{0:02x}".format(data[3]))
    print("Session configuration ID: {0}\n".format(2 ** ((data[5] & 4) * 2 + data[4] & 2)))



def xcp_arbitration_id_discovery(args):
    """Scans for XCP support by brute forcing XCP connect messages against different arbitration IDs."""
    min_id = int_from_str_base(args.min)
    max_id = int_from_str_base(args.max)

    with CanActions() as can_wrap:
        print("Starting XCP discovery")

        def response_analyser_wrapper(arb_id):
            print "\rSending XCP connect to 0x{0:04x}".format(arb_id),
            stdout.flush()

            def response_analyser(msg):
                # Handle positive response
                if msg.data[0] == 0xff:
                    can_wrap.bruteforce_stop()
                    decode_connect_response(msg)
                    print("Found XCP at arbitration ID 0x{0:04x}, reply at 0x{1:04x}".format(arb_id, msg.arbitration_id))
                # Handle negative response
                elif msg.data[0] == 0xfe:
                    print("\nFound XCP (with a bad reply) at arbitration ID {0:03x}, reply at {1:04x}".format(
                        arb_id, msg.arbitration_id))
                    can_wrap.bruteforce_stop()
                    decode_xcp_error(msg)
            return response_analyser

        def none_found(s):
            print("\nXCP could not be found: {0}".format(s))

        can_wrap.bruteforce_arbitration_id([0xff], response_analyser_wrapper,
                                           min_id=min_id, max_id=max_id, callback_not_found=none_found)


def xcp_get_basic_information(args):

    send_arb_id = int_from_str_base(args.src)
    rcv_arb_id = int_from_str_base(args.dst)

    def handle_description_file(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("Desc file response:\n{0}".format(msg))
            print("".join([chr(x) for x in msg.data[1:]]))
        else:
            print("Weird get status reply: {0}\n".format(msg))

    def handle_get_id_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("GET ID response:\n{0}".format(msg))
            can_wrap.send_single_message_with_callback([0xf5, msg.data[4]], handle_description_file)
        else:
            print("Weird get status reply: {0}\n".format(msg))

    def handle_get_status_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            decode_get_status_response(msg)
            # TODO: Different values possible (1=ASAM-MC2 filename etc)
            can_wrap.send_single_message_with_callback([0xfa, 0x01], handle_get_id_reply)
        else:
            print("Weird get status reply: {0}\n".format(msg))

    def handle_get_comm_mode_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            decode_get_comm_mode_info_response(msg)
            can_wrap.send_single_message_with_callback([0xfd], handle_get_status_reply)
        else:
            print("Weird comm mode reply: {0}\n".format(msg))

    def handle_connect(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            can_wrap.send_single_message_with_callback([0xfb], handle_get_comm_mode_reply)
        else:
            print("Weird connect reply: {0}\n".format(msg))

    print("Probing for XCP info")
    with CanActions(arb_id=send_arb_id) as can_wrap:
        can_wrap.send_single_message_with_callback([0xff], handle_connect)
        time.sleep(2)
        print("End of sequence")


def xcp_memory_dump(args):
    """
    Performs a memory dump to file or stdout via XCP.

    :param args: A namespace containing src, dst, start, length and f
    """
    send_arb_id = int_from_str_base(args.src)
    rcv_arb_id = int_from_str_base(args.dst)
    start_address = int_from_str_base(args.start)
    length = int_from_str_base(args.length)
    dump_file = args.f

    global byte_counter, bytes_left, dump_complete, segment_counter, idle_timeout
    # Timeout timer
    idle_timeout = 3.0
    dump_complete = False
    # Counters for data length
    byte_counter = 0
    segment_counter = 0

    def handle_upload_reply(msg):
        global byte_counter, bytes_left, dump_complete, idle_timeout, segment_counter
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            # Reset timeout timer
            idle_timeout = 3.0
            # Calculate end index of data to handle
            end_index = min(8, bytes_left + 1)

            if dump_file:
                with open(dump_file, "ab") as outfile:
                    outfile.write(bytearray(msg.data[1:end_index]))
            else:
                print(" ".join(["{0:02x}".format(i) for i in msg.data[1:end_index]]))
            # Update counters
            byte_counter += 7
            bytes_left -= 7
            if bytes_left < 1:
                if dump_file:
                    print "\rDumping segment {0} ({1} b, 0 b left)".format(segment_counter, length)
                print("Dump complete!")
                dump_complete = True
            elif byte_counter > 251:
                # Dump another segment
                segment_counter += 1
                if dump_file:
                    # Print progress
                    print "\rDumping segment {0} ({1} b, {2} b left)".format(
                        segment_counter, ((segment_counter+1)*0xf5 + byte_counter), bytes_left),
                    stdout.flush()

                byte_counter = 0
                can_wrap.send_single_message_with_callback([0xf5, min(0xfc, bytes_left)], handle_upload_reply)

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
            print "\rDumping segment 0",
            can_wrap.send_single_message_with_callback([0xf5, min(0xfc, bytes_left)], handle_upload_reply)
        else:
            print("Unexpected reply: {0}\n".format(msg))

    def handle_connect_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("Connected")
            can_wrap.send_single_message_with_callback(
                [0xf6, 0x00, 0x00, 0x00, r[0], r[1], r[2], r[3]],
                handle_set_mta_reply)
        else:
            print("Weird connect reply: {0}\n".format(msg))

    # Calculate address bytes (4 bytes, least significant first)
    r = []
    n = start_address
    bytes_left = length
    n &= 0xFFFFFFFF
    for i in range(4):
        r.append(n & 0xFF)
        n >>= 8
    # Make sure dump_file can be opened if specified (clearing it if it already exists)
    if dump_file:
        with open(dump_file, "w") as tmp:
            pass
    # Initialize
    with CanActions(arb_id=send_arb_id) as can_wrap:
        print("Attempting XCP memory dump")
        # Connect and prepare for dump
        can_wrap.send_single_message_with_callback([0xff], handle_connect_reply)
        # Idle timeout handling
        while idle_timeout > 0.0 and not dump_complete:
            time.sleep(0.5)
            idle_timeout -= 0.5
        if not dump_complete:
            print("\nERROR: Dump ended due to idle timeout")


def parse_args(args):
    """
    Parser for XCP module arguments.

    :return: Namespace containing action and action-specific arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py xcp",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""XCP module for CaringCaribou""",
                                     epilog="""Example usage:
  cc.py xcp discovery
  cc.py xcp info 1000 1001
  cc.py xcp dump 0x3e8 0x3e9 0x1fffb000 0x4800 -f bootloader.hex""")
    subparsers = parser.add_subparsers()

    # Parser for XCP discovery
    parser_disc = subparsers.add_parser("discovery")
    parser_disc.add_argument("-min", type=str, default=None)
    parser_disc.add_argument("-max", type=str, default=None)
    parser_disc.set_defaults(func=xcp_arbitration_id_discovery)

    # Parser for XCP info
    parser_info = subparsers.add_parser("info")
    parser_info.add_argument("src", type=str, help="arbitration ID to transmit from")
    parser_info.add_argument("dst", type=str, help="arbitration ID to listen to")
    parser_info.set_defaults(func=xcp_get_basic_information)

    # Parser for XCP data dump
    parser_dump = subparsers.add_parser("dump")
    parser_dump.add_argument("src", type=str, help="arbitration ID to transmit from")
    parser_dump.add_argument("dst", type=str, help="arbitration ID to listen to")
    parser_dump.add_argument("start", type=str, help="start address")
    # TODO: use length OR end address as mutually exclusive group?
    parser_dump.add_argument("length", type=str, help="dump length")
    parser_dump.add_argument("-f", "-file", type=str, help="output file", default=None)
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
