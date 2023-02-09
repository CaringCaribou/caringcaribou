from __future__ import print_function
from ..utils.common import list_to_hex_str, parse_int_dec_or_hex
from ..utils.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MAX_EXTENDED
from ..utils.constants import ARBITRATION_ID_MIN
from ..utils.iso14229_1 import Constants, NegativeResponseCodes
from doipclient import DoIPClient
from doipclient.connectors import DoIPClientUDSConnector
from udsoncan.client import Client
from udsoncan.services import *
from sys import stdout, version_info
import argparse
import datetime
import time
import sys
import struct

# Handle large ranges efficiently in both python 2 and 3
if version_info[0] == 2:
    range = xrange

UDS_SERVICE_NAMES = {
    0x10: "DIAGNOSTIC_SESSION_CONTROL",
    0x11: "ECU_RESET",
    0x14: "CLEAR_DIAGNOSTIC_INFORMATION",
    0x19: "READ_DTC_INFORMATION",
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
    0x3D: "WRITE_MEMORY_BY_ADDRESS",
    0x3E: "TESTER_PRESENT",
    0x7F: "NEGATIVE_RESPONSE",
    0x83: "ACCESS_TIMING_PARAMETER",
    0x84: "SECURED_DATA_TRANSMISSION",
    0x85: "CONTROL_DTC_SETTING",
    0x86: "RESPONSE_ON_EVENT",
    0x87: "LINK_CONTROL"
}

DELAY_DISCOVERY = 0.2
DELAY_TESTER_PRESENT = 0.5
DELAY_SECSEED_RESET = 0.01
DELAY_FUZZ_RESET = 3.901
TIMEOUT_SERVICES = 0.2

# Max number of arbitration IDs to backtrack during verification
VERIFICATION_BACKTRACK = 5
# Extra time in seconds to wait for responses during verification
VERIFICATION_EXTRA_DELAY = 0.5

BYTE_MIN = 0x00
BYTE_MAX = 0xFF

DUMP_DID_MIN = 0x0000
DUMP_DID_MAX = 0xFFFF
DUMP_DID_TIMEOUT = 0.2

# Diagnostic Message payload type - see Table 21 "Payload type diagnostic message structure"
# https://python-doipclient.readthedocs.io/en/latest/messages.html
PAYLOAD_TYPE = 0x8001


class DevNull:
    # Supress errors solution: 
    # https://stackoverflow.com/questions/5925918/python-suppressing-errors-from-going-to-commandline
    def write(self, msg):
        pass


# Duplicate testing from https://www.iditect.com/guide/python/python_howto_find_the_duplicates_in_a_list.html
def find_duplicates(sequence):
    first_seen = set()
    first_seen_add = first_seen.add
    duplicates = set(i for i in sequence if i in first_seen or first_seen_add(i))
    return duplicates


def ecu_reset(client, reset_type):
    if reset_type == 1:
        client.ecu_reset(ECUReset.ResetType.hardReset)
    elif reset_type == 2:
        client.ecu_reset(ECUReset.ResetType.keyOffOnReset)
    elif reset_type == 3:
        client.ecu_reset(ECUReset.ResetType.softReset)
    elif reset_type == 4:
        client.ecu_reset(ECUReset.ResetType.enableRapidPowerShutDown)
    elif reset_type == 5:
        client.ecu_reset(ECUReset.ResetType.disableRapidPowerShutDown)


def extended_session(client, session_type):
    if session_type == 1:
        client.change_session(DiagnosticSessionControl.Session.defaultSession)
    elif session_type == 2:
        client.change_session(DiagnosticSessionControl.Session.programmingSession)
    elif session_type == 3:
        client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)
    elif session_type == 4:
        client.change_session(DiagnosticSessionControl.Session.safetySystemDiagnosticSession)


def uds_discovery(min_id, max_id, blacklist_args, auto_blacklist_duration,
                  delay, print_results=True):
    """Scans for diagnostics support by brute forcing session control
        messages to different arbitration IDs.

    Returns a list of all (client_arb_id, server_arb_id) pairs found.

    :param min_id: start arbitration ID value
    :param max_id: end arbitration ID value
    :param blacklist_args: blacklist for arbitration ID values
    :param auto_blacklist_duration: seconds to scan for interfering
      arbitration IDs to blacklist automatically
    :param delay: delay between each message
    :param print_results: whether results should be printed to stdout
    :type min_id: int
    :type max_id: int
    :type blacklist_args: [int]
    :type auto_blacklist_duration: float
    :type delay: float
    :type print_results: bool
    :return: list of (client_arbitration_id, server_arbitration_id) pairs
    :rtype [(int, int)]
    """

    # Set defaults
    if min_id is None:
        min_id = ARBITRATION_ID_MIN
    if max_id is None:
        if min_id <= ARBITRATION_ID_MAX:
            max_id = ARBITRATION_ID_MAX
        else:
            # If min_id is extended, use an extended default max_id as well
            max_id = ARBITRATION_ID_MAX_EXTENDED
    if auto_blacklist_duration is None:
        auto_blacklist_duration = 0
    if blacklist_args is None:
        blacklist_args = []

    # Sanity checks
    if max_id < min_id:
        raise ValueError("max_id must not be smaller than min_id - got min:0x{0:x}, max:0x{1:x}".format(min_id, max_id))
    if auto_blacklist_duration < 0:
        raise ValueError("auto_blacklist_duration must not be smaller than 0, got {0}'".format(auto_blacklist_duration))
    elif auto_blacklist_duration > 0:
        timeout = auto_blacklist_duration
    else:
        timeout = 2

    blacklist = set(blacklist_args)

    found_arbitration_ids = []

    send_arb_id = min_id - 1

    print("Waiting for Vehicle Identification Announcement\n")
    print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
    address, announcement = DoIPClient.await_vehicle_announcement()
    logical_address = announcement.logical_address
    ip, port = address
    print("ECU IP and port found: ", ip, ",", port, "\nECU Logical Address Found: ", hex(logical_address), "\n")

    print("Searching for Client Node ID\n")

    client_id_status = 0
    while send_arb_id < max_id:

        send_arb_id += 1
        if print_results:
            print("\rSending Diagnostic Session Control to 0x{0:04x}"
                  .format(send_arb_id), end="")

        try:
            if send_arb_id in blacklist:
                # Ignore blacklisted arbitration IDs
                continue

            if client_id_status == 0:
                doip_client = DoIPClient(ip, logical_address, client_logical_address=send_arb_id)
            else:
                doip_client = DoIPClient(ip, send_arb_id, client_logical_address=client_logical_address)

            conn = DoIPClientUDSConnector(doip_client)
            with Client(conn, request_timeout=timeout) as client:
                response = client.change_session(DiagnosticSessionControl.Session.defaultSession)
            if response.positive:
                print("\n\nFound diagnostics server "
                      "listening at 0x{0:04x}, "
                      "response at 0x{1:04x}"
                      .format(logical_address, send_arb_id))
                found_arb_id_pair = (logical_address, send_arb_id)
                found_arbitration_ids.append(found_arb_id_pair)

                if client_id_status == 0:
                    client_id_status = 1
                    client_logical_address = send_arb_id
                    send_arb_id = min_id - 1
                    print("\nSearching for Server Node ID\n")
                else:
                    continue
            else:
                blacklist.add(send_arb_id)

        except KeyboardInterrupt:
            return found_arbitration_ids
        except ConnectionRefusedError:
            time.sleep(delay)

        except ConnectionResetError:
            time.sleep(delay)
            continue

        except TimeoutError:
            sys.stderr = DevNull()
            continue

        except OSError:
            print("Please check the connection and try again.\n")

    return found_arbitration_ids


def __uds_discovery_wrapper(args):
    """Wrapper used to initiate a UDS discovery scan"""
    min_id = args.min
    max_id = args.max
    blacklist = args.blacklist
    auto_blacklist_duration = args.autoblacklist
    delay = args.delay
    print_results = True

    try:
        arb_id_pairs = uds_discovery(min_id, max_id, blacklist,
                                     auto_blacklist_duration,
                                     delay, print_results)
        if len(arb_id_pairs) == 0:
            # No UDS discovered
            print("\nDiagnostics service could not be found.")
        else:
            # Print result table
            print("\nIdentified diagnostics:\n")
            table_line = "+------------+------------+"
            print(table_line)
            print("| CLIENT ID  | SERVER ID  |")
            print(table_line)
            for (client_id, server_id) in arb_id_pairs:
                print("| 0x{0:08x} | 0x{1:08x} |"
                      .format(client_id, server_id))
            print(table_line)
    except ValueError as e:
        print("Discovery failed: {0}".format(e))


def service_discovery(arb_id_request, arb_id_response, timeout,
                      min_id=BYTE_MIN, max_id=BYTE_MAX, print_results=True):
    """Scans for supported UDS services on the specified arbitration ID.
       Returns a list of found service IDs.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param timeout: delay between each request sent
    :param min_id: first service ID to scan
    :param max_id: last service ID to scan
    :param print_results: whether progress should be printed to stdout
    :type arb_id_request: int
    :type arb_id_response: int
    :type timeout: float
    :type min_id: int
    :type max_id: int
    :type print_results: bool
    :return: list of supported service IDs
    :rtype [int]
    """
    found_services = []

    print("Waiting for Vehicle Identification Announcement\n")
    print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
    address, announcement = DoIPClient.await_vehicle_announcement()
    logical_address = arb_id_request
    ip, port = address

    print("Discovering Services\n")

    try:

        for service_id in range(min_id, max_id + 1):

            if print_results:
                print("\rProbing service 0x{0:02x} ({0}/{1}): found {2}"
                      .format(service_id, max_id, len(found_services)),
                      end="")
            stdout.flush()

            doip_client = DoIPClient(ip, logical_address, client_logical_address=arb_id_response)

            conn = DoIPClientUDSConnector(doip_client)

            s = struct.pack("<h", service_id)

            doip_message = struct.pack("!HH", arb_id_response, arb_id_request) + s[:1] + b"\x00"

            try:
                with Client(conn, request_timeout=timeout) as client:
                    extended_session(client, session_type=3)

                    doip_client.send_doip(PAYLOAD_TYPE, doip_message)
                    response = doip_client.receive_diagnostic(timeout)

                    doip_client.close()

                    if response is None or response[2] == NegativeResponseCodes.SERVICE_NOT_SUPPORTED:
                        continue

                    if response[2] == NegativeResponseCodes.SUB_FUNCTION_NOT_SUPPORTED or \
                            response[2] == NegativeResponseCodes.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT:
                        response_id = service_id
                        response_service_id = response[2]
                        status = response[2]
                        if response_id != Constants.NR_SI:
                            request_id = service_id
                            found_services.append(request_id)
                        elif status != NegativeResponseCodes.SERVICE_NOT_SUPPORTED:
                            # Any other response than "service not supported" counts
                            found_services.append(response_service_id)

            except ConfigError:
                sys.stderr = DevNull()
                time.sleep(3)
                continue
            except OSError:
                sys.stderr = DevNull()
                time.sleep(3)
                continue
            except IndexError:
                sys.stderr = DevNull()
                continue

        if print_results:
            print("\nDone!")

    except KeyboardInterrupt:
        if print_results:
            print("\nInterrupted by user!\n")
        return found_services

    except (ConnectionRefusedError, ConnectionResetError, TimeoutError, OSError):
        print("Please check the connection and try again.\n")

    return found_services


def __service_discovery_wrapper(args):
    """Wrapper used to initiate a service discovery scan"""
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    # Probe services
    found_services = service_discovery(arb_id_request,
                                       arb_id_response, timeout)
    # Print results
    for service_id in found_services:
        service_id_name = UDS_SERVICE_NAMES.get(service_id, "Unknown service")
        print("Supported service 0x{0:02x}: {1}".format(service_id, service_id_name))


def tester_present(arb_id_request, arb_id_response, delay, duration):
    """Sends TesterPresent messages to 'arb_id_request'. Stops automatically
    after 'duration' seconds or runs forever if this is None.

    :param arb_id_request: arbitration ID for requests
    :param delay: seconds between each request
    :param duration: seconds before automatically stopping, or None to
                     continue forever
    
    :type arb_id_request: int
    :type delay: float
    :type duration: float or None
    """

    # Calculate end timestamp if the TesterPresent should automatically
    # stop after a given duration
    auto_stop = duration is not None
    end_time = None
    if auto_stop:
        end_time = (datetime.datetime.now()
                    + datetime.timedelta(seconds=duration))

    print("\nWaiting for Vehicle Identification Announcement\n")
    print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
    address, announcement = DoIPClient.await_vehicle_announcement()
    logical_address = arb_id_request
    ip, port = address

    doip_client = DoIPClient(ip, logical_address, client_logical_address=arb_id_response)
    conn = DoIPClientUDSConnector(doip_client)
    with Client(conn, request_timeout=5) as client:
        counter = 1
        print("Sending TesterPresent to arbitration ID {0} (0x{0:02x})"
              .format(arb_id_request))
        print("\nPress Ctrl+C to stop\n")
        while True:
            client.tester_present()
            print("\rCounter:", counter, end="")
            stdout.flush()
            time.sleep(delay)
            counter += 1
            if auto_stop and datetime.datetime.now() >= end_time:
                break


def __tester_present_wrapper(args):
    """Wrapper used to initiate a TesterPresent session"""
    arb_id_request = args.src
    arb_id_response = args.dst
    delay = args.delay
    duration = args.duration

    tester_present(arb_id_request, arb_id_response, delay, duration)


def __ecu_reset_wrapper(args):
    """Wrapper used to initiate ECU Reset"""
    logical_address = args.src
    reset_type = args.reset_type

    if not 1 <= reset_type <= 5:
        raise ValueError("reset type must be within interval 0x01-0x05")

    print("Sending ECU reset, type 0x{0:02x} to arbitration ID 0x{1:02x}".format(reset_type, logical_address))
    try:
        print("\nWaiting for Vehicle Identification Announcement\n")
        print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
        address, announcement = DoIPClient.await_vehicle_announcement()
        ip, port = address

        doip_client = DoIPClient(ip, logical_address, client_logical_address=args.dst)
        conn = DoIPClientUDSConnector(doip_client)
        with Client(conn, request_timeout=5) as client:
            ecu_reset(client, reset_type)

        print(doip_client.request_entity_status())

    except ConnectionRefusedError:
        print("Connection Refused: Please check the connection and try again.\n")

    except ConnectionResetError:
        print("Connection Reset: Please check the connection and try again.\n")

    except TimeoutError:
        print("Timeout Error: Please check the connection and try again.\n")

    except OSError:
        print("OSError: Please check the connection and try again.\n")


def __security_seed_wrapper(args):
    """Wrapper used to initiate security seed dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset
    session_type = args.sess_type
    level = args.sec_level
    num_seeds = args.num
    reset_delay = args.delay

    seed_list = []

    print("\nWaiting for Vehicle Identification Announcement\n")
    print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
    address, announcement = DoIPClient.await_vehicle_announcement()
    logical_address = arb_id_request
    ip, port = address

    try:

        doip_client = DoIPClient(ip, logical_address, client_logical_address=arb_id_response)
        conn = DoIPClientUDSConnector(doip_client)

        print("Security seed dump started. Press Ctrl+C to stop.\n")
        with Client(conn) as client:
            while num_seeds > len(seed_list) or num_seeds == 0:
                # Diagnostics Session Control
                try:
                    extended_session(client, session_type)

                except InvalidResponseException:
                    print("Unable to enter extended session. Retrying...\n")
                    continue
                try:
                    # Request seed
                    response = client.request_seed(level)

                    if response is None:
                        print("\nInvalid response")
                    elif response.data:
                        seed_list.append(response.data)
                        print("Seed received: {}\t(Total captured: {})"
                              .format(response.data,
                                      len(seed_list)), end="\r")
                        stdout.flush()

                    if reset_type:
                        ecu_reset(client, reset_type)
                        time.sleep(reset_delay)

                except NegativeResponseException:
                    break

    except KeyboardInterrupt:
        print("Interrupted by user.")
    except ValueError as e:
        print(e)
        return
    except ConnectionRefusedError:
        print("Please check the connection and try again.\n")

    except ConnectionResetError:
        print("Please check the connection and try again.\n")

    except TimeoutError:
        print("Please check the connection and try again.\n")

    except OSError:
        print("Please check the connection and try again.\n")

    if len(seed_list) > 0:
        print("\n")
        print("Security Access Seeds captured:")
        for seed in seed_list:
            print("".join("{:02x}".format(x) for x in seed))


def __dump_dids_wrapper(args):
    """Wrapper used to initiate data identifier dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    timeout = args.timeout
    min_did = args.min_did
    max_did = args.max_did
    print_results = True
    dump_dids(arb_id_request, arb_id_response, timeout, min_did, max_did,
              print_results)


def dump_dids(arb_id_request, arb_id_response, timeout,
              min_did=DUMP_DID_MIN, max_did=DUMP_DID_MAX, print_results=True):
    """
    Sends read data by identifier (DID) messages to 'arb_id_request'.
    Returns a list of positive responses received from 'arb_id_response' within
    'timeout' seconds or an empty list if no positive responses were received.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :param min_did: minimum device identifier to read
    :param max_did: maximum device identifier to read
    :param print_results: whether progress should be printed to stdout
    :type arb_id_request: int
    :type arb_id_response: int
    :type timeout: float or None
    :type min_did: int
    :type max_did: int
    :type print_results: bool
    :return: list of tuples containing DID and response bytes on success,
             empty list if no responses
    :rtype [(int, [int])] or []
    """
    # Sanity checks
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("Timeout value ({0}) cannot be negative"
                         .format(timeout))

    if max_did < min_did:
        raise ValueError("max_did must not be smaller than min_did - got min:0x{0:x}, max:0x{1:x}".format(
            min_did, max_did))

    responses = []
    print("Waiting for Vehicle Identification Announcement\n")
    print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
    address, announcement = DoIPClient.await_vehicle_announcement()
    logical_address = arb_id_request
    ip, port = address

    print("Discovering DIDs\n")

    try:
        doip_client = DoIPClient(ip, logical_address, client_logical_address=arb_id_response)
        conn = DoIPClientUDSConnector(doip_client)
        if print_results:
            print("Dumping DIDs in range 0x{:04x}-0x{:04x}\n".format(min_did, max_did))
            print("Identified DIDs:")
            print("DID    Value (hex)")
        for identifier in range(min_did, max_did + 1):
            try:
                with Client(conn, request_timeout=timeout) as client:
                    extended_session(client, session_type=3)
                    response = client.read_data_by_identifier(identifier)

                if response.positive:
                    responses.append((identifier, response.data))
                    if print_results:
                        print("0x{:04x}".format(identifier), list_to_hex_str(response))
            except ConfigError:
                sys.stderr = DevNull()
                continue
        if print_results:
            print("\nDone!")
        return responses

    except ConnectionRefusedError:
        print("Please check the connection and try again.\n")

    except ConnectionResetError:
        print("Please check the connection and try again.\n")

    except TimeoutError:
        print("Please check the connection and try again.\n")

    except OSError:
        print("Please check the connection and try again.\n")


def seed_randomness_fuzzer(args):
    """Wrapper used to initiate security randomness fuzzer"""
    arb_id_request = args.src
    arb_id_response = args.dst
    session_type = args.sess_type
    security_level = args.sec_level
    iterations = args.iter
    reset_delay = args.delay
    reset_type = args.reset_method
    inter = args.inter_delay

    seed_list = []

    print("Waiting for Vehicle Identification Announcement\n")
    print("Power cycle your ECU and wait for a few seconds for the broadcast to be received\n")
    address, announcement = DoIPClient.await_vehicle_announcement()
    logical_address = arb_id_request
    ip, port = address

    try:

        # Issue first reset with the supplied delay time
        print("Security seed dump started. Press Ctrl+C if you need to stop.\n")
        for _ in range(iterations):
            try:
                with DoIPClient(ip, logical_address, client_logical_address=arb_id_response) as doip_client:
                    conn = DoIPClientUDSConnector(doip_client)

                    with Client(conn) as client:
                        extended_session(client, session_type)

                        time.sleep(inter)

                        seed_response = client.request_seed(security_level)
                        seed_hex_str = list_to_hex_str(seed_response).data
                        seed_list.append(seed_hex_str)
                        print("Seed received: {0}".format(seed_hex_str))
                    ecu_reset(client, reset_type)

                time.sleep(reset_delay)

            except TimeoutError:
                print("Timeout Error Exception: You may need to increase the intermediate delay (-id).")
                time.sleep(0.5)
                continue
            except NegativeResponseException:
                time.sleep(0.5)
                continue
            except ConnectionRefusedError:
                print("Connection Refused Error: You may need to increase the reset delay (-d).")
                time.sleep(0.5)
                continue

    except KeyboardInterrupt:
        print("Interrupted by user.")

    except ValueError as e:
        print(e)
        return

    # Print captured seeds and found duplicates
    if len(seed_list) > 0:
        print("\n")
        print("Security Access Seeds captured:")
        for seed in seed_list:
            print(seed)
        print("\nDuplicates found: \n", find_duplicates(seed_list))


def __parse_args(args):
    """Parser for module arguments"""
    parser = argparse.ArgumentParser(
        prog="cc.py doip",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="DoIP module for "
                    "CaringCaribou",
        epilog="""Example usage:
  cc.py doip discovery
  cc.py doip discovery -blacklist 0x123 0x456
  cc.py doip discovery -autoblacklist 10
  cc.py doip services 0x733 0x633
  cc.py doip ecu_reset 1 0x733 0x633
  cc.py doip testerpresent 0x733
  cc.py doip security_seed 0x3 0x1 0x733 0x633 -r 1 -d 0.5
  cc.py doip dump_dids 0x733 0x633
  cc.py doip dump_dids 0x733 0x633 --min_did 0x6300 --max_did 0x6fff -t 0.1
  cc.py doip seed_randomness_fuzzer 2 2 0x733 0x633 -m 1 -t 10 -d 50 -id 4""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for diagnostics discovery
    parser_discovery = subparsers.add_parser("discovery")
    parser_discovery.add_argument("-min",
                                  type=parse_int_dec_or_hex, default=None,
                                  help="min arbitration ID "
                                       "to send request for")
    parser_discovery.add_argument("-max",
                                  type=parse_int_dec_or_hex, default=None,
                                  help="max arbitration ID "
                                       "to send request for")
    parser_discovery.add_argument("-b", "--blacklist", metavar="B",
                                  type=parse_int_dec_or_hex, default=[],
                                  nargs="+",
                                  help="arbitration IDs to blacklist "
                                       "responses from")
    parser_discovery.add_argument("-ab", "--autoblacklist", metavar="N",
                                  type=float, default=0,
                                  help="listen for false positives for N seconds "
                                       "and blacklist matching arbitration "
                                       "IDs before running discovery")
    parser_discovery.add_argument("-d", "--delay", metavar="D",
                                  type=float, default=DELAY_DISCOVERY,
                                  help="D seconds delay between messages "
                                       "(default: {0})".format(DELAY_DISCOVERY))
    parser_discovery.set_defaults(func=__uds_discovery_wrapper)

    # Parser for diagnostics service discovery
    parser_info = subparsers.add_parser("services")
    parser_info.add_argument("src",
                             type=parse_int_dec_or_hex,
                             help="arbitration ID to transmit to")
    parser_info.add_argument("dst",
                             type=parse_int_dec_or_hex,
                             help="arbitration ID to listen to")
    parser_info.add_argument("-t", "--timeout", metavar="T",
                             type=float, default=TIMEOUT_SERVICES,
                             help="wait T seconds for response before "
                                  "timeout (default: {0})"
                             .format(TIMEOUT_SERVICES))
    parser_info.set_defaults(func=__service_discovery_wrapper)

    # Parser for ECU Reset
    parser_ecu_reset = subparsers.add_parser("ecu_reset")
    parser_ecu_reset.add_argument("reset_type", metavar="type",
                                  type=parse_int_dec_or_hex,
                                  help="Reset type: 1=hard, 2=key off/on, "
                                       "3=soft, "
                                       "4=enable rapid power shutdown, "
                                       "5=disable rapid power shutdown")
    parser_ecu_reset.add_argument("src",
                                  type=parse_int_dec_or_hex,
                                  help="arbitration ID to transmit to")
    parser_ecu_reset.add_argument("dst",
                                  type=parse_int_dec_or_hex,
                                  help="arbitration ID to listen to")
    parser_ecu_reset.set_defaults(func=__ecu_reset_wrapper)

    # Parser for TesterPresent
    parser_tp = subparsers.add_parser("testerpresent")
    parser_tp.add_argument("src",
                           type=parse_int_dec_or_hex,
                           help="arbitration ID to transmit to")
    parser_tp.add_argument("dst",
                           type=parse_int_dec_or_hex,
                           help="arbitration ID to listen to")
    parser_tp.add_argument("-d", "--delay", metavar="D",
                           type=float, default=DELAY_TESTER_PRESENT,
                           help="send TesterPresent every D seconds "
                                "(default: {0})".format(DELAY_TESTER_PRESENT))
    parser_tp.add_argument("-dur", "--duration", metavar="S",
                           type=float,
                           help="automatically stop after S seconds")
    parser_tp.set_defaults(func=__tester_present_wrapper)

    # Parser for SecuritySeedDump
    parser_secseed = subparsers.add_parser("security_seed")
    parser_secseed.add_argument("sess_type", metavar="stype",
                                type=parse_int_dec_or_hex,
                                help="Session Type: 1=defaultSession "
                                     "2=programmingSession 3=extendedSession "
                                     "4=safetySession ")
    parser_secseed.add_argument("sec_level", metavar="level",
                                type=parse_int_dec_or_hex,
                                help="Security level: "
                                     "[0x1-0x41 (odd only)]=OEM "
                                     "0x5F=EOLPyrotechnics "
                                     "[0x61-0x7E]=Supplier "
                                     "[0x0, 0x43-0x5E, 0x7F]=ISOSAEReserved")
    parser_secseed.add_argument("src",
                                type=parse_int_dec_or_hex,
                                help="arbitration ID to transmit to")
    parser_secseed.add_argument("dst",
                                type=parse_int_dec_or_hex,
                                help="arbitration ID to listen to")
    parser_secseed.add_argument("-r", "--reset", metavar="RTYPE",
                                type=parse_int_dec_or_hex,
                                help="Enable reset between security seed "
                                     "requests. Valid RTYPE integers are: "
                                     "1=hardReset, 2=key off/on, 3=softReset, "
                                     "4=enable rapid power shutdown, "
                                     "5=disable rapid power shutdown. "
                                     "(default: None)")
    parser_secseed.add_argument("-d", "--delay", metavar="D",
                                type=float, default=DELAY_SECSEED_RESET,
                                help="Wait D seconds between reset and "
                                     "security seed request. You'll likely "
                                     "need to increase this when using RTYPE: "
                                     "1=hardReset. Does nothing if RTYPE "
                                     "is None. (default: {0})"
                                .format(DELAY_SECSEED_RESET))
    parser_secseed.add_argument("-n", "--num", metavar="NUM", default=0,
                                type=parse_int_dec_or_hex,
                                help="Specify a positive number of security"
                                     " seeds to capture before terminating. "
                                     "A '0' is interpreted as infinity. "
                                     "(default: 0)")
    parser_secseed.set_defaults(func=__security_seed_wrapper)

    # Parser for dump_did
    parser_did = subparsers.add_parser("dump_dids")
    parser_did.add_argument("src",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to transmit to")
    parser_did.add_argument("dst",
                            type=parse_int_dec_or_hex,
                            help="arbitration ID to listen to")
    parser_did.add_argument("-t", "--timeout",
                            type=float, metavar="T",
                            default=DUMP_DID_TIMEOUT,
                            help="wait T seconds for response before "
                                 "timeout")
    parser_did.add_argument("--min_did",
                            type=parse_int_dec_or_hex,
                            default=DUMP_DID_MIN,
                            help="minimum device identifier (DID) to read (default: 0x0000)")
    parser_did.add_argument("--max_did",
                            type=parse_int_dec_or_hex,
                            default=DUMP_DID_MAX,
                            help="maximum device identifier (DID) to read (default: 0xFFFF)")
    parser_did.set_defaults(func=__dump_dids_wrapper)

    # Parser for Delay fuzz testing
    parser_randomness_fuzzer = subparsers.add_parser("seed_randomness_fuzzer")
    parser_randomness_fuzzer.add_argument("sess_type", metavar="stype",
                                          type=parse_int_dec_or_hex,
                                          help="Session Type: 1=defaultSession "
                                               "2=programmingSession 3=extendedSession "
                                               "4=safetySession ")
    parser_randomness_fuzzer.add_argument("sec_level", metavar="level",
                                          type=parse_int_dec_or_hex,
                                          help="Security level: "
                                               "[0x1-0x41 (odd only)]=OEM "
                                               "0x5F=EOLPyrotechnics "
                                               "[0x61-0x7E]=Supplier "
                                               "[0x0, 0x43-0x5E, 0x7F]=ISOSAEReserved")
    parser_randomness_fuzzer.add_argument("src",
                                          type=parse_int_dec_or_hex,
                                          help="arbitration ID to transmit to")
    parser_randomness_fuzzer.add_argument("dst",
                                          type=parse_int_dec_or_hex,
                                          help="arbitration ID to listen to")
    parser_randomness_fuzzer.add_argument("-t", "--iter", metavar="ITERATIONS", default=1000,
                                          type=parse_int_dec_or_hex,
                                          help="Number of iterations of seed requests. "
                                               "It is highly suggested to perform >=1000  "
                                               "for accurate results. "
                                               "(default: 1000)")
    parser_randomness_fuzzer.add_argument("-r", "--reset", metavar="RTYPE", default=1,
                                          type=parse_int_dec_or_hex,
                                          help="Enable reset between security seed "
                                               "requests. Valid RTYPE integers are: "
                                               "1=hardReset, 2=key off/on, 3=softReset, "
                                               "4=enable rapid power shutdown, "
                                               "5=disable rapid power shutdown. "
                                               "This attack is based on hard ECUReset (1) "
                                               "as it targets seed randomness based on "
                                               "the system clock. (default: hardReset)")
    parser_randomness_fuzzer.add_argument("-id", "--inter_delay", metavar="RTYPE", default=0.1,
                                          type=float,
                                          help="Intermediate delay between messages:"
                                               "(default: 0.1)")
    parser_randomness_fuzzer.add_argument("-m", "--reset_method", metavar="RMETHOD", default=1,
                                          type=parse_int_dec_or_hex,
                                          help="The method that the ECUReset will happen: "
                                               "1=before each seed request "
                                               "0=once before the seed requests start "
                                               "(default: 1) *This method works better with option 1.*")
    parser_randomness_fuzzer.add_argument("-d", "--delay", metavar="D",
                                          type=float, default=DELAY_SECSEED_RESET,
                                          help="Wait D seconds between reset and "
                                               "security seed request. You'll likely "
                                               "need to increase this when using RTYPE: "
                                               "1=hardReset. Does nothing if RTYPE "
                                               "is None. (default: {0})"
                                          .format(DELAY_FUZZ_RESET))
    parser_randomness_fuzzer.set_defaults(func=seed_randomness_fuzzer)

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    """Module main wrapper"""
    try:
        args = __parse_args(arg_list)
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
