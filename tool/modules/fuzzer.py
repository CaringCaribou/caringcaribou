from __future__ import print_function
from sys import version_info, stdout
import argparse
import random

from itertools import product
from lib.can_actions import *
from time import sleep

# Python 2/3 compatibility
if version_info[0] == 2:
    range = xrange
    input = raw_input

# Number of seconds to wait between messages
CALLBACK_HANDLER_DURATION = 0.01
# Payload length limits
MIN_PL_LENGTH = 1
MAX_PL_LENGTH = 8
# Max size of random seed if no seed is provided in arguments
DEFAULT_SEED_MAX = 2 ** 16
# Number of sub-lists to split message list into per round in 'replay' mode
REPLAY_NUMBER_OF_SUB_LISTS = 5
# Default payload, split into nibbles
DEFAULT_PAYLOAD = [0x0] * 16
# Default arbitration ID, split into nibbles
DEFAULT_ARB_ID = [0x0] * 4


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
    """
    Seeds the PRNG with 'seed'. If this is None, a seed is pulled from the PRNG instead.

    :param seed: int to use for seeding
    """
    if seed is None:
        seed = random.randint(0, DEFAULT_SEED_MAX)
    else:
        seed = int_from_str_base(seed)
    print("Seed: {0} (0x{0:x})".format(seed))
    random.seed(seed)


def hex_str_to_nibble_list(data):
    """
    Converts a hexadecimal str values into a list of int nibbles.

    Example:
    hex_str_to_nibble_list("12ABF7")
    gives
    [0x1, 0x2, 0xA, 0xB, 0xF, 0x7]

    :param data: str of hexadecimal values
    :return: list of int nibbles
    """
    if data is None:
        return None
    data_ints = []
    for nibble_str in data:
        nibble_int = int(nibble_str, 16)
        data_ints.append(nibble_int)
    return data_ints


def bitmap_str_to_bool_list(bitmap_str):
    """
    Converts a bitmap str to a corresponding bool array.

    Example:
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
            raise ValueError("Invalid character '{0}' in bitmap '{1}' (should be '0' or '1')".format(
                bit, bitmap_str))
    return bool_bitmap


def payload_to_str(payload):
    """
    Returns a str representation of 'payload'

    Example:
    payload_to_str([0x12, 0xFC, 0xA7]
    gives
    "12 fc a7"

    :param payload: list of int byte values
    :return: str representing payload
    """
    return " ".join(list(map("{0:02x}".format, payload)))


def parse_directive(directive):
    """
    Parses a cansend directive

    :param directive: str representing a cansend directive
    :return: tuple (int arbitration_id, [int data_byte])
    """
    segments = directive.split("#")
    arb_id = int(segments[0], 16)
    data_str = segments[1]
    data = [int(data_str[i:i + 2], 16) for i in range(0, len(data_str), 2)]
    return arb_id, data


def apply_fuzzed_data(initial_data, fuzzed_nibbles, bitmap):
    """
    Applies 'fuzzed_nibbles' on top of 'initial_data', for all indices where 'bitmap' is True.
    Returns result as a list of bytes.

    Example:
    apply_fuzzed_data([0x2, 0x4, 0xA, 0xB], [0x5, 0xF], [False, True, True, False])
    gives the following result:
    [0x25, 0xFB]

    :param initial_data: list of initial data nibbles
    :param fuzzed_nibbles: list of nibbles to apply
    :param bitmap: list of bool values, indicating where to apply fuzzed nibbles
    :return: list of bytes
    """
    fuzz_index = 0
    result_bytes = []
    for index in range(0, len(bitmap), 2):
        # Apply fuzzed nibbles on top of initial payload
        if bitmap[index]:
            high_nibble = fuzzed_nibbles[fuzz_index]
            fuzz_index += 1
        else:
            high_nibble = initial_data[index]

        if bitmap[index + 1]:
            low_nibble = fuzzed_nibbles[fuzz_index]
            fuzz_index += 1
        else:
            low_nibble = initial_data[index + 1]

        current_byte = (high_nibble << 4) + low_nibble
        result_bytes.append(current_byte)
    return result_bytes


def nibbles_to_bytes(nibbles):
    """
    Converts a list of nibbles into a list of corresponding bytes.

    Example:
    nibbles_to_bytes([0x2, 0x1, 0xF, 0xA, 0x3, 0xC])
    gives
    [0x21, 0xFA, 0x3C]

    :param nibbles: list of nibble values
    :return: list of int values (bytes)
    """
    result_bytes = []
    for index in range(0, len(nibbles), 2):
        high_nibble = nibbles[index]
        low_nibble = nibbles[index + 1]
        current_byte = (high_nibble << 4) + low_nibble
        result_bytes.append(current_byte)
    return result_bytes


def split_lists(full_list, pieces):
    """
    Generator function which splits 'full_list' into smaller sub-lists

    :param full_list: list to split
    :param pieces: number of sub-lists to produce
    :return: yields one sub-list at a time
    """
    length = len(full_list)
    for i in range(pieces):
        sub_list = full_list[i * length // pieces: (i + 1) * length // pieces]
        if len(sub_list) == 0:
            # Skip empty sub-lists (e.g. if a list of 2 elements is split into 3 parts, one will be empty)
            continue
        yield sub_list


def get_random_arbitration_id(min_id, max_id):
    """
    Returns a random arbitration ID in the range min_id <= arb_id <= max_id

    :param min_id: int minimum allowed arbitration ID (inclusive)
    :param max_id: int maximum allowed arbitration ID (inclusive)
    :return: int arbitration ID
    """
    arb_id = random.randint(min_id, max_id)
    return arb_id


def get_random_payload_data(min_length, max_length):
    """
    Generates a random payload, whose length lies in the interval 'min_length' to 'max_length'

    :param min_length: int minimum length
    :param max_length: int maximum length
    :return: list of randomized bytes
    """
    # Decide number of bytes to generate
    payload_length = random.randint(min_length, max_length)
    # Generate random bytes
    payload = []
    for i in range(payload_length):
        data_byte = random.randint(BYTE_MIN, BYTE_MAX)
        payload.append(data_byte)
    return payload


def random_fuzz(static_arb_id, static_payload, filename=None, min_id=ARBITRATION_ID_MIN, max_id=ARBITRATION_ID_MAX,
                min_payload_length=MIN_PL_LENGTH, max_payload_length=MAX_PL_LENGTH, show_status=True, seed=None):
    """
    A simple random fuzzer algorithm, which sends random or static CAN payloads to random or static arbitration IDs

    :param static_arb_id: force usage of given arbitration ID
    :param static_payload: force usage of given payload
    :param filename: file to write cansend directives to
    :param min_id: minimum allowed arbitration ID
    :param max_id: maximum allowed arbitration ID
    :param min_payload_length: minimum allowed payload length
    :param max_payload_length: maximum allowed payload length
    :param show_status: bool indicating whether current message and counter should be printed to stdout
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
            message_count = 0
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

                if show_status:
                    print("\rMessages sent: {0}".format(message_count), end="")
                    stdout.flush()

                # Send message
                can_wrap.send(data=payload, arb_id=arb_id)
                message_count += 1

                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, payload)
                sleep(CALLBACK_HANDLER_DURATION)
    finally:
        if output_file is not None:
            output_file.close()


def replay_file_fuzz(filename):
    """
    Replay cansend directives from 'filename'

    :param filename: str source file to read cansend directives from
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
    print("Replay finished")


def identify_fuzz(all_composites):
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
            gen = split_lists(all_composites, 1)
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
                            gen = split_lists(composites, REPLAY_NUMBER_OF_SUB_LISTS)
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


def bruteforce_fuzz(arb_id, initial_payload, payload_bitmap, filename=None, start_index=0,
                    show_progress=True, show_responses=True):
    """
    Performs a brute force of selected nibbles of a payload for a given arbitration ID.
    Nibble selection is controlled by bool list 'payload_bitmap'.

    Example:
    bruteforce_fuzz(0x123, [0x1, 0x2, 0xA, 0xB], [True, False, False, True])
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
                # Apply fuzzed data to payload
                output_payload = apply_fuzzed_data(initial_payload, current_fuzzed_nibbles, payload_bitmap)
                # Send payload
                can_wrap.send(output_payload)
                message_count += 1
                if show_progress:
                    print("\rCurrent: {0} Index: {1}".format(payload_to_str(output_payload), message_count), end="")
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
    if show_progress:
        print("Brute force finished")


def pad_to_even_length(original_list, padding=0x0):
    """
    Prepends 'padding' to 'original_list' if its length is uneven.

    Examples:
    pad_to_even_length([1, 2, 3]) gives [0, 1, 2, 3]
    pad_to_even_length([1, 2]) gives [1, 2]

    :param original_list: list of elements
    :param padding: element to prepend
    :return: list of even length
    """
    if len(original_list) % 2 == 1:
        original_list.insert(0, padding)
    return original_list


def mutate_fuzz(initial_arb_id, initial_payload, arb_id_bitmap, payload_bitmap, filename=None, show_status=True,
                show_responses=False, seed=None):
    """
    Performs mutation based fuzzing of selected nibbles of a given arbitration ID and payload.
    Nibble selection is controlled by bool lists 'arb_id_bitmap' and 'payload_bitmap'.

    :param initial_arb_id: list of nibbles (ints in interval 0x0-0xF, inclusive)
    :param initial_payload: list of nibbles (ints in interval 0x0-0xF, inclusive)
    :param arb_id_bitmap: list of bool values, representing which nibbles of 'initial_arb_id' to bruteforce
    :param payload_bitmap: list of bool values, representing which nibbles of 'initial_payload' to bruteforce
    :param filename: file to write cansend directives to
    :param show_status: bool indicating whether current message and counter should be printed to stdout
    :param show_responses: bool indicating whether responses should be printed to stdout
    :param seed: use given seed instead of random seed
    """
    # Seed handling
    set_seed(seed)

    # Apply padding if needed
    initial_arb_id = pad_to_even_length(initial_arb_id)
    initial_payload = pad_to_even_length(initial_payload)
    arb_id_bitmap = pad_to_even_length(arb_id_bitmap)
    payload_bitmap = pad_to_even_length(payload_bitmap)

    def response_handler(msg):
        # Callback handler for printing incoming messages
        if msg.arbitration_id != arb_id or list(msg.data) != payload:
            response_directive = directive_str(msg.arbitration_id, msg.data)
            print("  Received {0}".format(response_directive))

    number_of_nibbles_to_fuzz_arb_id = sum(arb_id_bitmap)
    number_of_nibbles_to_fuzz_payload = sum(payload_bitmap)

    file_logging_enabled = filename is not None
    output_file = None
    arb_id = int_from_byte_list(nibbles_to_bytes(initial_arb_id))
    payload = nibbles_to_bytes(initial_payload)

    try:
        if file_logging_enabled:
            output_file = open(filename, "a")
        with CanActions(arb_id=arb_id) as can_wrap:
            if show_responses:
                can_wrap.add_listener(response_handler)
            message_count = 0
            while True:
                if number_of_nibbles_to_fuzz_arb_id > 0:
                    # Mutate arbitration ID
                    fuzzed_nibbles_arb_id = [random.randint(0, 0xF) for _ in range(number_of_nibbles_to_fuzz_arb_id)]
                    arb_id_bytes = apply_fuzzed_data(initial_arb_id, fuzzed_nibbles_arb_id, arb_id_bitmap)
                    arb_id = int_from_byte_list(arb_id_bytes)

                if number_of_nibbles_to_fuzz_payload > 0:
                    # Mutate payload
                    fuzzed_nibbles_payload = [random.randint(0, 0xF) for _ in range(number_of_nibbles_to_fuzz_payload)]
                    payload = apply_fuzzed_data(initial_payload, fuzzed_nibbles_payload, payload_bitmap)

                if show_status:
                    print("\rSending {0:04x} # {1} ({2})".format(arb_id, payload_to_str(payload), message_count),
                          end="")
                    stdout.flush()

                can_wrap.send(payload, arb_id)
                message_count += 1

                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, payload)
                sleep(CALLBACK_HANDLER_DURATION)
    except KeyboardInterrupt:
        if show_status:
            print()
    finally:
        if output_file is not None:
            output_file.close()


def __handle_random(args):
    random_fuzz(static_arb_id=args.arb_id, static_payload=args.payload, filename=args.file,
                min_payload_length=args.minpl, max_payload_length=args.maxpl, seed=args.seed)


def __handle_replay(args):
    replay_file_fuzz(filename=args.filename)


def __handle_bruteforce(args):
    arb_id = int_from_str_base(args.arb_id)
    payload = hex_str_to_nibble_list(args.payload) or DEFAULT_PAYLOAD

    if args.payload_bitmap is None:
        payload_bitmap = [True] * len(payload)
    elif len(args.payload_bitmap) != len(payload):
        raise ValueError("payload_bitmap must have same length as payload")
    else:
        payload_bitmap = bitmap_str_to_bool_list(args.payload_bitmap)

    bruteforce_fuzz(arb_id=arb_id, initial_payload=payload, payload_bitmap=payload_bitmap, filename=args.file,
                    start_index=args.start, show_progress=True, show_responses=args.responses)


def __handle_mutate(args):
    arb_id = hex_str_to_nibble_list(args.arb_id) or DEFAULT_ARB_ID
    payload = hex_str_to_nibble_list(args.payload) or DEFAULT_PAYLOAD

    if args.id_bitmap is None:
        id_bitmap = [True] * len(arb_id)
    elif len(args.id_bitmap) != len(arb_id):
        raise ValueError("id_bitmap must have same length as arbitration ID")
    else:
        id_bitmap = bitmap_str_to_bool_list(args.id_bitmap)

    if args.payload_bitmap is None:
        payload_bitmap = [True] * len(payload)
    elif len(args.payload_bitmap) != len(payload):
        raise ValueError("payload_bitmap must have same length as payload")
    else:
        payload_bitmap = bitmap_str_to_bool_list(args.payload_bitmap)

    mutate_fuzz(initial_arb_id=arb_id, initial_payload=payload, arb_id_bitmap=id_bitmap,
                payload_bitmap=payload_bitmap, filename=args.file, show_responses=args.responses, seed=args.seed)


def __handle_identify(args):
    filename = args.filename

    fd = open(filename, "r")
    composites = []
    for directive in fd:
        directive = directive.rstrip()
        if directive:
            composite = parse_directive(directive)
            composites.append(composite)
    identify_fuzz(composites)


def parse_args(args):
    """
    Argument parser for the fuzzer module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py fuzzer",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Fuzzing module for CaringCaribou",
                                     epilog="""Example usage:

./cc.py fuzzer random
./cc.py fuzzer random -f log.txt
./cc.py fuzzer replay log.txt
./cc.py fuzzer identify log.txt
./cc.py fuzzer brute -p 12345678 -pb 00001100 0x123
./cc.py fuzzer mutate -p 1234abcd -pb 00001100 -i 7fff -ib 0111""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    cmd_random = subparsers.add_parser("random", help="Random fuzzer for messages and arbitration IDs")
    cmd_random.add_argument("-arb_id", default=None, help="set static arbitration ID")
    cmd_random.add_argument("-payload", default=None, help="set static payload")
    cmd_random.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_random.add_argument("-minpl", type=int, default=MIN_PL_LENGTH, help="minimum payload length")
    cmd_random.add_argument("-maxpl", type=int, default=MAX_PL_LENGTH, help="maximum payload length")
    cmd_random.add_argument("-seed", "-s", metavar="S", default=None, help="set random seed")
    cmd_random.set_defaults(func=__handle_random)

    # Linear
    cmd_linear = subparsers.add_parser("replay", help="Replay a previously recorded directive file")
    cmd_linear.add_argument("filename", help="input directive file to replay")
    cmd_linear.set_defaults(func=__handle_replay)

    # Replay (linear with response mapping)
    cmd_replay = subparsers.add_parser("identify", help="Replay and identify message causing a specific event")
    cmd_replay.add_argument("filename", help="input directive file to replay")
    cmd_replay.set_defaults(func=__handle_identify)

    # Ring based bruteforce
    cmd_brute = subparsers.add_parser("brute", help="Brute force selected nibbles in a message")
    cmd_brute.add_argument("arb_id", help="arbitration ID")
    cmd_brute.add_argument("-payload", "-p", default=None, help="payload as hex string, e.g. 0011223344ABCDEF")
    cmd_brute.add_argument("-payload_bitmap", "-pb", default=None,
                           help="bitmap as binary string, e.g. 01001101 where '1' is a nibble index to override")
    cmd_brute.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_brute.add_argument("-responses", "-r", action="store_true", help="print responses to stdout")
    cmd_brute.add_argument("-start", "-s", type=int, default=0, help="start index (for resuming previous session)")
    cmd_brute.set_defaults(func=__handle_bruteforce)

    # Mutate
    cmd_mutate = subparsers.add_parser("mutate", help="Mutate selected nibbles in arbitration ID and message")
    cmd_mutate.add_argument("-arb_id", "-i", metavar="ID", default=None, help="initial arbitration ID")
    cmd_mutate.add_argument("-id_bitmap", "-ib", metavar="BM", help="arbitration ID bitmap as binary string")
    cmd_mutate.add_argument("-payload", "-p", metavar="P", default=None,
                            help="initial payload as hex string, e.g. 0011223344ABCDEF")
    cmd_mutate.add_argument("-payload_bitmap", "-pb", metavar="PB", help="payload bitmap as binary string")
    cmd_mutate.add_argument("-responses", "-r", action="store_true", help="print responses to stdout")
    cmd_mutate.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_mutate.add_argument("-seed", "-s", metavar="S", default=None, help="set random seed")
    cmd_mutate.set_defaults(func=__handle_mutate)

    args = parser.parse_args(args)
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
