from __future__ import print_function
from lib.can_actions import int_from_str_base
from lib.iso15765_2 import IsoTp
from lib.iso14229_1 import Iso14229_1_nrc
from sys import stdout
import argparse
import time


UDS_SERVICE_NAMES = {
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


REQUEST_DELAY = 0.01
BYTE_MIN = 0x00
BYTE_MAX = 0xFF


def service_discovery(arb_id_request, arb_id_response, request_delay):
    """
    Scans for supported UDS services on the specified arbitration ID.

    :return: list of supported service IDs
    :param arb_id_request: int arbitration ID for requests
    :param arb_id_response: int arbitration ID for responses
    :param request_delay: float delay between each request sent
    """
    found_services = []

    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        # Send requests
        for service_id in range(BYTE_MIN, BYTE_MAX + 1):
            tp.send_request([service_id])
            print("\rProbing service 0x{0:02x} ({0}/{1})".format(service_id, BYTE_MAX), end="")
            stdout.flush()
            time.sleep(request_delay)
        print("\n")
        # Parse responses
        while True:
            msg = tp.bus.recv(0.1)
            if msg is None:
                # No more responses to parse
                break
            service_id = msg.data[2]
            status = msg.data[3]
            if status != Iso14229_1_nrc.SERVICE_NOT_SUPPORTED:
                # Any other response than "service not supported" counts
                found_services.append(service_id)
    return found_services


def service_discovery_wrapper(args):
    """
    Scans for supported UDS services on the specified arbitration ID.

    :return: list of supported service IDs
    :param args: A namespace containing src and dst
    """
    arb_id_request = int_from_str_base(args.src)
    arb_id_response = int_from_str_base(args.dst)
    request_delay = args.delay
    # Probe services
    found_services = service_discovery(arb_id_request, arb_id_response, request_delay)
    # Print results
    for service_id in found_services:
        service_name = UDS_SERVICE_NAMES.get(service_id, "Unknown service")
        print("Supported service 0x{0:02x}: {1}".format(service_id, service_name))


def parse_args(args):
    """
    Parser for diagnostics module arguments.

    :return: Namespace containing action and action-specific arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py uds",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""Universal Diagnostic Services module for CaringCaribou""",
                                     epilog="""Example usage:
  cc.py uds services 0x733 0x633""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for diagnostics service discovery
    parser_info = subparsers.add_parser("services")
    parser_info.add_argument("src", help="arbitration ID to transmit from")
    parser_info.add_argument("dst", help="arbitration ID to listen to")
    parser_info.add_argument("--delay", type=float, default=REQUEST_DELAY, help="delay between each message")
    parser_info.set_defaults(func=service_discovery_wrapper)

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    try:
        args = parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
