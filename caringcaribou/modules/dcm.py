from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import parse_int_dec_or_hex
from sys import stdout
import argparse
import time

DCM_SERVICE_NAMES = {
    0x10: "DIAGNOSTIC_SESSION_CONTROL",
    0x11: "ECU_RESET",
    0x12: "GMLAN_READ_FAILURE_RECORD",
    0x14: "CLEAR_DIAGNOSTIC_INFORMATION",
    0x19: "READ_DTC_INFORMATION",
    0x1A: "GMLAN_READ_DIAGNOSTIC_ID",
    0x20: "RETURN_TO_NORMAL",
    0x22: "READ_DATA_BY_IDENTIFIER",
    0x23: "READ_MEMORY_BY_ADDRESS",
    0x24: "READ_SCALING_DATA_BY_IDENTIFIER",
    0x27: "SECURITY_ACCESS",
    0x28: "COMMUNICATION_CONTROL",
    0x2A: "READ_DATA_BY_PERIODIC_IDENTIFIER",
    0x2C: "DYNAMICALLY_DEFINE_DATA_IDENTIFIER",
    0x2D: "DEFINE_PID_BY_MEMORY_ADDRESS",
    0x2E: "WRITE_DATA_BY_IDENTIFIER",
    0x2F: "INPUT_OUTPUT_CONTROL_BY_IDENTIFIER",
    0x31: "ROUTINE_CONTROL",
    0x34: "REQUEST_DOWNLOAD",
    0x35: "REQUEST_UPLOAD",
    0x36: "TRANSFER_DATA",
    0x37: "REQUEST_TRANSFER_EXIT",
    0x38: "REQUEST_FILE_TRANSFER",
    0x3B: "GMLAN_WRITE_DID",
    0x3D: "WRITE_MEMORY_BY_ADDRESS",
    0x3E: "TESTER_PRESENT",
    0x7F: "NEGATIVE_RESPONSE",
    0x83: "ACCESS_TIMING_PARAMETER",
    0x84: "SECURED_DATA_TRANSMISSION",
    0x85: "CONTROL_DTC_SETTING",
    0x86: "RESPONSE_ON_EVENT",
    0x87: "LINK_CONTROL",
    0xA2: "GMLAN_REPORT_PROGRAMMING_STATE",
    0xA5: "GMLAN_ENTER_PROGRAMMING_MODE",
    0xA9: "GMLAN_CHECK_CODES",
    0xAA: "GMLAN_READ_DPID",
    0xAE: "GMLAN_DEVICE_CONTROL"
}

NRC = {
    0x10: "generalReject",
    0x11: "serviceNotSupported",
    0x12: "sub-functionNotSupported",
    0x13: "incorrectMessageLengthOrInvalidFormat",
    0x14: "responseTooBig",
    0x21: "busyRepeatRequest",
    0x22: "conditionsNotCorrect",
    0x24: "requestSequenceError",
    0x25: "noResponseFromSub-netComponent",
    0x26: "failurePreventsExecutionOfRequestedAction",
    0x31: "requestOutOfRange",
    0x33: "securityAccessDenied",
    0x35: "invalidKey",
    0x36: "exceededNumberOfAttempts",
    0x37: "requiredTimeDelayNotExpired",
    0x70: "uploadDownloadNotAccepted",
    0x71: "transferDataSuspended",
    0x72: "generalProgrammingFailure",
    0x73: "wrongBlockSequenceCounter",
    0x78: "requestCorrectlyReceivedResponsePending",
    0x7E: "sub-FunctionNotSupportedInActiveSession",
    0x7F: "serviceNotSupportedInActiveSession"
}


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


def dcm_dtc(args):
    """
    Fetches and prints the Diagnostic Trouble Codes from a supported service (Mode $03)

    :param args: A namespace containing src, dst and clear
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst
    clear = args.clear
    big_data = []
    big_data_size = 0

    def dtc_type(x):
        return {
            0: "P",
            1: "C",
            2: "B",
            3: "U",
        }.get(x, "?")

    def decode_dtc(data):  # Expects 2 bytes
        if len(data) != 2:
            return
        return dtc_type((data[0] & 0xC0) >> 6) + format((data[0] & 0x30) >> 4) + format(data[0] & 0x0F, "01x") + format(
            data[1], "02x")

    def decode_dtc_pkt(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        return_packet = False
        # TODO: Are we sure that data byte 0 is 0x10, or should the check be against data[0] & 0x10 instead?
        if msg.data[0] == 0x10 and (msg.data[2] == 0x43 or msg.data[2] == 0x47):
            return_packet = True
        if (msg.data[0] & 0xF0) == 0x20:  # We should probably set a state for this
            return_packet = True
        if msg.data[1] == 0x43:
            return_packet = True
        if msg.data[2] == 0x47:
            return_packet = True
        if not return_packet:
            return

        global big_data
        global big_data_size

        if big_data_size == 0 and (msg.data[1] == 0x43 or msg.data[1] == 0x47):  # Single frame
            print("There are {0} DTCs".format(msg.data[2]))
            if msg.data[2] == 0:
                return
            if msg.data[0] > 2:
                print("DTC: {0}".format(decode_dtc(msg.data[3:5])))
            if msg.data[0] > 4:
                print("DTC: {0}".format(decode_dtc(msg.data[5:6])))
            if msg.data[0] > 6:
                print("DTC: {0}".format(decode_dtc(msg.data[7:9])))
        if msg.data[0] == 0x10:  # Multi Frame (First Frame)
            full_dlc = (msg.data[0] & 0x0F) + msg.data[1]
            print("There are {0} DTCs".format(msg.data[3]))
            print("DTC: {0}".format(decode_dtc(msg.data[4:6])))
            print("DTC: {0}".format(decode_dtc(msg.data[6:8])))
            can_wrap.send([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            big_data_size = full_dlc - 6
        if (msg.data[0] & 0xF0) == 0x20:  # Consecutive
            if big_data_size > 8:
                big_data.extend(msg.data[1:])
                big_data_size -= 7
            else:
                big_data.extend(msg.data[1:big_data_size + 1])
                big_data_size = 0
            if big_data_size == 0:
                for i in range(0, len(big_data), 2):
                    print("DTC: {0}".format(decode_dtc(big_data[i:i + 2])))

    with CanActions(arb_id=send_arb_id) as can_wrap:
        if clear:
            msg = insert_message_length([0x04], pad=True)
            can_wrap.send(msg)
            print("Cleared DTCs and reset MIL")
        else:
            print("Fetching Diagnostic Trouble Codes")
            msg = insert_message_length([0x03], pad=True)
            can_wrap.send_single_message_with_callback(msg, decode_dtc_pkt)
            time.sleep(0.5)
            print("Fetching Pending Diagnostic Trouble Codes")
            msg = insert_message_length([0x07], pad=True)
            can_wrap.send_single_message_with_callback(msg, decode_dtc_pkt)
            time.sleep(1)


def dcm_discovery(args):
    """
    Scans for diagnostics support by sending session control against different arbitration IDs.

    :param: args: A namespace containing min and max
    """
    min_id = args.min
    max_id = args.max
    no_stop = args.nostop
    blacklist = args.blacklist

    valid_responses = [0x50, 0x7F]

    def scan_arbitration_ids_to_blacklist(scan_duration):
        print("Scanning for arbitration IDs to blacklist (-autoblacklist)")
        ids_to_blacklist = set()

        def response_handler(msg):
            """
            Blacklists the arbitration ID of a message if it could be misinterpreted as valid diagnostic response

            :param msg: can.Message instance to check
            """
            if len(msg.data) > 1 and msg.data[1] in valid_responses:
                ids_to_blacklist.add(msg.arbitration_id)

        with CanActions() as can_actions:
            # Listen for matches
            can_actions.add_listener(response_handler)
            for i in range(scan_duration, 0, -1):
                print("\r{0:> 3} seconds left, {1} found".format(i-1, len(ids_to_blacklist)), end="")
                stdout.flush()
                time.sleep(1)
            print("")
            can_actions.clear_listeners()
        # Add found matches to blacklist
        for arb_id in ids_to_blacklist:
            blacklist.append(arb_id)

    # Perform automatic blacklist scanning
    if args.autoblacklist > 0:
        scan_arbitration_ids_to_blacklist(args.autoblacklist)

    class Diagnostics:
        found = False

    with CanActions() as can_wrap:
        print("Starting diagnostics service discovery")

        def response_analyser_wrapper(arb_id):
            print("\rSending Diagnostic Session Control to 0x{0:04x}".format(arb_id), end="")
            stdout.flush()

            def response_analyser(msg):
                # Ignore blacklisted arbitration IDs
                if msg.arbitration_id in blacklist:
                    return
                # Catch both ok and negative response
                if len(msg.data) >= 2 and msg.data[1] in valid_responses:
                    Diagnostics.found = True
                    print("\nFound diagnostics at arbitration ID 0x{0:04x}, "
                          "reply at 0x{1:04x}".format(arb_id, msg.arbitration_id))
                    if not no_stop:
                        can_wrap.bruteforce_stop()

            return response_analyser

        def discovery_finished(s):
            if Diagnostics.found:
                print("\n{0}".format(s))
            else:
                print("\nDiagnostics service could not be found: {0}".format(s))

        # Message to bruteforce - [length, session control, default session]
        message = insert_message_length([0x10, 0x01], pad=True)
        can_wrap.bruteforce_arbitration_id(message, response_analyser_wrapper,
                                           min_id=min_id, max_id=max_id, callback_end=discovery_finished)


def service_discovery(args):
    """
    Scans for supported DCM services. Prints a list of all supported services afterward.

    :param args: A namespace containing src and dst
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst

    with CanActions(arb_id=send_arb_id) as can_wrap:
        print("Starting DCM service discovery")
        supported_services = []

        def response_analyser_wrapper(service_id):
            print("\rProbing service 0x{0:02x} ({1} found)".format(service_id, len(supported_services)), end="")
            stdout.flush()

            def response_analyser(m):
                # Skip incoming messages with wrong arbitration ID
                if m.arbitration_id != rcv_arb_id:
                    return
                # Skip replies where service is not supported
                if m.data[3] == 0x11:
                    return
                # Service supported - add to list
                supported_services.append(m.data[2])

            return response_analyser

        def done():
            print("\nDone!")

        # Message to bruteforce - [length, service id]
        msg = insert_message_length([0x00], pad=True)
        # Index of service id byte in message
        service_index = 1
        try:
            # Initiate bruteforce
            can_wrap.bruteforce_data(msg, service_index, response_analyser_wrapper, callback_end=done)
        finally:
            # Clear listeners
            can_wrap.notifier.listeners = []
            print("")
            # Print id and name of all found services
            for service in supported_services:
                service_name = DCM_SERVICE_NAMES.get(service, "Unknown service")
                print("Supported service 0x{0:02x}: {1}".format(service, service_name))


def subfunc_discovery(args):
    """
    Scans for subfunctions of a given service.

    :param args: A namespace containing src, dst, service, show and i
    """
    send_arb_id = args.src
    rcv_arb_id = args.dst
    service_id = args.service
    show_data = args.show
    bruteforce_indices = args.i

    # Sanity checks
    all_valid = True
    for i in bruteforce_indices:
        if not 2 <= i <= 7:
            print("Invalid bruteforce index '{0}' - must be in range 2-7".format(i))
            all_valid = False
    if not all_valid:
        return

    with CanActions(arb_id=send_arb_id) as can_wrap:
        found_sub_functions = []
        print("Starting DCM sub-function discovery")

        def response_analyser_wrapper(data):
            print("\rProbing sub-function 0x{0:02x} data {1} (found: {2})".format(
                service_id, data, len(found_sub_functions)), end="")
            stdout.flush()

            def response_analyser(msg):
                if msg.arbitration_id != rcv_arb_id:
                    return
                # Response queued - do not handle
                if msg.data[:4] == [0x03, 0x7f, service_id, 0x78]:
                    can_wrap.current_delay = 1.0
                    return
                # Catch ok status
                elif msg.data[1] - 0x40 == service_id or \
                        (msg.data[1] == 0x7F and msg.data[3] not in [0x11, 0x12, 0x31, 0x78]):
                    found_sub_functions.append((data, [msg]))
                elif msg.data[0] == 0x10:
                    # If response takes up multiple frames
                    can_wrap.current_delay = 1.0
                    found_sub_functions.append((data, [msg]))
                    if show_data:
                        # Cool, give me the rest
                        can_wrap.send([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                    else:
                        # Fine, but I don't want the remaining data
                        can_wrap.send([0x32, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                elif show_data and msg.data[0] & 0xF0 == 0x20:
                    # Parts following a 0x30 in multiple frame response (keep waiting)
                    can_wrap.current_delay = 1.0
                    found_sub_functions[-1][1].append(msg)
                else:
                    # We got an answer - no reason to keep waiting
                    can_wrap.current_delay = 0.0

            return response_analyser

        def finished(s):
            print("\nDone: {0}".format(s))

        try:
            # Message to bruteforce - [length, session control, default session]
            payload = [service_id]
            for ind in range(max(bruteforce_indices) - 1):
                payload.append(0x00)
            message = insert_message_length(payload, pad=True)
            can_wrap.bruteforce_data_new(message, bruteforce_indices=bruteforce_indices,
                                         callback=response_analyser_wrapper,
                                         callback_done=finished)
            can_wrap.notifier.listeners = []
        finally:
            # Print found functions
            if len(found_sub_functions) > 0:
                print("\n\nFound sub-functions for service 0x{0:02x} ({1}):\n".format(
                    service_id, DCM_SERVICE_NAMES.get(service_id, "Unknown service")))
                for (sub_function, msgs) in found_sub_functions:
                    print("Sub-function {0}".format(" ".join(sub_function)))
                    if show_data:
                        for message in msgs:
                            print("  {0}".format(message))
            else:
                print("\n\nNo sub-functions were found")


def tester_present(args):
    send_arb_id = args.src
    delay = args.delay
    suppress_positive_response = args.spr

    testerpresent_service_id = 0x3E

    if suppress_positive_response:
        sub_function = 0x80
    else:
        sub_function = 0x00

    message_data = [0x02, testerpresent_service_id, sub_function, 0x00, 0x00, 0x00, 0x00, 0x00]
    print("Sending TesterPresent to arbitration ID {0} (0x{0:02x})".format(send_arb_id))
    print("\nPress Ctrl+C to stop\n")
    with CanActions(arb_id=send_arb_id) as can_wrap:
        counter = 1
        while True:
            can_wrap.send(data=message_data)
            print("\rCounter:", counter, end="")
            stdout.flush()
            time.sleep(delay)
            counter += 1


def parse_args(args):
    """
    Parser for diagnostics module arguments.

    :return: Namespace containing action and action-specific arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="caringcaribou dcm",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""Diagnostics module for CaringCaribou
DeprecationWarning: The DCM module has been replaced by the UDS module""",
                                     epilog="""Example usage:
  caringcaribou dcm discovery
  caringcaribou dcm discovery -blacklist 0x123 0x456
  caringcaribou dcm discovery -autoblacklist 10
  caringcaribou dcm services 0x733 0x633
  caringcaribou dcm subfunc 0x733 0x633 0x22 2 3
  caringcaribou dcm dtc 0x7df 0x7e8
  caringcaribou dcm testerpresent 0x733""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for diagnostics discovery
    parser_disc = subparsers.add_parser("discovery")
    parser_disc.add_argument("-min", type=parse_int_dec_or_hex, default=None)
    parser_disc.add_argument("-max", type=parse_int_dec_or_hex, default=None)
    parser_disc.add_argument("-nostop", default=False, action="store_true",
                             help="scan until end of range")
    parser_disc.add_argument("-blacklist", metavar="B", type=parse_int_dec_or_hex, default=[], nargs="+",
                             help="arbitration IDs to ignore")
    parser_disc.add_argument("-autoblacklist", metavar="N", type=int, default=0,
                             help="scan for interfering signals for N seconds and blacklist matching arbitration IDs")
    parser_disc.set_defaults(func=dcm_discovery)

    # Parser for diagnostics service discovery
    parser_info = subparsers.add_parser("services")
    parser_info.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_info.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_info.set_defaults(func=service_discovery)

    # Parser for diagnostics sub-function discovery
    parser_dump = subparsers.add_parser("subfunc")
    parser_dump.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_dump.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_dump.add_argument("service", type=parse_int_dec_or_hex, help="service ID (e.g. 0x22 for Read DID)")
    parser_dump.add_argument("-show", action="store_true", help="show data in terminal")
    parser_dump.add_argument("i", type=int, nargs="+", help="sub-function indices")
    parser_dump.set_defaults(func=subfunc_discovery)

    # Parser for DTC
    parser_dtc = subparsers.add_parser("dtc")
    parser_dtc.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_dtc.add_argument("dst", type=parse_int_dec_or_hex, help="arbitration ID to listen to")
    parser_dtc.add_argument("-clear", action="store_true", help="Clear DTC / MIL")
    parser_dtc.set_defaults(func=dcm_dtc)

    # Parser for TesterPresent
    parser_tp = subparsers.add_parser("testerpresent")
    parser_tp.add_argument("src", type=parse_int_dec_or_hex, help="arbitration ID to transmit from")
    parser_tp.add_argument("-delay", type=float, default=0.5, help="delay between each TesterPresent message")
    parser_tp.add_argument("-spr", action="store_true", help="suppress positive response")
    parser_tp.set_defaults(func=tester_present)

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    try:
        args = parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
