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

from lib.can_actions import CanActions, int_from_str_base
from time import sleep


# Python 2/3 compatibility
if version_info[0] == 2:
    range = xrange
    input = raw_input


# --- [0]
# Static variable definitions and generic methods
# ---


# Number of seconds for callback handler to be active.
CALLBACK_HANDLER_DURATION = 0.0001
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


def directive_send(arb_id, payload, response_handler):
    """
    Sends a cansend directive.

    :param arb_id: The destination arbitration id.
    :param payload: The payload to be sent.
    :param response_handler: The callback handler that needs to be called when a response message is received.
    """
    arb_id = "0x" + arb_id
    send_msg = payload_to_str_base(payload)
    with CanActions(int_from_str_base(arb_id)) as can_wrap:
        # Send the message on the CAN bus and register a callback
        # handler for incoming messages
        can_wrap.send_single_message_with_callback(list_int_from_str_base(send_msg), response_handler)
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


# --- [2]
# Methods that handle random fuzzing.
# ---


def get_random_id(length=MAX_ID_LENGTH - 1):
    """
    Gets a random arbitration id.

    :return: A random arbitration id.
    """
    arb_id = random.choice(LEAD_ID_CHARACTERS)
    for i in range(length - 1):
        arb_id += random.choice(CHARACTERS)
    return arb_id


def get_random_payload(length=MAX_PAYLOAD_LENGTH):
    """
    Gets a random payload.

    :param: length: The length of the payload.
    :return: A random payload.
    """
    payload = ""
    for i in range(length):
        payload += random.choice(CHARACTERS)
    return payload


def random_fuzz(static_arb_id, static_payload, logging=0, filename=None, id_length=MAX_ID_LENGTH - 1,
                payload_length=MAX_PAYLOAD_LENGTH):
    """
    A simple random id fuzzer algorithm.
    Send random or static CAN payloads to random or static arbitration ids.
    Uses CanActions to send/receive from the CAN bus.

    :param logging: How many cansend directives must be kept in memory at a time.
    :param static_arb_id: Override the static id with the given id.
    :param static_payload: Override the static payload with the given payload.
    :param filename: The file where the cansend directives should be written to.
    :param id_length: The length of the id.
    :param payload_length: The length of the payload.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + arb_id + "#" + payload)
        print("  Received Message: " + str(msg))

    log = [None] * logging
    counter = 0
    while True:
        arb_id = (static_arb_id if static_arb_id is not None else get_random_id(id_length))
        payload = (static_payload if static_payload is not None else get_random_payload(payload_length))

        directive_send(arb_id, payload, response_handler)

        counter += 1
        if logging != 0:
            log[counter % logging] = arb_id + "#" + payload

        if filename is not None:
            write_directive_to_file(filename, arb_id, payload)


# --- [3]
# Methods that handle linear fuzzing.
# ---


def linear_file_fuzz(filename, logging=0):
    """
    Use a given input file to send can packets.
    Uses CanActions to send/receive from the CAN bus.

    :param filename: The file where the cansend directives should be read from.
    :param logging: How many cansend directives must be kept in memory at a time.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + directive.rstrip())
        print("  Received Message: " + str(msg))

    fd = open(filename, "r")
    log = [None] * logging
    counter = 0
    for directive in fd:
        composite = parse_directive(directive)
        arb_id = composite[0]
        payload = composite[1]

        directive_send(arb_id, payload, response_handler)

        counter += 1
        if logging != 0:
            log[counter % logging] = directive


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


def replay_file_fuzz(composites, logging=0):
    """
    Use a list of arb_id and payload composites.
    Uses CanActions to send/receive from the CAN bus.
    This method will also ask for user input after each iteration of the linear algorithm.
    This allows the user to find what singular packet is causing the effect.

    :param composites: A list of arb_id and payload composites.
    :param logging: How many cansend directives must be kept in memory at a time.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + arb_id + "#" + payload)
        print("  Received Message: " + str(msg))

    counter = 0
    log = [None] * logging

    for composite in composites:
        arb_id = composite[0]
        payload = composite[1]

        directive_send(arb_id, payload, response_handler)

        counter += 1
        if logging != 0:
            log[counter % logging] = arb_id + "#" + payload

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
                replay_file_fuzz(temp, logging)
            return

        elif response == "n":
            return

        elif response == "q":
            raise StopIteration()

        elif response == "r":
            print("Replaying the same payloads.")
            replay_file_fuzz(composites, logging)
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


def ring_bf_fuzz(arb_id, initial_payload=ZERO_PAYLOAD, payload_bitmap=None, logging=0, filename=None,
                 length=MAX_PAYLOAD_LENGTH):
    """
    A simple brute force fuzzer algorithm.
    Attempts to brute force a static id using a ring based brute force algorithm.
    Uses CanActions to send/receive from the CAN bus.

    :param arb_id: The arbitration id to use.
    :param payload_bitmap: A bitmap that specifies what bits should be brute-forced.
    :param initial_payload: The initial payload from where to start brute forcing.
    :param logging: How many cansend directives must be kept in memory at a time.
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
    log = [None] * logging
    counter = 0

    # manually send first payload
    send_payload = reverse_payload(internal_masked_payload)
    directive_send(arb_id, send_payload, response_handler)

    counter += 1
    if logging != 0:
        log[counter % logging] = arb_id + "#" + send_payload

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

        counter += 1
        if logging != 0:
            log[counter % logging] = arb_id + "#" + send_payload

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


def mutate_fuzz(initial_arb_id, initial_payload, arb_id_bitmap, payload_bitmap, logging=0, filename=None):
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
    :param logging: How many cansend directives must be kept in memory at a time.
    :param filename: The file where the cansend directives should be written to.
    """
    # Define a callback function which will handle incoming messages
    def response_handler(msg):
        print("Directive: " + arb_id + "#" + payload)
        print("  Received Message: " + str(msg))

    # payload_bitmap = [False, False, True, True, False, False, False, False]
    log = [None] * logging
    counter = 0
    while True:
        arb_id = get_mutated_id(initial_arb_id, arb_id_bitmap)
        payload = get_mutated_payload(initial_payload, payload_bitmap)

        directive_send(arb_id, payload, response_handler)

        counter += 1
        if logging != 0:
            log[counter % logging] = arb_id + "#" + payload

        if filename is not None:
            write_directive_to_file(filename, arb_id, payload)


# --- [7]
# Handler methods.
# ---


def __handle_random(args):
    random_fuzz(static_arb_id=args.id, static_payload=args.payload, logging=args.log, filename=args.file)


def __handle_linear(args):
    filename = args.file
    if filename is None:
        raise NameError

    linear_file_fuzz(filename=filename, logging=args.log)
    print("Linear fuzz finished.")


def __handle_ring_bf(args):
    payload = args.payload
    if payload is None:
        payload = ZERO_PAYLOAD

    if args.id is None:
        raise ValueError

    ring_bf_fuzz(arb_id=args.id, initial_payload=payload, payload_bitmap=args.payload_bitmap,
                 logging=args.log, filename=args.file)
    print("Brute forcing finished.")


def __handle_mutate(args):
    if args.id is None:
        args.id = ZERO_PAYLOAD

    if args.payload is None:
        args.payload = ZERO_PAYLOAD

    if args.id_bitmap is None:
        args.id_bitmap = [True] * (MAX_ID_LENGTH - 1)
        args.id_bitmap.insert(0, False)  # By default, don't mutate on extended can ids

    if args.payload_bitmap is None:
        args.payload_bitmap = [True] * MAX_PAYLOAD_LENGTH

    mutate_fuzz(initial_payload=args.payload, initial_arb_id=args.id, arb_id_bitmap=args.id_bitmap,
                payload_bitmap=args.payload_bitmap, logging=args.log, filename=args.file)


def __handle_replay(args):
    filename = args.file
    if filename is None:
        raise NameError

    fd = open(filename, "r")
    composites = []
    for directive in fd:
        composite = parse_directive(directive)
        composites.append(composite)

    try:
        replay_file_fuzz(composites, logging=args.log)
    except StopIteration:
        pass

    print("Exited replay mode.")


def handle_args(args):
    """
    Set up the environment using the passed arguments and execute the correct algorithm.

    :param args: Module argument list passed by cc.py
    """

    if args.id and len(args.id) > MAX_ID_LENGTH:
        raise ValueError
    if args.payload and (len(args.payload) % 2 != 0 or len(args.payload) > MAX_PAYLOAD_LENGTH):
        raise ValueError

    if args.id_bitmap:
        if len(args.id_bitmap) > MAX_ID_LENGTH:
            raise ValueError
        for i in range(len(args.id_bitmap)):
            args.id_bitmap[i] = string_to_bool(args.id_bitmap[i])
    if args.payload_bitmap:
        if len(args.payload_bitmap) > MAX_PAYLOAD_LENGTH:
            raise ValueError
        for i in range(len(args.payload_bitmap)):
            args.payload_bitmap[i] = string_to_bool(args.payload_bitmap[i])

    if args.alg == "random":
        __handle_random(args)
    elif args.alg == "linear":
        __handle_linear(args)
    elif args.alg == "replay":
        __handle_replay(args)
    elif args.alg == "ring_bf":
        __handle_ring_bf(args)
    elif args.alg == "mutate":
        __handle_mutate(args)
    else:
        raise ValueError


# --- [8]
# Main methods.
# ---


def parse_args(args):
    """
    Argument parser for the template module.

    Notes about values of namespace after parsing:
    Arguments that must be converted before -use static, -gen.
    Arguments that can be None: -alg, -file, -payload.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py fuzzer",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="A fuzzer for the CAN bus",
                                     epilog="""Example usage:
                                     ./cc.py fuzzer -alg random
                                     ./cc.py fuzzer -alg ring_bf -id 244 -payload_bitmap 0000001 
                                     -file example.txt
                                     """

                                            + """\nCurrently supported algorithms:
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

    parser.add_argument("-alg", type=str, help="What fuzzing algorithm to use.")
    parser.add_argument("-log", type=int, default=0,
                        help="How many cansend directives must be kept in memory at a time (default is 0)")

    parser.add_argument("-file", type=str, help="Specify a file to where the fuzzer should write"
                                                "the cansend directives it uses. "
                                                "This is required for the linear algorithm.")

    parser.add_argument("-id", type=str, help="Specify an id to use. "
                                              " Use the following syntax: 123")
    parser.add_argument("-id_bitmap", type=list, help="Override the default id bitmap with a different id bitmap. "
                                                      "Use the following syntax: 0100 "
                                                      "(with 1 a digit that can be overriden)")

    parser.add_argument("-payload", type=str, help="Specify a payload to use. "
                                                   "Use the following syntax: FFFFFFFF")
    parser.add_argument("-payload_bitmap", type=list,
                        help="Override the default payload bitmap with a different payload bitmap. "
                             "Use the following syntax: 0100 (with 1 a digit that can be overriden)")

    args = parser.parse_args(args)
    return args


def module_main(arg_list):
    """
    Module main wrapper. This is the entry point of the module when called by cc.py

    :param arg_list: Module argument list passed by cc.py
    """
    try:
        # Parse arguments
        args = parse_args(arg_list)
        print("Press control + c to exit.\n")
        handle_args(args)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
    except ValueError:
        print("Invalid syntax.")
    except NameError:
        print("Not enough arguments specified.")
    exit(0)
