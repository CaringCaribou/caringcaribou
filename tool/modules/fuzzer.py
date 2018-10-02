# fuzzer.py
#
# Dictionary:
#   1.  "cansend directive"
#       A string that follows the formatting of (for example): "123#FFFFFFFF".
#       This is similar to the arguments one would pass to the cansend command line tool (part of can-util).
#   2. "composite cansend directive"
#       A cansend directive split up in its id and payload: [id, payload].
from __future__ import print_function
from sys import version_info
import argparse
import random
import string

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


def write_directive_to_file_handle(file_handle, arb_id, payload):
    """
    Writes a cansend directive to a file

    :param file_handle: handle for the file to write to
    :param arb_id: arbitration ID of the cansend directive
    :param payload: payload of the cansend directive
    """
    data = "".join(["{0:02X}".format(x) for x in payload])
    file_handle.write("{0:03X}#{1}\n".format(arb_id, data))


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


def parse_directive(line):
    """
    Parses a given cansend directive.

    :param line: A given string that represent a cansend directive.
    :return: Returns a composite directive: [id, payload]
    """
    composite = list()
    pointer = line.find("#")
    composite.append(line[0: pointer])
    composite.append(line[pointer + 1: len(line) - 1])
    return composite


def directive_str(arb_id, payload):
    payload_str = "".join(["{0:02X}".format(x) for x in payload])
    directive = "{0:03X}#{1}".format(arb_id, payload_str)
    return directive


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
    Use a given input file to send can packets.
    Uses CanActions to send/receive from the CAN bus.

    :param filename: The file where the cansend directives should be read from.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + directive.rstrip())
        print("  Received Message: " + str(msg))

    fd = open(filename, "r")
    counter = 0
    for directive in fd:
        composite = parse_directive(directive)
        arb_id = composite[0]
        payload = composite[1]

        directive_send(arb_id, payload, response_handler)

        counter += 1


# --- [4]
# Methods that handle replay fuzzing.
# ---


def split_composites(old_composites):
    """
    Split the old composites in 5 equal parts.

    :param old_composites: The old composites that need to be split.
    :return: returns a list of composite lists. Where each composite list has count ~= len(old_composites) // 5.
    """
    new_composites = []
    if len(old_composites) <= 5:
        for composite in old_composites:
            new_composites.append([composite])
        return new_composites

    pieces = 5
    count = len(old_composites) // pieces
    increments = [count] * pieces

    rest = len(old_composites) % pieces
    for i in range(rest):
        increments[i] += 1

    offset = 0
    for i in range(len(increments)):
        temp_composites = []
        for j in range(increments[i]):
            temp_composites.append(old_composites[offset + j])
        new_composites.append(temp_composites)
        offset += increments[i]

    return new_composites


def replay_file_fuzz(composites):
    """
    Use a list of arb_id and payload composites.
    Uses CanActions to send/receive from the CAN bus.
    This method will also ask for user input after each iteration of the linear algorithm.
    This allows the user to find what singular packet is causing the effect.

    :param composites: A list of arb_id and payload composites.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + arb_id + "#" + payload)
        print("  Received Message: " + str(msg))

    for composite in composites:
        arb_id = composite[0]
        payload = composite[1]

        directive_send(arb_id, payload, response_handler)

    print("Played {} payloads.".format(len(composites)))
    while True:
        print("")
        response = str(input("Was the desired effect observed?" + "\n"
                             "((y)es | (n)o | (l)ist | (r)eplay) | (q)uit: "))

        if response == "y":
            if len(composites) == 1:
                print("The potential payload is:")
                print(composites[0][0] + "#" + composites[0][1])
                raise StopIteration()

            new_composites = split_composites(composites)

            for temp in reversed(new_composites):
                replay_file_fuzz(temp)
            return

        elif response == "n":
            return

        elif response == "q":
            raise StopIteration()

        elif response == "r":
            print("Replaying the same payloads.")
            replay_file_fuzz(composites)
            return

        elif response == "l":
            for composite in composites:
                print(composite[0] + "#" + composite[1])
            print("Dumped directives currently in memory.")

        else:
            print("Invalid option, please select a valid option.")


# --- [5]
# Methods that handle brute force fuzzing.
# ---


def reverse_payload(payload):
    """
    Reverses a given payload

    :param payload: The payload to be reversed.
    :return: The reverse of the given payload
    """
    result = ""
    for i in range(len(payload) - 1, -1, -1):
        result += payload[i]
    return result


def get_masked_payload(payload_bitmap, payload, length=MAX_PAYLOAD_LENGTH):
    """
    Gets a masked payload.

    :param payload: The original payload.
    :param payload_bitmap: Bitmap that specifies what (hex) bits need to be used in the new payload. A 0 is a mask.
    :param length: The length of the payload.
    :return: Returns a new payload where all but the bits specified in the payload_bitmap are masked.
    """
    for i in range(length - len(payload_bitmap)):
        payload_bitmap.append(True)

    old_payload = payload + "1" * (length - len(payload))
    new_payload = ""

    for i in range(len(payload_bitmap)):
        if payload_bitmap[i]:
            new_payload += old_payload[i]

    return new_payload


def merge_masked_payload_with_payload(masked_payload, payload, payload_bitmap):
    """
    Merges a masked payload with a normal payload using the bitmap that masked the masked payload.

    :param payload_bitmap: Bitmap that specifies what (hex) bits need to be used in the new payload. A 0 is a mask.
    :param masked_payload: The payload that was masked using the given bitmap.
    :param payload: The normal payload.
    :return: A payload that is the result of merging the masked and normal payloads.
    """
    new_payload = ""
    counter = 0
    for i in range(len(payload)):
        if i >= len(payload_bitmap) or not payload_bitmap[i]:
            new_payload += payload[i]
        elif payload_bitmap[i]:
            new_payload += masked_payload[counter]
            counter += 1
    return new_payload


def get_next_bf_payload(last_payload):
    """
    Gets the next brute force payload.
    This method uses a ring method to get the next payload.
    For example: 0001 -> 0002 and 000F -> 0010

    :param last_payload: The last payload that was used.
    :return: Returns the next brute force payload to be used.
    """
    # Find the most inner ring.
    ring = len(last_payload) - 1
    while last_payload[ring] == "F":
        ring -= 1
        if ring < 0:
            raise OverflowError

    if ring < 0:
        return last_payload

    # Get the position of the character at the position ring in the last payload in CHARACTERS.
    i = CHARACTERS.find(last_payload[ring])
    # Construct the next payload.
    # First keep all the unchanged characters, then add the incremented character,
    # set all the remaining characters to 0.
    payload = last_payload[: ring] + CHARACTERS[(i + 1) % len(CHARACTERS)] + "0" * (len(last_payload) - 1 - ring)

    return payload


def ring_bf_fuzz(arb_id, initial_payload=ZERO_PAYLOAD, payload_bitmap=None, filename=None,
                 length=MAX_PAYLOAD_LENGTH):
    """
    A simple brute force fuzzer algorithm.
    Attempts to brute force a static id using a ring based brute force algorithm.
    Uses CanActions to send/receive from the CAN bus.

    :param arb_id: The arbitration id to use.
    :param payload_bitmap: A bitmap that specifies what bits should be brute-forced.
    :param initial_payload: The initial payload from where to start brute forcing.
    :param filename: The file where the cansend directives should be written to.
    :param length: The length of the payload.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + arb_id + "#" + send_payload)
        print("  Received Message: " + str(msg))

    # Set payload to the part of initial_payload that will be used internally.
    # The internal payload is the reverse of the relevant part of the send payload.
    # Initially, no mask must be applied.
    internal_masked_payload = reverse_payload(initial_payload[: length + 1])

    # manually send first payload
    send_payload = reverse_payload(internal_masked_payload)
    directive_send(arb_id, send_payload, response_handler)

    while internal_masked_payload != "F" * length:
        if payload_bitmap is not None:
            # Sets up a new internal masked payload out of the last send payload, then reverse it for internal use.
            internal_masked_payload = reverse_payload(get_masked_payload(payload_bitmap, send_payload, length=length))

        # Get the actual next internal masked payload. If the ring overflows, brute forcing is finished.
        try:
            internal_masked_payload = get_next_bf_payload(internal_masked_payload)
        except OverflowError:
            return

        if payload_bitmap is not None:
            # To get the new send payload, merge the reversed internal masked payload with the last send payload.
            send_payload = merge_masked_payload_with_payload(reverse_payload(internal_masked_payload),
                                                             send_payload, payload_bitmap)
        else:
            # If there is no bitmap, no merge needs to occur.
            send_payload = reverse_payload(internal_masked_payload)

        directive_send(arb_id, send_payload, response_handler)

        if filename is not None:
            write_directive_to_file(filename, arb_id, send_payload)


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
    linear_file_fuzz(filename=args.file)
    print("Linear fuzz finished.")


def __handle_ring_bf(args):
    payload = args.payload
    if payload is None:
        payload = ZERO_PAYLOAD

    ring_bf_fuzz(arb_id=args.arb_id, initial_payload=payload, payload_bitmap=args.payload_bitmap, filename=args.file)
    print("Brute forcing finished.")


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
    filename = args.file

    fd = open(filename, "r")
    composites = []
    for directive in fd:
        composite = parse_directive(directive)
        composites.append(composite)

    try:
        replay_file_fuzz(composites)
    except StopIteration:
        pass

    print("Exited replay mode.")


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
    cmd_ring_bf.add_argument("-payload", "-p", default=ZERO_PAYLOAD, help="force payload (hex string, e.g. FFFFFFFF)")
    cmd_ring_bf.add_argument("-payload_bitmap", "-pb", help="force payload bitmap (binary string, e.g. 0100 where "
                                                            "'1' is a digit that can be overridden)")
    cmd_ring_bf.add_argument("-file", "-f", default=None, help="directive file to replay")
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

    if "payload" in args and args.payload is not None and \
            (len(args.payload) % 2 != 0 or len(args.payload) > MAX_PAYLOAD_LENGTH):
        raise ValueError

    if "id_bitmap" in args and args.id_bitmap is not None:
        if len(args.id_bitmap) > MAX_ID_LENGTH:
            raise ValueError
        bitmap = [None] * len(args.id_bitmap)
        for i in range(len(args.id_bitmap)):
            bitmap[i] = string_to_bool(args.id_bitmap[i])
        args.id_bitmap = bitmap

    if "payload_bitmap" in args and args.payload_bitmap is not None:
        if len(args.payload_bitmap) > MAX_PAYLOAD_LENGTH:
            raise ValueError
        bitmap = [None] * len(args.payload_bitmap)
        for i in range(len(args.payload_bitmap)):
            bitmap[i] = string_to_bool(args.payload_bitmap[i])
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
        print("Press control + c to exit.\n")
        # Call appropriate function
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
