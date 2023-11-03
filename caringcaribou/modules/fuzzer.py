from __future__ import print_function
from sys import version_info, stdout
import argparse
import random
from itertools import product
from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import hex_str_to_nibble_list, int_from_byte_list, list_to_hex_str, parse_int_dec_or_hex
from caringcaribou.utils.constants import ARBITRATION_ID_MAX, ARBITRATION_ID_MIN, BYTE_MAX, BYTE_MIN
from time import sleep


# Python 2/3 compatibility
if version_info[0] == 2:
    range = xrange
    input = raw_input

# Number of seconds to wait between messages
DELAY_BETWEEN_MESSAGES = 0.01
# Message data length limits
MIN_DATA_LENGTH = 1
MAX_DATA_LENGTH = 8
# Max size of random seed if no seed is provided in arguments
DEFAULT_SEED_MAX = 2 ** 16
# Number of sub-lists to split message list into per round in 'replay' mode
REPLAY_NUMBER_OF_SUB_LISTS = 5


def directive_str(arb_id, data):
    """
    Converts a directive to its string representation

    :param arb_id: message arbitration ID
    :param data: message data bytes
    :return: str representing directive
    """
    data = list_to_hex_str(data, "")
    directive = "{0:03X}#{1}".format(arb_id, data)
    return directive


def write_directive_to_file_handle(file_handle, arb_id, data):
    """
    Writes a cansend directive to a file

    :param file_handle: handle for the output file
    :param arb_id: int arbitration ID
    :param data: list of data bytes
    """
    directive = directive_str(arb_id, data)
    file_handle.write("{0}\n".format(directive))


def set_seed(seed=None):
    """
    Seeds the PRNG with 'seed'. If this is None, a seed is pulled from the PRNG instead.

    :param seed: int to use for seeding
    """
    if seed is None:
        seed = random.randint(0, DEFAULT_SEED_MAX)
    print("Seed: {0} (0x{0:x})".format(seed))
    random.seed(seed)


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
        # Apply fuzzed nibbles on top of initial data
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


def get_random_data(min_length, max_length):
    """
    Generates a list of random data bytes, whose length lies in the interval 'min_length' to 'max_length'

    :param min_length: int minimum length
    :param max_length: int maximum length
    :return: list of randomized bytes
    """
    # Decide number of bytes to generate
    data_length = random.randint(min_length, max_length)
    # Generate random bytes
    data = []
    for i in range(data_length):
        data_byte = random.randint(BYTE_MIN, BYTE_MAX)
        data.append(data_byte)
    return data


def parse_directives_from_file(filename):
    """
    Parses 'filename' and returns a list of all directives contained within

    :param filename: str file to parse
    :return: list of str directives
    """
    print("Parsing messages from {0}".format(filename))
    line_number = 0
    with open(filename, "r") as fd:
        directives = []
        for directive in fd:
            line_number += 1
            directive = directive.rstrip()
            if directive:
                try:
                    composite = parse_directive(directive)
                    directives.append(composite)
                except ValueError:
                    print("  Error: Could not parse message on line {0}: {1}".format(line_number, directive))
    print("  {0} messages parsed".format(len(directives)))
    return directives


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


def random_fuzz(static_arb_id=None, static_data=None, filename=None, min_id=ARBITRATION_ID_MIN,
                max_id=ARBITRATION_ID_MAX, min_data_length=MIN_DATA_LENGTH, max_data_length=MAX_DATA_LENGTH,
                start_index=0, show_status=True, seed=None):
    """
    A simple random fuzzer algorithm, which sends random or static data to random or static arbitration IDs

    :param static_arb_id: int representing static arbitration ID
    :param static_data: list of bytes representing static data
    :param filename: file to write cansend directives to
    :param min_id: minimum allowed arbitration ID
    :param max_id: maximum allowed arbitration ID
    :param min_data_length: minimum allowed data length
    :param max_data_length: maximum allowed data length
    :param start_index: int index to start at (can be used to resume interrupted session)
    :param show_status: bool indicating whether current message and counter should be printed to stdout
    :param seed: use given seed instead of random seed
    """
    # Sanity checks
    if static_arb_id is not None and static_data is not None:
        raise ValueError("Both static arbitration ID and static data cannot be set at the same time")
    if not 0 <= min_id < max_id <= ARBITRATION_ID_MAX:
        raise ValueError("Invalid value for min_id and/or max_id")
    if not MIN_DATA_LENGTH <= min_data_length <= max_data_length <= MAX_DATA_LENGTH:
        raise ValueError("Invalid value for min_data_length ({0}) and/or max_data_length ({1})".format(
            min_data_length, max_data_length))
    if static_data is not None and len(static_data) > MAX_DATA_LENGTH:
        raise ValueError("static_data ({0} bytes) must not be more than {1} bytes long".format(
            len(static_data), MAX_DATA_LENGTH))
    if not 0 <= start_index:
        raise ValueError("Invalid start index '{0}', must be 0 or larger".format(start_index))

    # Seed handling
    set_seed(seed)

    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        if msg.arbitration_id != arb_id or list(msg.data) != data:
            directive = directive_str(arb_id, data)
            print("\rDirective: {0} (index {1})".format(directive, current_index))
            print("  Received message: {0}".format(msg))

    arb_id = None
    data = None
    file_logging_enabled = filename is not None
    output_file = None
    try:
        if file_logging_enabled:
            output_file = open(filename, "a")
        with CanActions() as can_wrap:
            # Register callback handler for incoming messages
            current_index = 0
            messages_sent = 0
            can_wrap.add_listener(response_handler)
            if show_status:
                print("Starting at index {0}\n".format(start_index))
            # Fuzzing logic
            while True:
                # Set arbitration ID
                if static_arb_id is None:
                    # Use a random arbitration ID
                    arb_id = get_random_arbitration_id(min_id, max_id)
                else:
                    # Use the static arbitration ID
                    arb_id = static_arb_id

                # Set data
                if static_data is None:
                    data = get_random_data(min_data_length, max_data_length)
                else:
                    data = static_data

                # If start index is not reached yet, continue without sending and sleeping
                if current_index < start_index:
                    current_index += 1
                    continue

                if show_status:
                    print("\rMessages sent: {0}, index: {1}".format(messages_sent, current_index), end="")
                    stdout.flush()

                # Send message
                can_wrap.send(data=data, arb_id=arb_id)
                messages_sent += 1

                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, data)
                sleep(DELAY_BETWEEN_MESSAGES)
                current_index += 1
    except IOError as e:
        print("ERROR: {0}".format(e))
    finally:
        if output_file is not None:
            output_file.close()


def bruteforce_fuzz(arb_id, initial_data, data_bitmap, filename=None, start_index=0, show_progress=True,
                    show_responses=True):
    """
    Performs a brute force of selected data nibbles for a given arbitration ID.
    Nibble selection is controlled by bool list 'data_bitmap'.

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
    :param initial_data: list of nibbles (ints in interval 0x0-0xF, inclusive)
    :param data_bitmap: list of bool values, representing which nibbles of 'initial_data' to bruteforce
    :param filename: file to write cansend directives to
    :param start_index: int index to start at (can be used to resume interrupted session)
    :param show_progress: bool indicating whether progress should be printed to stdout
    :param show_responses: bool indicating whether responses should be printed to stdout
    """
    # Sanity checks
    if not 2 <= len(initial_data) <= 16:
        raise ValueError("Invalid initial data: must be between 2 and 16 nibbles")
    if not len(initial_data) % 2 == 0:
        raise ValueError("Invalid initial data: must have an even length")
    if not len(initial_data) == len(data_bitmap):
        raise ValueError("Initial data ({0}) and data bitmap ({1}) must have the same length".format(
            len(initial_data), len(data_bitmap)))

    number_of_nibbles_to_bruteforce = sum(data_bitmap)
    end_index = 16 ** number_of_nibbles_to_bruteforce

    if not 0 <= start_index <= end_index:
        raise ValueError("Invalid start index '{0}', current range is [0-{1}]".format(start_index, end_index))

    def response_handler(msg):
        # Callback handler for printing incoming messages
        if msg.arbitration_id != arb_id or list(msg.data) != output_data:
            response_directive = directive_str(msg.arbitration_id, msg.data)
            print("  Received {0}".format(response_directive))

    # Initialize fuzzed nibble generator
    nibble_values = range(0xF + 1)
    fuzz_data = product(nibble_values, repeat=number_of_nibbles_to_bruteforce)

    file_logging_enabled = filename is not None
    output_file = None
    output_data = []
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
                # Apply fuzzed data
                output_data = apply_fuzzed_data(initial_data, current_fuzzed_nibbles, data_bitmap)
                # Send message
                can_wrap.send(output_data)
                message_count += 1
                if show_progress:
                    print("\rCurrent: {0} Index: {1}".format(list_to_hex_str(output_data, " "), message_count), end="")
                    stdout.flush()
                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, output_data)
                sleep(DELAY_BETWEEN_MESSAGES)
            if show_progress:
                print()
    finally:
        if output_file is not None:
            output_file.close()
    if show_progress:
        print("Brute force finished")


def mutate_fuzz(initial_arb_id, initial_data, arb_id_bitmap, data_bitmap, filename=None, start_index=0,
                show_status=True, show_responses=False, seed=None):
    """
    Performs mutation based fuzzing of selected nibbles of a given arbitration ID and data.
    Nibble selection is controlled by bool lists 'arb_id_bitmap' and 'data_bitmap'.

    :param initial_arb_id: list of nibbles (ints in interval 0x0-0xF, inclusive)
    :param initial_data: list of nibbles (ints in interval 0x0-0xF, inclusive)
    :param arb_id_bitmap: list of bool values, representing which nibbles of 'initial_arb_id' to bruteforce
    :param data_bitmap: list of bool values, representing which nibbles of 'initial_data' to bruteforce
    :param filename: file to write cansend directives to
    :param start_index: int index to start at (can be used to resume interrupted session)
    :param show_status: bool indicating whether current message and counter should be printed to stdout
    :param show_responses: bool indicating whether responses should be printed to stdout
    :param seed: use given seed instead of random seed
    """
    # Sanity checks
    if not 0 <= start_index:
        raise ValueError("Invalid start index '{0}', must be 0 or larger".format(start_index))

    # Seed handling
    set_seed(seed)

    def response_handler(msg):
        # Callback handler for printing incoming messages
        if msg.arbitration_id != arb_id or list(msg.data) != data:
            response_directive = directive_str(msg.arbitration_id, msg.data)
            print("  Received {0}".format(response_directive))

    number_of_nibbles_to_fuzz_arb_id = sum(arb_id_bitmap)
    number_of_nibbles_to_fuzz_data = sum(data_bitmap)

    file_logging_enabled = filename is not None
    output_file = None

    # Set initial values - needed in case they are static
    data = None
    arb_id = None
    if number_of_nibbles_to_fuzz_data == 0:
        data = apply_fuzzed_data(initial_data, [], data_bitmap)
    if number_of_nibbles_to_fuzz_arb_id == 0:
        arb_id = int_from_byte_list(apply_fuzzed_data(initial_arb_id, [], arb_id_bitmap))

    try:
        if file_logging_enabled:
            output_file = open(filename, "a")
        with CanActions() as can_wrap:
            current_index = 0
            messages_sent = 0
            if show_responses:
                can_wrap.add_listener(response_handler)
            while True:
                if number_of_nibbles_to_fuzz_arb_id > 0:
                    # Mutate arbitration ID
                    fuzzed_nibbles_arb_id = [random.randint(0, 0xF) for _ in range(number_of_nibbles_to_fuzz_arb_id)]
                    arb_id_bytes = apply_fuzzed_data(initial_arb_id, fuzzed_nibbles_arb_id, arb_id_bitmap)
                    arb_id = int_from_byte_list(arb_id_bytes)

                if number_of_nibbles_to_fuzz_data > 0:
                    # Mutate data
                    fuzzed_nibbles_data = [random.randint(0, 0xF) for _ in range(number_of_nibbles_to_fuzz_data)]
                    data = apply_fuzzed_data(initial_data, fuzzed_nibbles_data, data_bitmap)

                if current_index < start_index:
                    current_index += 1
                    continue

                if show_status:
                    print("\rSending {0:04x} # {1} ({2} sent, index {3})".format(
                        arb_id, list_to_hex_str(data, " "), messages_sent, current_index), end="")
                    stdout.flush()

                can_wrap.send(data, arb_id)
                messages_sent += 1

                # Log to file
                if file_logging_enabled:
                    write_directive_to_file_handle(output_file, arb_id, data)
                sleep(DELAY_BETWEEN_MESSAGES)
                current_index += 1
    finally:
        if output_file is not None:
            output_file.close()


def replay_fuzz(directives, show_requests, show_responses):
    """
    Replay cansend directives from 'filename'

    :param directives: list of (int arb_id, list data) tuples
    :param show_requests: bool indicating whether requests should be printed to stdout
    :param show_responses: bool indicating whether responses should be printed to stdout
    """

    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        if msg.arbitration_id != arb_id or list(msg.data) != data:
            if not show_requests:
                # Print last sent request
                print("Sent: {0}".format(directive))
            print("  Received: {0}".format(directive_str(msg.arbitration_id, msg.data)))

    arb_id = None
    data = None
    count = 0

    with CanActions() as can_wrap:
        if show_responses:
            # Enable callback handler for incoming messages
            can_wrap.add_listener(response_handler)
        for arb_id, data in directives:
            count += 1
            directive = directive_str(arb_id, data)
            can_wrap.send(data=data, arb_id=arb_id)
            if show_requests:
                print("Sending ({0}) {1}".format(count, directive))
            sleep(DELAY_BETWEEN_MESSAGES)
    print("Replay finished")


def identify_fuzz(all_composites, show_responses):
    """
    Replays a list of composites causing an effect, prompting for input to help isolate the message causing the effect

    :param all_composites: list of composites
    :param show_responses: bool indicating whether responses should be printed to stdout
    :return: str directive if message is found,
             None otherwise
    """

    def response_handler(msg):
        if msg.arbitration_id != arb_id or list(msg.data) != data:
            response_directive = directive_str(msg.arbitration_id, msg.data)
            print("  Received {0}".format(response_directive))

    arb_id = None
    data = None
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
                if show_responses:
                    # Enable callback handler for incoming messages
                    can_wrap.add_listener(response_handler)
                # Send messages
                for index in range(len(composites)):
                    composite = composites[index]
                    arb_id = composite[0]
                    data = composite[1]
                    directive = directive_str(arb_id, data)
                    can_wrap.send(data=data, arb_id=arb_id)
                    print("Sending ({0}/{1}) {2}".format(index+1, len(composites), directive))
                    sleep(DELAY_BETWEEN_MESSAGES)
                # Disable callback handler for incoming messages
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
                        return None
                    else:
                        # Invalid choice - ask again
                        print("Invalid choice")
                        valid_response = False
        except StopIteration:
            # No more messages to try - give up
            print("\nNo match was found.")
            return None


def __handle_random(args):
    data = None
    if args.data is not None:
        data_nibbles = hex_str_to_nibble_list(args.data)
        padded_nibbles = pad_to_even_length(data_nibbles)
        data = nibbles_to_bytes(padded_nibbles)
    random_fuzz(static_arb_id=args.id, static_data=data, filename=args.file,
                min_data_length=args.min, max_data_length=args.max, start_index=args.index, seed=args.seed)


def parse_hex_and_dot_indices(values, dot_index_marker="."):
    """
    Parses a str consisting of hex nibble values and 'dot_index_marker' and returns a tuple consisting of
    a list of (int or None) values and a boolean list of dot indices.

    Example:
    parse_hex_and_dot_indices("1.34AB..")
    gives
    ([1, None, 3, 4, 0xA, 0xB, None, None], [False, True, False, False, False, False, True, True])

    :param values: str input consisting of hex and 'dot_index_marker' values
    :param dot_index_marker: str character which identifies dot indices
    :return: tuple with list of int/None values and list of int dot indices
    """
    dot_indices = []
    hex_data = []

    # Pad to even length if needed
    if len(values) % 2 == 1:
        hex_data.append(0)
        dot_indices.append(False)

    # Parse values
    for i in range(len(values)):
        nibble = values[i]

        is_dot_index = nibble == dot_index_marker
        dot_indices.append(is_dot_index)

        if is_dot_index:
            hex_nibble = None
        else:
            hex_nibble = int(nibble, 16)
        hex_data.append(hex_nibble)
    return hex_data, dot_indices


def __handle_bruteforce(args):
    data, data_bitmap = parse_hex_and_dot_indices(args.data)

    bruteforce_fuzz(arb_id=args.arb_id, initial_data=data, data_bitmap=data_bitmap, filename=args.file,
                    start_index=args.index, show_progress=True, show_responses=args.responses)


def __handle_mutate(args):
    arb_id, id_bitmap = parse_hex_and_dot_indices(args.arb_id)
    data, data_bitmap = parse_hex_and_dot_indices(args.data)

    mutate_fuzz(initial_arb_id=arb_id, initial_data=data, arb_id_bitmap=id_bitmap,
                data_bitmap=data_bitmap, filename=args.file, start_index=args.index,
                show_responses=args.responses, seed=args.seed)


def __handle_replay(args):
    filename = args.filename
    try:
        directives = parse_directives_from_file(filename)
        print("Sending messages")
        replay_fuzz(directives=directives, show_requests=args.requests, show_responses=args.responses)
    except IOError as e:
        print("ERROR: {0}".format(e))


def __handle_identify(args):
    try:
        directives = parse_directives_from_file(args.filename)
        # Call handling function
        identify_fuzz(directives, show_responses=args.responses)
    except IOError as e:
        print("IOError:", e)


def parse_args(args):
    """
    Argument parser for the fuzzer module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    global DELAY_BETWEEN_MESSAGES
    parser = argparse.ArgumentParser(prog="ccn.py fuzzer",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Fuzzing module for CaringCaribouNext",
                                     epilog="""Example usage:

./ccn.py fuzzer random
./ccn.py fuzzer random -min 4 -seed 0xabc123 -f log.txt
./ccn.py fuzzer brute 0x123 12ab..78
./ccn.py fuzzer mutate 7f.. 12ab....
./ccn.py fuzzer replay log.txt
./ccn.py fuzzer identify log.txt""")
    subparsers = parser.add_subparsers(dest="module_function")
    subparsers.required = True

    # Random fuzzer
    cmd_random = subparsers.add_parser("random", help="Random fuzzer for messages and arbitration IDs")
    cmd_random.add_argument("-id", type=parse_int_dec_or_hex, default=None, help="set static arbitration ID")
    cmd_random.add_argument("-data", "-d", default=None, help="set static data")
    cmd_random.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_random.add_argument("-min", type=int, default=MIN_DATA_LENGTH, help="minimum data length")
    cmd_random.add_argument("-max", type=int, default=MAX_DATA_LENGTH, help="maximum data length")
    cmd_random.add_argument("-index", "-i", metavar="I", type=parse_int_dec_or_hex, default=0,
                            help="start index (for resuming previous session)")
    cmd_random.add_argument("-seed", "-s", metavar="S", type=parse_int_dec_or_hex, default=None, help="set random seed")
    cmd_random.add_argument("-delay", type=float, metavar="D", default=DELAY_BETWEEN_MESSAGES,
                            help="delay between messages")
    cmd_random.set_defaults(func=__handle_random)

    # Brute force fuzzer
    cmd_brute = subparsers.add_parser("brute", help="Brute force selected nibbles in a message")
    cmd_brute.add_argument("arb_id", type=parse_int_dec_or_hex, help="arbitration ID")
    cmd_brute.add_argument("data", help="hex data where dots mark indices to bruteforce, e.g. 123.AB..")
    cmd_brute.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_brute.add_argument("-responses", "-r", action="store_true", help="print responses to stdout")
    cmd_brute.add_argument("-index", "-i", metavar="I", type=parse_int_dec_or_hex, default=0,
                           help="start index (for resuming previous session)")
    cmd_brute.add_argument("-delay", type=float, metavar="D", default=DELAY_BETWEEN_MESSAGES,
                           help="delay between messages")
    cmd_brute.set_defaults(func=__handle_bruteforce)

    # Mutate fuzzer
    cmd_mutate = subparsers.add_parser("mutate", help="Mutate selected nibbles in arbitration ID and message")
    cmd_mutate.add_argument("arb_id", help="hex arbitration ID where dots mark indices to mutate, e.g. 7f..")
    cmd_mutate.add_argument("data", help="hex data where dots mark indices to mutate, e.g. 123.AB..")
    cmd_mutate.add_argument("-responses", "-r", action="store_true", help="print responses to stdout")
    cmd_mutate.add_argument("-file", "-f", default=None, help="log file for cansend directives")
    cmd_mutate.add_argument("-seed", "-s", metavar="S", type=parse_int_dec_or_hex, default=None, help="set random seed")
    cmd_mutate.add_argument("-index", "-i", metavar="I", type=parse_int_dec_or_hex, default=0,
                            help="start index (for resuming previous session)")
    cmd_mutate.add_argument("-delay", type=float, metavar="D", default=DELAY_BETWEEN_MESSAGES,
                            help="delay between messages")
    cmd_mutate.set_defaults(func=__handle_mutate)

    # Replay
    cmd_replay = subparsers.add_parser("replay", help="Replay a previously recorded directive file")
    cmd_replay.add_argument("filename", help="input directive file to replay")
    cmd_replay.add_argument("-requests", "-req", action="store_true", help="print requests to stdout")
    cmd_replay.add_argument("-responses", "-res", action="store_true", help="print responses to stdout")
    cmd_replay.add_argument("-delay", type=float, metavar="D", default=DELAY_BETWEEN_MESSAGES,
                            help="delay between messages")
    cmd_replay.set_defaults(func=__handle_replay)

    # Identify (replay with response mapping)
    cmd_identify = subparsers.add_parser("identify", help="Replay and identify message causing a specific event")
    cmd_identify.add_argument("filename", help="input directive file to replay")
    cmd_identify.add_argument("-responses", "-res", action="store_true", help="print responses to stdout")
    cmd_identify.add_argument("-delay", type=float, metavar="D", default=DELAY_BETWEEN_MESSAGES,
                              help="delay between messages")
    cmd_identify.set_defaults(func=__handle_identify)

    args = parser.parse_args(args)
    if "delay" in args:
        DELAY_BETWEEN_MESSAGES = args.delay
    return args


def module_main(arg_list):
    """
    Fuzz module main wrapper.

    :param arg_list: Module argument list passed by ccn.py
    """
    try:
        # Parse arguments
        args = parse_args(arg_list)
        # Call appropriate function
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
