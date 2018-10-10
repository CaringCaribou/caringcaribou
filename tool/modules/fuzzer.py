# fuzzer.py
#
# Dictionary:
#   1.  "cansend directive"
#       A string that follows the formatting of (for example): "123#FFFFFFFF".
#       This is similar to the arguments one would pass to the cansend command line tool (part of can-util).
#   2. "composite cansend directive"
#       A cansend directive split up in its id and payload: [id, payload].
from __future__ import print_function
from sys import version_info, stdout
import argparse
import random
import string

from itertools import product
from lib.can_actions import *
from time import sleep


# Python 2/3 compatibility
if version_info[0] == 2:
    range = xrange
    input = raw_input


# --- [0]
# Static variable definitions and generic methods
# ---


# Number of seconds to wait between messages
CALLBACK_HANDLER_DURATION = 0.01
# Payload length limits
MIN_PL_LENGTH = 1
MAX_PL_LENGTH = 8
# Max size of random seed if no seed is provided in arguments
DEFAULT_SEED_MAX = 2**16
# Number of sub-lists to split message list into per round in 'replay' mode
REPLAY_NUMBER_OF_SUB_LISTS = 5
# Default payload, split into nibbles
DEFAULT_PAYLOAD = [0x0] * 16

# The characters used to generate random ids/payloads.
CHARACTERS = string.hexdigits[0: 10] + string.hexdigits[16: 22]
# The leading value in a can id is a value between 0 and 7.
LEAD_ID_CHARACTERS = string.digits[0: 8]
# The max length of an id.
# Do note that the fuzzer by default works with an id of length 3.
# It thus does not use extended can ids by default
MAX_ID_LENGTH = 4
# The max length of a payload.
MAX_PAYLOAD_LENGTH = 16
# An extended arbitration id consisting only of zeros.
ZERO_ARB_ID = "0" * MAX_ID_LENGTH
# A payload consisting only of zeros.
ZERO_PAYLOAD = "0" * MAX_PAYLOAD_LENGTH


def directive_send(arb_id, payload, response_handler, can_wrap):
    """
    Sends a cansend directive.

    :param arb_id: The destination arbitration id.
    :param payload: The payload to be sent.
    :param response_handler: The callback handler that needs to be called when a response message is received.
    :param can_wrap: CanActions instance used to send message
    """
    arb_id = "0x" + arb_id  # FIXME auto-prefix should be removed to use default behavior
    send_msg = payload_to_str_base(payload)
    arb_id = int_from_str_base(arb_id)
    # Send the message on the CAN bus and register a callback
    # handler for incoming messages
    msg_list = list_int_from_str_base(send_msg)
    can_wrap.set_listener(response_handler)
    can_wrap.send(msg_list, arb_id)
    # Letting callback handler be active for CALLBACK_HANDLER_DURATION seconds
    sleep(CALLBACK_HANDLER_DURATION)
    # can_wrap.clear_listeners()


def write_directive_to_file(filename, arb_id, payload):
    """
    Writes a cansend directive to a file.

    :param filename: The filename of the file to write to.
    :param arb_id: The arbitration id of the cansend directive.
    :param payload: The payload of the cansend directive.
    """
    fd = open(filename, "a")
    try:
        fd.write(arb_id + "#" + payload + "\n")
    finally:
        fd.close()


def directive_str(arb_id, payload):
    """
    Converts a directive to its string representation

    :param arb_id: message arbitration ID
    :param payload: message data bytes
    :return: str representing directive
    """
    data = "".join(["{0:02X}".format(x) for x in payload])
    directive = "{0:03X}#{1}".format(arb_id, data)
    return directive


def write_directive_to_file_handle(file_handle, arb_id, payload):
    """
    Writes a cansend directive to a file

    :param file_handle: handle for the file to write to
    :param arb_id: arbitration ID of the cansend directive
    :param payload: payload of the cansend directive
    """
    directive = directive_str(arb_id, payload)
    file_handle.write("{0}\n".format(directive))


def set_seed(seed=None):
    if seed is None:
        seed = random.randint(0, DEFAULT_SEED_MAX)
    else:
        seed = int_from_str_base(seed)
    print("Seed: {0} (0x{0:x})".format(seed))
    random.seed(seed)


# --- [1]
# Converter methods
# ---


def list_int_from_str_base(line):
    """
    Converts a given string to its list int representation.
    Uses CaringCaribou's int_from_str_base implementation.

    :param line: A given string that follows the format of (for example): "0xFF 0xFF 0xFF 0xFF".
    :return: Returns a list of ints representing the values in the string.
             For example: [0xFF, 0xFF, 0xFF, 0xFF] (with 0xFF in its int representation).
    """
    temp = line.split()
    for i in range(len(temp)):
        temp[i] = int_from_str_base(temp[i])
    return temp


def payload_to_str_base(payload):
    """
    Converts a given payload to its str_base representation.
    A str_base payload is for example: "0xFF 0xFF 0xFF 0xFF".

    :param payload: The payload to be converted.
    :return: Returns the str_base representation of the payload.
    """
    result = ""
    for i in range(0, len(payload), 2):
        result += "0x" + payload[i] + payload[i + 1] + " "
    result = result[:len(result) - 1]
    return result


def string_to_bool(value):
    """
    Converts a given string to a boolean.

    :param value:
    :return: False if value.upper() == "FALSE" or value == "0" or value == "" else True
    """
    return False if value.upper() == "FALSE" or value == "0" or value == "" else True


def parse_directive(directive):
    """
    Parses a cansend directive

    :param directive: str representing a cansend directive
    :return: tuple (int arbitration_id, [int data_byte])
    """
    segments = directive.split("#")
    arb_id = int(segments[0], 16)
    data_str = segments[1]
    data = [int(data_str[i:i+2], 16) for i in range(0, len(data_str), 2)]
    return arb_id, data


# --- [2]
# Methods that handle random fuzzing.
# ---


def get_random_arbitration_id(min_id, max_id):
    """
    Returns an arbitration ID in the range min_id <= arb_id <= max_id

    :param min_id: Minimum allowed arbitration ID (inclusive)
    :param max_id: Maximum allowed arbitration ID (inclusive)
    :return: int arbitration ID
    """
    arb_id = random.randint(min_id, max_id)
    return arb_id


def get_random_payload_data(min_length, max_length):
    # Decide number of bytes to generate
    payload_length = random.randint(min_length, max_length)
    # Generate random bytes
    payload = []
    for i in range(payload_length):
        data_byte = random.randint(BYTE_MIN, BYTE_MAX)
        payload.append(data_byte)
    return payload


def random_fuzz(static_arb_id, static_payload, filename=None, min_id=ARBITRATION_ID_MIN, max_id=ARBITRATION_ID_MAX,
                min_payload_length=MIN_PL_LENGTH, max_payload_length=MAX_PL_LENGTH, seed=None):
    """
    A simple random fuzzer algorithm, which sends random or static CAN payloads to random or static arbitration IDs

    :param static_arb_id: force usage of given arbitration ID
    :param static_payload: force usage of given payload
    :param filename: file to write cansend directives to
    :param min_id: minimum allowed arbitration ID
    :param max_id: maximum allowed arbitration ID
    :param min_payload_length: minimum allowed payload length
    :param max_payload_length: maximum allowed payload length
    :param seed: use given seed instead of random seed
    """
    # Sanity checks
    if min_id > max_id:
        raise ValueError("min_id must not be larger than max_id")
    if min_payload_length > max_payload_length:
        raise ValueError("min_payload_length must not be larger than max_payload_length")

    # Seed handling
    set_seed(seed)

    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        if msg.arbitration_id != arb_id or list(msg.data) != payload:
            directive = directive_str(arb_id, payload)
            print("Directive: {0}".format(directive))
            print("  Received message: {0}".format(msg))

    arb_id = None
    payload = None
    file_logging_enabled = filename is not None
    output_file = None
    try:
        if file_logging_enabled:
            output_file = open(filename, "a")
        with CanActions() as can_wrap:
            # Register callback handler for incoming messages
            can_wrap.add_listener(response_handler)
            # Fuzzing logic
            while True:
                # Set arbitration ID
                if static_arb_id is None:
                    # Use a random arbitration ID
                    arb_id = get_random_arbitration_id(min_id, max_id)
                else:
                    # Use the static arbitration ID
                    arb_id = static_arb_id

                # Set payload
                if static_payload is None:
                    payload = get_random_payload_data(min_payload_length, max_payload_length)
                else:
                    payload = static_payload

                # Send message
                can_wrap.send(data=payload, arb_id=arb_id)
                sleep(CALLBACK_HANDLER_DURATION)

                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, payload)
    finally:
        if output_file is not None:
            output_file.close()

# --- [3]
# Methods that handle linear fuzzing.
# ---


def linear_file_fuzz(filename):
    """
    Replay cansend directives from the given file

    :param filename: Source file to read cansend directives from
    """

    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        if msg.arbitration_id != arb_id or list(msg.data) != payload:
            print("Directive: {0}".format(directive))
            print("  Received message: {0}".format(msg))

    arb_id = None
    payload = None

    with open(filename, "r") as fd:
        with CanActions() as can_wrap:
            can_wrap.add_listener(response_handler)
            for line in fd:
                directive = line.rstrip()
                if directive:
                    arb_id, payload = parse_directive(directive)
                    can_wrap.send(data=payload, arb_id=arb_id)
                    sleep(CALLBACK_HANDLER_DURATION)


# --- [4]
# Methods that handle replay fuzzing.
# ---


def split_composites(composites, pieces):
    """
    Generator function which splits 'old_composites' into smaller sub-lists

    :param composites: list to split
    :param pieces: number of sub-lists to produce
    :return: yields one sub-list at a time
    """
    length = len(composites)
    for i in range(pieces):
        sub_list = composites[i * length // pieces: (i + 1) * length // pieces]
        if len(sub_list) == 0:
            # Skip empty sub-lists (e.g. if a list of 2 elements if split into 3 parts, one will be empty)
            continue
        yield sub_list


def replay_file_fuzz(all_composites):
    """
    Replays a list of composites causing an effect, prompting for input to help isolate the message causing the effect

    :param all_composites: list of composites
    :return: str directive if message is found,
             None otherwise
    """

    def response_handler(msg):
        if msg.arbitration_id != arb_id or list(msg.data) != payload:
            response_directive = directive_str(msg.arbitration_id, msg.data)
            print("  Received {0}".format(response_directive))

    arb_id = None
    payload = None
    composites = None
    directive = None
    repeat = False

    with CanActions() as can_wrap:
        try:
            # Send all messages in first round
            gen = split_composites(all_composites, 1)
            while True:
                print()
                if repeat:
                    # Keep previous list of messages to send
                    repeat = False
                else:
                    # Get next list of messages to send
                    composites = next(gen)
                # Enable CAN listener
                can_wrap.add_listener(response_handler)
                # Send messages
                for composite in composites:
                    arb_id = composite[0]
                    payload = composite[1]
                    directive = directive_str(arb_id, payload)
                    print("Sending {0}".format(directive))
                    can_wrap.send(data=payload, arb_id=arb_id)
                    sleep(CALLBACK_HANDLER_DURATION)
                # Disable CAN listener
                can_wrap.clear_listeners()

                # Get user input
                print("\nWas the desired effect observed?")
                valid_response = False
                while not valid_response:
                    valid_response = True

                    response = input("(y)es | (n)o | (r)eplay | (q)uit: ").lower()

                    if response == "y":
                        if len(composites) == 1:
                            # Single message found
                            print("\nMatch found! Message causing effect: {0}".format(directive))
                            return directive
                        else:
                            # Split into even smaller lists of messages
                            gen = split_composites(composites, REPLAY_NUMBER_OF_SUB_LISTS)
                    elif response == "n":
                        # Try next list of messages
                        pass
                    elif response == "r":
                        # Repeat batch
                        repeat = True
                    elif response == "q":
                        # Quit
                        return
                    else:
                        # Invalid choice - ask again
                        print("Invalid choice")
                        valid_response = False

        except StopIteration:
            # No more messages to try - give up
            print("\nNo match was found.")
            return None


# --- [5]
# Methods that handle brute force fuzzing.
# ---


def ring_bf_fuzz(arb_id, initial_payload, payload_bitmap, filename=None, start_index=0,
                 show_progress=True, show_responses=True):
    """
    Performs a brute force of selected nibbles (octets) of a payload for a given arbitration ID.
    Nibble selection is controlled by bool list 'payload_bitmap'.

    Example:
    ring_bf_fuzz(0x123, [0x1, 0x2, 0xA, 0xB], [True, False, False, True])
    will cause the following messages to be sent:

    0x123#02A0
    0x123#02A1
    0x123#02A2
    (...)
    0x123#02AF
    0x123#12A0
    0x123#12A1
    (...)
    0x123#F2AF

    :param arb_id: int arbitration ID
    :param initial_payload: list of nibbles (ints in interval 0x0-0xF, inclusive)
    :param payload_bitmap: list of bool values, representing which nibbles of 'initial_payload' to bruteforce
    :param filename: file to write cansend directives to
    :param start_index: int index to start at (can be used to resume interrupted session)
    :param show_progress: bool indicating whether progress should be printed to stdout
    :param show_responses: bool indicating whether responses should be printed to stdout
    """
    # Sanity checks
    if not 2 <= len(initial_payload) <= 16:
        raise ValueError("Invalid initial payload: must be between 2 and 16 nibbles")
    if not len(initial_payload) % 2 == 0:
        raise ValueError("Invalid initial payload: must have an even length")
    if not len(initial_payload) == len(payload_bitmap):
        raise ValueError("Payload ({0}) and payload bitmap ({1}) must have the same length".format(len(initial_payload),
                                                                                                   len(payload_bitmap)))

    number_of_nibbles = len(payload_bitmap)
    number_of_nibbles_to_bruteforce = sum(payload_bitmap)
    end_index = 16 ** number_of_nibbles_to_bruteforce

    if not 0 <= start_index <= end_index:
        raise ValueError("Invalid start index '{0}', current range is [0-{1}]".format(start_index, end_index))

    def response_handler(msg):
        # Callback handler for printing incoming messages
        if msg.arbitration_id != arb_id or list(msg.data) != output_payload:
            response_directive = directive_str(msg.arbitration_id, msg.data)
            print("  Received {0}".format(response_directive))

    # Initialize fuzzed nibble generator
    nibble_values = range(0xF + 1)
    fuzz_data = product(nibble_values, repeat=number_of_nibbles_to_bruteforce)

    file_logging_enabled = filename is not None
    output_file = None
    output_payload = []
    try:
        if file_logging_enabled:
            output_file = open(filename, "a")
        with CanActions(arb_id=arb_id) as can_wrap:
            if show_progress:
                print("Starting at index {0} of {1}\n".format(start_index, end_index))
            if show_responses:
                can_wrap.add_listener(response_handler)
            message_count = 0
            # Traverse all outputs from fuzz generator
            for current_fuzzed_nibbles in fuzz_data:
                # Skip handling until start_index is met
                if message_count < start_index:
                    message_count += 1
                    continue

                fuzz_index = 0
                output_payload = []

                for index in range(0, number_of_nibbles, 2):
                    if message_count < start_index:
                        continue
                    # Apply fuzzed nibbles on top of initial payload
                    if payload_bitmap[index]:
                        high_nibble = current_fuzzed_nibbles[fuzz_index]
                        fuzz_index += 1
                    else:
                        high_nibble = initial_payload[index]

                    if payload_bitmap[index + 1]:
                        low_nibble = current_fuzzed_nibbles[fuzz_index]
                        fuzz_index += 1
                    else:
                        low_nibble = initial_payload[index + 1]

                    current_byte = (high_nibble << 4) + low_nibble
                    output_payload.append(current_byte)

                can_wrap.send(output_payload)
                message_count += 1
                if show_progress:
                    # TODO - Pick a suitable output format
                    print("\rCurrent: {0} Index: {1}".format(",".join(list(map("{0:02x}".format, output_payload))),
                                                             message_count), end="")
                    stdout.flush()
                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, output_payload)
                sleep(CALLBACK_HANDLER_DURATION)
            if show_progress:
                print()
    finally:
        if output_file is not None:
            output_file.close()

# --- [6]
# Methods that handle mutation fuzzing.
# ---


def get_mutated_id(arb_id, arb_id_bitmap):
    """
    Gets a mutated arbitration id.

    :param arb_id: The original arbitration id.
    :param arb_id_bitmap: Specifies what (hex) bits need to be mutated in the arbitration id.
    :return: Returns a mutated arbitration id.
    """
    for i in range(MAX_ID_LENGTH - len(arb_id_bitmap)):
        arb_id_bitmap.append(True)

    old_arb_id = "0" * (MAX_ID_LENGTH - len(arb_id)) + arb_id
    new_arb_id = ""

    for i in range(len(arb_id_bitmap)):
        if arb_id_bitmap[i] and i == 0:
            new_arb_id += random.choice(LEAD_ID_CHARACTERS)
        elif arb_id_bitmap[i]:
            new_arb_id += random.choice(CHARACTERS)
        else:
            new_arb_id += old_arb_id[i]

    for j in range(MAX_ID_LENGTH - len(arb_id_bitmap)):
        new_arb_id += old_arb_id[len(arb_id_bitmap) + j]
    return new_arb_id


def get_mutated_payload(payload, payload_bitmap):
    """
    Gets a mutated payload.

    :param payload: The original payload.
    :param payload_bitmap: Specifies what (hex) bits need to be mutated in the payload.
    :return: Returns a mutated payload.
    """
    for i in range(MAX_PAYLOAD_LENGTH - len(payload_bitmap)):
        payload_bitmap.append(True)

    old_payload = payload + "1" * (MAX_PAYLOAD_LENGTH - len(payload))
    new_payload = ""

    for i in range(len(payload_bitmap)):
        if payload_bitmap[i]:
            new_payload += random.choice(CHARACTERS)
        else:
            new_payload += old_payload[i]

    for j in range(MAX_PAYLOAD_LENGTH - len(payload_bitmap)):
        new_payload += old_payload[len(payload_bitmap) + j]
    return new_payload


def mutate_fuzz(initial_arb_id, initial_payload, arb_id_bitmap, payload_bitmap, filename=None):
    """
    A simple mutation based fuzzer algorithm.
    Mutates (hex) bits in the given id/payload.
    The mutation bits are specified in the id/payload bitmaps.
    The mutations are random values.
    Uses CanActions to send/receive from the CAN bus.

    :param initial_arb_id: The initial arbitration id to use.
    :param initial_payload: The initial payload to use.
    :param arb_id_bitmap: Specifies what (hex) bits need to be mutated in the arbitration id.
    :param payload_bitmap: Specifies what (hex) bits need to be mutated in the payload.
    :param filename: The file where the cansend directives should be written to.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + arb_id + "#" + payload)
        print("  Received Message: " + str(msg))

    # payload_bitmap = [False, False, True, True, False, False, False, False]
    while True:
        arb_id = get_mutated_id(initial_arb_id, arb_id_bitmap)
        payload = get_mutated_payload(initial_payload, payload_bitmap)

        directive_send(arb_id, payload, response_handler)

        if filename is not None:
            write_directive_to_file(filename, arb_id, payload)


# --- [7]
# Handler methods.
# ---


def __handle_random(args):
    random_fuzz(static_arb_id=args.arb_id, static_payload=args.payload, filename=args.file,
                min_payload_length=args.minpl, max_payload_length=args.maxpl, seed=args.seed)


def __handle_linear(args):
    linear_file_fuzz(filename=args.filename)
    print("Linear fuzz finished")


def __handle_ring_bf(args):
    ring_bf_fuzz(arb_id=args.arb_id, initial_payload=args.payload, payload_bitmap=args.payload_bitmap,
                 filename=args.file, start_index=args.start, show_progress=True, show_responses=args.responses)
    print("Brute forcing finished")


def __handle_mutate(args):
    if args.arb_id is None:
        args.arb_id = ZERO_PAYLOAD

    if args.payload is None:
        args.payload = ZERO_PAYLOAD

    if args.id_bitmap is None:
        args.id_bitmap = [True] * (MAX_ID_LENGTH - 1)
        args.id_bitmap.insert(0, False)  # By default, don't mutate on extended can ids

    if args.payload_bitmap is None:
        args.payload_bitmap = [True] * MAX_PAYLOAD_LENGTH

    mutate_fuzz(initial_payload=args.payload, initial_arb_id=args.arb_id, arb_id_bitmap=args.id_bitmap,
                payload_bitmap=args.payload_bitmap, filename=args.file)


def __handle_replay(args):
    filename = args.filename

    fd = open(filename, "r")
    composites = []
    for directive in fd:
        directive = directive.rstrip()
        if directive:
            composite = parse_directive(directive)
            composites.append(composite)
    replay_file_fuzz(composites)


# --- [8]
# Main methods.
# ---


def parse_args(args):
    """
    Argument parser for the fuzzer module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py fuzzer",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="A fuzzer for the CAN bus",
                                     epilog="""Example usage:
./cc.py fuzzer random
./cc.py fuzzer ring_bf 244 -payload_bitmap 0000001 
-file example.txt

Supported algorithms:
random - Send random or static CAN payloads to 
      random or static arbitration ids.
linear - Use a given input file to send can packets.
replay - Use the linear algorithm but also attempt 
      to find a specific payload response.
ring_bf - Attempts to brute force a static id 
       using a ring based brute force algorithm.
mutate - Mutates (hex) bits in the given id/payload.
      The mutation bits are specified 
      in the id/payload bitmaps.""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    cmd_random = subparsers.add_parser("random")
    cmd_random.add_argument("-arb_id", default=None, help="set static arbitration ID")
    cmd_random.add_argument("-payload", default=None, help="set static payload")
    cmd_random.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_random.add_argument("-minpl", type=int, default=MIN_PL_LENGTH, help="minimum payload length")
    cmd_random.add_argument("-maxpl", type=int, default=MAX_PL_LENGTH, help="maximum payload length")
    cmd_random.add_argument("-seed", "-s", metavar="S", default=None, help="set random seed")
    cmd_random.set_defaults(func=__handle_random)

    # Linear
    cmd_linear = subparsers.add_parser("linear")
    cmd_linear.add_argument("filename", help="input directive file to replay")
    cmd_linear.set_defaults(func=__handle_linear)

    # Replay (linear with response mapping)
    cmd_replay = subparsers.add_parser("replay")
    cmd_replay.add_argument("filename", help="input directive file to replay")
    cmd_replay.set_defaults(func=__handle_replay)

    # Ring based bruteforce
    cmd_ring_bf = subparsers.add_parser("ring_bf")
    cmd_ring_bf.add_argument("arb_id", help="arbitration ID")
    cmd_ring_bf.add_argument("-payload", "-p", default=None, help="payload as hex string, e.g. 0011223344ABCDEF")
    cmd_ring_bf.add_argument("-payload_bitmap", "-pb", default=None,
                             help="bitmap as binary string, e.g. 01001101 where '1' is a nibble index to override")
    cmd_ring_bf.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_ring_bf.add_argument("-responses", "-r", action="store_true", help="print responses to stdout")
    cmd_ring_bf.add_argument("-start", "-s", type=int, default=0, help="start index (for resuming previous session)")
    cmd_ring_bf.set_defaults(func=__handle_ring_bf)

    # Mutate
    cmd_mutate = subparsers.add_parser("mutate")
    cmd_mutate.add_argument("-arb_id", default=ZERO_ARB_ID, help="")
    cmd_mutate.add_argument("-payload", default=ZERO_PAYLOAD, help="")
    cmd_mutate.add_argument("-id_bitmap", "-ib", help="force arbitration ID bitmap (binary string, e.g. 0100 where "
                                                      "'1' is a digit that can be overridden)")
    cmd_mutate.add_argument("-payload_bitmap", "-pb", help="force payload bitmap (binary string, e.g. 0100 where "
                                                           "'1' is a digit that can be overridden)")
    cmd_mutate.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_mutate.set_defaults(func=__handle_mutate)

    args = parser.parse_args(args)

    # Process specific argument logic
    # TODO Rewrite wrapper logic for custom formats

    # Parse arbitration ID as int
    if "arb_id" in args and args.arb_id is not None:
        args.arb_id = int_from_str_base(args.arb_id)

    # Parse payload as a str consisting of hexadecimal nibbles
    if "payload" in args:
        if args.payload is None:
            default_payload = DEFAULT_PAYLOAD
            args.payload = default_payload
        else:
            payload_ints = []
            for nibble_str in args.payload:
                nibble_int = int(nibble_str, 16)
                payload_ints.append(nibble_int)
            args.payload = payload_ints

    def bitmap_str_to_bool_list(bitmap_str):
        """
        Converts a bitmap str to a corresponding bool array. Example:

        bitmap_str_to_bool_list('10110') => [True, False, True, True, False]

        :param bitmap_str: Binary string
        :return: list of bool values
        """
        bool_bitmap = []
        for bit in bitmap_str:
            if bit == "0":
                bool_bitmap.append(False)
            elif bit == "1":
                bool_bitmap.append(True)
            else:
                raise ValueError("Invalid character '{0}' in bitmap '{1}' (should be '0' or '1')".format(bit,
                                                                                                         bitmap_str))
        return bool_bitmap

    if "id_bitmap" in args and args.id_bitmap is not None:
        if len(args.id_bitmap) > MAX_ID_LENGTH:
            raise ValueError
        bitmap = bitmap_str_to_bool_list(args.id_bitmap)
        args.payload_bitmap = bitmap

    if "payload_bitmap" in args and args.payload_bitmap is not None:
        pb_length = len(args.payload_bitmap)
        if pb_length > MAX_PAYLOAD_LENGTH:
            raise ValueError("Payload bitmap is too long ({0} characters, max allowed: {1})".format(pb_length,
                                                                                                    MAX_PAYLOAD_LENGTH))
        bitmap = bitmap_str_to_bool_list(args.payload_bitmap)
        args.payload_bitmap = bitmap

    return args


def module_main(arg_list):
    """
    Fuzz module main wrapper.

    :param arg_list: Module argument list passed by cc.py
    """
    try:
        # Parse arguments
        args = parse_args(arg_list)
        # Call appropriate function
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
