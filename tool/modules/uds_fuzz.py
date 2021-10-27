#!/usr/bin/env python
# Released under GNU General Public License v3
# https://github.com/Cr0wTom/UDS-Seed-Randomness-Fuzzer

from __future__ import print_function
from lib.can_actions import auto_blacklist
from lib.common import list_to_hex_str, parse_int_dec_or_hex
from lib.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MAX_EXTENDED
from lib.constants import ARBITRATION_ID_MIN
from lib.iso15765_2 import IsoTp
from lib.iso14229_1 import Constants, Iso14229_1, NegativeResponseCodes, Services
from sys import stdout, version_info
import argparse
import datetime
import time


# Python 2/3 compatibility
if version_info[0] == 2:
    range = xrange
    input = raw_input

NRC_NAMES = {
    0x00: "POSITIVE_RESPONSE",
    0x10: "GENERAL_REJECT",
    0x11: "SERVICE_NOT_SUPPORTED",
    0x12: "SUB_FUNCTION_NOT_SUPPORTED",
    0x13: "INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT",
    0x14: "RESPONSE_TOO_LONG",
    0x21: "BUSY_REPEAT_REQUEST",
    0x22: "CONDITIONS_NOT_CORRECT",
    0x24: "REQUEST_SEQUENCE_ERROR",
    0x25: "NO_RESPONSE_FROM_SUBNET_COMPONENT",
    0x26: "FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION",
    0x31: "REQUEST_OUT_OF_RANGE",
    0x33: "SECURITY_ACCESS_DENIED",
    0x35: "INVALID_KEY",
    0x36: "EXCEEDED_NUMBER_OF_ATTEMPTS",
    0x37: "REQUIRED_TIME_DELAY_NOT_EXPIRED",
    0x70: "UPLOAD_DOWNLOAD_NOT_ACCEPTED",
    0x71: "TRANSFER_DATA_SUSPENDED",
    0x72: "GENERAL_PROGRAMMING_FAILURE",
    0x73: "WRONG_BLOCK_SEQUENCE_COUNTER",
    0x78: "REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING",
    0x7E: "SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION",
    0x7F: "SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION",
    0x81: "RPM_TOO_HIGH",
    0x82: "RPM_TOO_LOW",
    0x83: "ENGINE_IS_RUNNING",
    0x84: "ENGINE_IS_NOT_RUNNING",
    0x85: "ENGINE_RUN_TIME_TOO_LOW",
    0x86: "TEMPERATURE_TOO_HIGH",
    0x87: "TEMPERATURE_TOO_LOW",
    0x88: "VEHICLE_SPEED_TOO_HIGH",
    0x89: "VEHICLE_SPEED_TOO_LOW",
    0x8A: "THROTTLE_PEDAL_TOO_HIGH",
    0x8B: "THROTTLE_PEDAL_TOO_LOW",
    0x8C: "TRANSMISSION_RANGE_NOT_IN_NEUTRAL",
    0x8D: "TRANSMISSION_RANGE_NOT_IN_GEAR",
    0x8F: "BRAKE_SWITCHES_NOT_CLOSED",
    0x90: "SHIFT_LEVER_NOT_IN_PARK",
    0x91: "TORQUE_CONVERTER_CLUTCH_LOCKED",
    0x92: "VOLTAGE_TOO_HIGH",
    0x93: "VOLTAGE_TOO_LOW"
}

# Number of seconds to wait between messages
DELAY_SECSEED_RESET = 0.011
DELAY_FUZZ_RESET = 3.901

# Message data length limits
MIN_DATA_LENGTH = 1
MAX_DATA_LENGTH = 8
# Max size of random seed if no seed is provided in arguments
DEFAULT_SEED_MAX = 2 ** 16
# Number of sub-lists to split message list into per round in 'replay' mode
REPLAY_NUMBER_OF_SUB_LISTS = 5
BYTE_MIN = 0x00
BYTE_MAX = 0xFF

# Duplicate testing from https://www.iditect.com/guide/python/python_howto_find_the_duplicates_in_a_list.html
def find_duplicates(sequence):
  first_seen = set()
  first_seen_add = first_seen.add  
  duplicates = set(i for i in sequence if i in first_seen or first_seen_add(i) )
  return duplicates 


def ecu_reset(arb_id_request, arb_id_response, reset_type, timeout):
    """Sends an ECU Reset message to 'arb_id_request'. Returns the first
        response received from 'arb_id_response' within 'timeout' seconds
        or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param reset_type: value corresponding to a reset type
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response int
    :type reset_type: int
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if not BYTE_MIN <= reset_type <= BYTE_MAX:
        raise ValueError("reset type must be within interval "
                         "0x{0:02x}-0x{1:02x}"
                         .format(BYTE_MIN, BYTE_MAX))
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("timeout value ({0}) cannot be negative"
                         .format(timeout))

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.ecu_reset(reset_type=reset_type)
            return response


def print_negative_response(response):
    """
    Helper function for decoding and printing a negative response received
    from a UDS server.

    :param response: Response data after CAN-TP layer has been removed
    :type response: [int]

    :return: Nothing
    """
    nrc = response[2]
    nrc_description = NRC_NAMES.get(nrc, "Unknown NRC value")
    print("Received negative response code (NRC) 0x{0:02x}: {1}"
          .format(nrc, nrc_description))

def seed_randomness_fuzzer(args):
    """Wrapper used to initiate security seed dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset
    session_type = args.sess_type
    level = args.sec_level
    iterations = args.iter
    reset_delay = args.delay
    reset_method = args.reset_method

    seed_list = []
    try: 
        print("Security seed dump started. Press Ctrl+C if you need to stop.\n")
        ecu_reset(arb_id_request, arb_id_response, reset_type, None)
        time.sleep(reset_delay)
        for i in range(iterations):

            # Extended diagnostics
            response = extended_session(arb_id_request,
                                        arb_id_response,
                                        session_type)
            if not Iso14229_1.is_positive_response(response):
                print("Unable to enter extended session. Retrying...\n")
                continue

            # Request seed
            response = request_seed(arb_id_request, arb_id_response,
                                    level, None, None)
            if response is None:
                print("\nInvalid response")
            elif Iso14229_1.is_positive_response(response):
                seed_list.append(list_to_hex_str(response[2:]))
                print("Seed received: {}\t(Total captured: {})"
                    .format(list_to_hex_str(response[2:]),
                            len(seed_list)), end="\r")
                stdout.flush()
            else:
                print_negative_response(response)

            if reset_method == 1:
                ecu_reset(arb_id_request, arb_id_response, reset_type, None)
                time.sleep(reset_delay)
            elif reset_method == 0:
                continue
            else:
                print("Not a valid reset method: " , reset_method)

        print("Duplicates found: \n", find_duplicates(seed_list))

    except KeyboardInterrupt:
        print("Interrupted by user.")
    except ValueError as e:
        print(e)
        return

    if len(seed_list) > 0:
        print("\n")
        print("Security Access Seeds captured:")
        for seed in seed_list:
            print(seed)


def delay_fuzzer(args):
    """Wrapper used to initiate security seed dump"""
    arb_id_request = args.src
    arb_id_response = args.dst
    reset_type = args.reset
    session_type = args.sess_type
    level = args.sec_level
    seed = args.seed
    reset_delay = args.delay

    seed_list = []
    try:
        print("Security seed dump started. Press Ctrl+C to stop.\n")
        while num_seeds > len(seed_list) or num_seeds == 0:
            # Extended diagnostics
            ecu_reset(arb_id_request, arb_id_response, reset_type, None)
            time.sleep(reset_delay)
            response = extended_session(arb_id_request,
                                        arb_id_response,
                                        session_type)
            if not Iso14229_1.is_positive_response(response):
                print("Unable to enter extended session. Retrying...\n")
                continue

            # Request seed
            response = request_seed(arb_id_request, arb_id_response,
                                    level, None, None)
            if response is None:
                print("\nInvalid response")
            elif Iso14229_1.is_positive_response(response):
                seed_list.append(list_to_hex_str(response[2:]))
                print("Seed received: {}\t(Total captured: {})"
                      .format(list_to_hex_str(response[2:]),
                              len(seed_list)), end="\r")
                stdout.flush()
                if seed in seed_list:
                    print("\nSeed found with delay: ", reset_delay)
                    break
            else:
                print_negative_response(response)
                break
            if reset_type:
                ecu_reset(arb_id_request, arb_id_response, reset_type, None)
                time.sleep(reset_delay)
                reset_delay += 0.001
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except ValueError as e:
        print(e)
        return

    if len(seed_list) > 0:
        print("\n")
        print("Security Access Seeds captured:")
        for seed in seed_list:
            print(seed)


def extended_session(arb_id_request, arb_id_response, session_type):
    with IsoTp(arb_id_request=arb_id_request, arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            response = uds.diagnostic_session_control(session_type)
            return response


def request_seed(arb_id_request, arb_id_response, level, data_record, timeout):
    """Sends an Request seed message to 'arb_id_request'. Returns the
       first response received from 'arb_id_response' within 'timeout'
       seconds or None otherwise.

    :param arb_id_request: arbitration ID for requests
    :param arb_id_response: arbitration ID for responses
    :param level: vehicle manufacturer specific access level to request
                  seed for
    :param data_record: optional vehicle manufacturer specific data to
                        transmit when requesting seed
    :param timeout: seconds to wait for response before timeout, or None
                    for default UDS timeout
    :type arb_id_request: int
    :type arb_id_response: int
    :type level: int
    :type data_record: [int] or None
    :type timeout: float or None
    :return: list of response byte values on success, None otherwise
    :rtype [int] or None
    """
    # Sanity checks
    if (not Services.SecurityAccess.RequestSeedOrSendKey()
       .is_valid_request_seed_level(level)):
        raise ValueError("Invalid request seed level")
    if isinstance(timeout, float) and timeout < 0.0:
        raise ValueError("Timeout value ({0}) cannot be negative"
                         .format(timeout))

    with IsoTp(arb_id_request=arb_id_request,
               arb_id_response=arb_id_response) as tp:
        # Setup filter for incoming messages
        tp.set_filter_single_arbitration_id(arb_id_response)
        with Iso14229_1(tp) as uds:
            # Set timeout
            if timeout is not None:
                uds.P3_CLIENT = timeout

            response = uds.security_access_request_seed(level, data_record)
            return response

           

def __parse_args(args):
    """Parser for module arguments"""
    parser = argparse.ArgumentParser(
                prog="cc.py uds_fuzz",
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description="UDS seed randomness fuzzer module for "
                "CaringCaribou",
                epilog="""Example usage:
  cc.py uds_fuzz seed_randomness_fuzzer -t 10 -d 3 3 0x03 0x733 0x633""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Parser for Delay fuzz testing
    parser_delay_fuzzer = subparsers.add_parser("delay_fuzzer")
    parser_delay_fuzzer.add_argument("sess_type", metavar="stype",
                                type=parse_int_dec_or_hex,
                                help="Session Type: 1=defaultSession "
                                     "2=programmingSession 3=extendedSession "
                                     "4=safetySession [0x40-0x5F]=OEM "
                                     "[0x60-0x7E]=Supplier "
                                     "[0x0, 0x5-0x3F, 0x7F]=ISOSAEReserved")
    parser_delay_fuzzer.add_argument("sec_level", metavar="level",
                                type=parse_int_dec_or_hex,
                                help="Security level: "
                                     "[0x1-0x41 (odd only)]=OEM "
                                     "0x5F=EOLPyrotechnics "
                                     "[0x61-0x7E]=Supplier "
                                     "[0x0, 0x43-0x5E, 0x7F]=ISOSAEReserved")
    parser_delay_fuzzer.add_argument("seed", metavar="SEED", 
                                type=parse_int_dec_or_hex,
                                help="Specify the target seed you want to intercept."
                                     "e.g. 0x0767034141414141 ")
    parser_delay_fuzzer.add_argument("src",
                                type=parse_int_dec_or_hex,
                                help="arbitration ID to transmit to")
    parser_delay_fuzzer.add_argument("dst",
                                type=parse_int_dec_or_hex,
                                help="arbitration ID to listen to")
    parser_delay_fuzzer.add_argument("-r", "--reset", metavar="RTYPE", default=1,
                                type=parse_int_dec_or_hex,
                                help="Enable reset between security seed "
                                     "requests. Valid RTYPE integers are: "
                                     "1=hardReset, 2=key off/on, 3=softReset, "
                                     "4=enable rapid power shutdown, "
                                     "5=disable rapid power shutdown. "
                                     "(default: hardReset)")
    parser_delay_fuzzer.add_argument("-d", "--delay", metavar="D",
                                type=float, default=DELAY_SECSEED_RESET,
                                help="Wait D seconds between reset and "
                                     "security seed request. You'll likely "
                                     "need to increase this when using RTYPE: "
                                     "1=hardReset. Does nothing if RTYPE "
                                     "is None. (default: {0})"
                                     .format(DELAY_SECSEED_RESET))
    parser_delay_fuzzer.set_defaults(func=delay_fuzzer)

    # Parser for Delay fuzz testing
    parser_randomness_fuzzer = subparsers.add_parser("seed_randomness_fuzzer")
    parser_randomness_fuzzer.add_argument("sess_type", metavar="stype",
                                type=parse_int_dec_or_hex,
                                help="Session Type: 1=defaultSession "
                                     "2=programmingSession 3=extendedSession "
                                     "4=safetySession [0x40-0x5F]=OEM "
                                     "[0x60-0x7E]=Supplier "
                                     "[0x0, 0x5-0x3F, 0x7F]=ISOSAEReserved")
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