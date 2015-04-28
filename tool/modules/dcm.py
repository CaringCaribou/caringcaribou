from can_actions import CanActions, insert_message_length
from sys import stdout
import argparse


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

DCM_SERVICE_NAMES = {
    0x10: 'DIAGNOSTIC_SESSION_CONTROL',
    0x11: 'ECU_RESET',
    0x14: 'CLEAR_DIAGNOSTIC_INFORMATION',
    0x19: 'READ_DTC_INFORMATION',
    0x22: 'READ_DATA_BY_IDENTIFIER',
    0x23: 'READ_MEMORY_BY_ADDRESS',
    0x24: 'READ_SCALING_DATA_BY_IDENTIFIER',
    0x27: 'SECURITY_ACCESS',
    0x28: 'COMMUNICATION_CONTROL',
    0x2A: 'READ_DATA_BY_PERIODIC_IDENTIFIER',
    0x2C: 'DYNAMICALLY_DEFINE_DATA_IDENTIFIER',
    0x2E: 'WRITE_DATA_BY_IDENTIFIER',
    0x2F: 'INPUT_OUTPUT_CONTROL_BY_IDENTIFIER',
    0x31: 'ROUTINE_CONTROL',
    0x34: 'REQUEST_DOWNLOAD',
    0x35: 'REQUEST_UPLOAD',
    0x36: 'TRANSFER_DATA',
    0x37: 'REQUEST_TRANSFER_EXIT',
    0x38: 'REQUEST_FILE_TRANSFER',
    0x3D: 'WRITE_MEMORY_BY_ADDRESS',
    0x3E: 'TESTER_PRESENT',
    0x7F: 'NEGATIVE_RESPONSE',
    0x83: 'ACCESS_TIMING_PARAMETER',
    0x84: 'SECURED_DATA_TRANSMISSION',
    0x85: 'CONTROL_DTC_SETTING',
    0x86: 'RESPONSE_ON_EVENT',
    0x87: 'LINK_CONTROL'
}

NRC = {
    0x10: 'generalReject',
    0x11: 'serviceNotSupported',
    0x12: 'sub-functionNotSupported',
    0x13: 'incorrectMessageLengthOrInvalidFormat',
    0x21: 'busyRepeatRequest',
    0x22: 'conditionsNotCorrect',
    0x31: 'requestOutOfRange',
    0x33: 'securityAccessDenied',
    0x72: 'generalProgrammingFailure',
    0x78: 'requestCorrectlyReceivedResponsePending',
    0x7F: 'serviceNotSupportedInActiveSession'
}


def dcm_discovery(args):
    """Scans for diagnostics support by sending session control against different arbitration IDs."""
    # TODO docstring args
    min_id = int_from_str_base(args.min)
    max_id = int_from_str_base(args.max)
    can_wrap = CanActions()
    print("Starting diagnostics service discovery")

    def response_analyser_wrapper(arb_id):
        print "\rSending diagnostics Tester Present to 0x{0:04x}".format(arb_id),
        stdout.flush()

        def response_analyser(msg):
            # Catch both ok and negative response
            if msg.data[1] in [0x50, 0x7F]:
                print("\nFound diagnostics at arbitration ID 0x{0:04x}, reply at 0x{1:04x}".format(arb_id, msg.arbitration_id))
                can_wrap.bruteforce_stop()
        return response_analyser

    def none_found(s):
        print("\nDiagnostics service could not be found: {0}".format(s))

    # Message to bruteforce - [length, session control, default session]
    message = insert_message_length([0x10, 0x01])
    can_wrap.bruteforce_arbitration_id(message, response_analyser_wrapper,
                                       min_id=min_id, max_id=max_id, callback_not_found=none_found)  # FIXME values


def service_discovery(args):
    """
    Scans for supported DCM services. Prints a list of all supported services afterwards.

    :param send_arb_id: Arbitration ID used for outgoing messages
    :param rcv_arb_id: Arbitration ID expected for incoming messages
    :return:
    """
    # TODO docstring args
    send_arb_id = int_from_str_base(args.src)
    rcv_arb_id = int_from_str_base(args.dst)

    can_wrap = CanActions(arb_id=send_arb_id)
    print("Starting DCM service discovery")
    supported_services = []

    def response_analyser_wrapper(service_id):
        print "\rProbing service 0x{0:02x} ({1} found)".format(service_id, len(supported_services)),
        stdout.flush()

        def response_analyser(msg):
            # Skip incoming messages with wrong arbitration ID
            if msg.arbitration_id != rcv_arb_id:
                return
            # Skip replies where service is not supported
            if msg.data[3] == 0x11:
                return
            # Service supported - add to list
            supported_services.append(msg.data[2])  # TODO: Does this really work for functions with length>1?
        return response_analyser

    def done():
        print("\nDone!")

    # Message to bruteforce - [length, service id]
    msg = [0x01, 0x00]
    # Index of service id byte in message
    service_index = 1
    try:
        # Initiate bruteforce
        can_wrap.bruteforce_data(msg, service_index, response_analyser_wrapper, callback_not_found=done)
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
    send_arb_id = int_from_str_base(args.src)
    rcv_arb_id = int_from_str_base(args.dst)
    service_id = int_from_str_base(args.service)
    show_data = args.show
    bruteforce_indices = args.i

    can_wrap = CanActions(arb_id=send_arb_id)
    found_sub_functions = []
    print("Starting DCM sub-function discovery")

    def response_analyser_wrapper(data):
        print "\rProbing sub-function 0x{0:02x} data {1} (found: {2})".format(
            service_id, data, len(found_sub_functions)),
        stdout.flush()


        def response_analyser(msg):
            if msg.arbitration_id != rcv_arb_id:
                return
            # Response queued - do not handle
            if msg.data[:4] == [0x03, 0x7f, service_id, 0x78]:
                can_wrap.current_delay = 1.0
                return
            # Catch ok status
            elif msg.data[1]-0x40 == service_id or (msg.data[1] == 0x7F and msg.data[3] not in [0x11, 0x12, 0x31, 0x78]): # TODO - more?
                found_sub_functions.append((data, [msg]))
            elif msg.data[0] == 0x10:
                # If response takes up multiple frames
                can_wrap.current_delay = 1.0
                found_sub_functions.append((data, [msg]))
                if show_data:
                    # Cool, give me the rest
                    can_wrap.send([0x30])
                else:
                    # Fine, but I don't want the remaining data
                    can_wrap.send([0x32])
            elif show_data and msg.data[0] & 0xF0 == 0x20:
                # Parts following a 0x30 in multiple frame response (keep waiting)
                can_wrap.current_delay = 1.0
                found_sub_functions[-1][1].append(msg)
            else:
                # We've got an answer - no reason to keep waiting
                can_wrap.current_delay = 0.0
        return response_analyser

    def finished():
        print("\nDone")

    try:
        # Message to bruteforce - [length, session control, default session]
        message = insert_message_length([service_id, 0x00, 0x00])
        can_wrap.bruteforce_data_new(message, bruteforce_indices=bruteforce_indices, callback=response_analyser_wrapper,
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
                    for msg in msgs:
                        print("  {0}".format(msg))
        else:
            print("\n\nNo sub-functions were found")


def parse_args(args):
    """
    Parser for diagnostics module arguments.

    :return: Namespace containing action and action-specific arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py dcm",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""Diagnostics module for CaringCaribou""",
                                     epilog="""Example usage:
  TODO""")  # FIXME
    subparsers = parser.add_subparsers()

    # Parser for diagnostics discovery
    parser_disc = subparsers.add_parser("discovery")
    parser_disc.add_argument("-min", type=str, default=None)
    parser_disc.add_argument("-max", type=str, default=None)
    parser_disc.set_defaults(func=dcm_discovery)

    # Parser for diagnostics service discovery
    parser_info = subparsers.add_parser("services")
    parser_info.add_argument("src", type=str, help="arbitration ID to transmit from")
    parser_info.add_argument("dst", type=str, help="arbitration ID to listen to")
    parser_info.set_defaults(func=service_discovery)

    # Parser for diagnostics sub-function discovery
    parser_dump = subparsers.add_parser("subfunc")  # TODO Args
    parser_dump.add_argument("src", type=str, help="arbitration ID to transmit from")
    parser_dump.add_argument("dst", type=str, help="arbitration ID to listen to")
    parser_dump.add_argument("service", type=str, help="service ID (e.g. 0x22 for Read DID)")
    parser_dump.add_argument("-show", action="store_true", help="show data in terminal")
    parser_dump.add_argument("i", type=int, nargs="+", help="sub-function indices")
    parser_dump.set_defaults(func=subfunc_discovery)

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    try:
        args = parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
