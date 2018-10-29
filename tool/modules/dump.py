from __future__ import print_function
from lib.can_actions import DEFAULT_INTERFACE, int_from_str_base, msg_to_candump_format
from modules.send import FILE_LINE_COMMENT_PREFIX
from sys import argv, stdout
import argparse
import can
import datetime


def initiate_dump(handler, whitelist, separator_seconds, candump_format):
    """
    Runs the 'handler' function on all incoming CAN messages.

    Filtering is controlled by the list 'args.whitelist'
    A separator is printed between messages if no messages have been handled in float 'args.separator_seconds'

    :param handler: function to call on all incoming messages
    :param whitelist: list of allowed arbitration IDs, or None to allow all
    :param separator_seconds: float seconds before printing a separator between messages, or None to never do this
    :param candump_format: bool indicating whether messages should be passed to 'handler' in candump str format
    """

    if candump_format:
        format_func = msg_to_candump_format
    else:
        format_func = str
    separator_enabled = separator_seconds is not None
    last_message_timestamp = datetime.datetime.min
    last_message_separator_printed = True

    print("Dumping CAN traffic (press Ctrl+C to exit)".format(whitelist))
    with can.Bus(DEFAULT_INTERFACE, "socketcan") as bus:
        for msg in bus:
            # Separator handling
            if separator_enabled and not last_message_separator_printed:
                if (datetime.datetime.now() - last_message_timestamp).total_seconds() > separator_seconds:
                    # Print separator
                    handler("---")
                    last_message_separator_printed = True
            # Message handling
            if len(whitelist) == 0 or msg.arbitration_id in whitelist:
                handler(format_func(msg))
                last_message_timestamp = datetime.datetime.now()
                last_message_separator_printed = False


def parse_args(args):
    """
    Argument parser for the dump module.

    :param args: List of arguments
    :return: Argument namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py dump",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="CAN traffic dump module for CaringCaribou",
                                     epilog="""Example usage:
  cc.py dump
  cc.py dump -f output.txt
  cc.py dump -c -f output.txt 0x733 0x734""")
    parser.add_argument("-f", "--file",
                        metavar="F",
                        help="Write output to file F (default: stdout)")
    parser.add_argument("whitelist",
                        metavar="W",
                        nargs="*",
                        help="Arbitration ID to whitelist")
    parser.add_argument("-c",
                        action="store_true",
                        dest="candump_format",
                        help="Output on candump format")
    parser.add_argument("-s",
                        type=float,
                        metavar="SEC",
                        dest="separator_seconds",
                        help="Print separating line after SEC silent seconds")
    args = parser.parse_args(args)
    return args


def file_header():
    """
    Returns an output file header string, consisting of a number of comment lines.

    :return: str header
    """
    argument_str = " ".join(argv)
    lines = ["Caring Caribou dump file",
             datetime.datetime.now(),
             argument_str]
    header = "".join(["{0} {1}\n".format(FILE_LINE_COMMENT_PREFIX, line) for line in lines])
    return header


def module_main(args):
    """
    Dump module main wrapper.

    :param args: List of module arguments
    """
    args = parse_args(args)
    whitelist = [int_from_str_base(x) for x in args.whitelist]
    separator_seconds = args.separator_seconds
    candump_format = args.candump_format

    # Print to stdout
    if args.file is None:
        initiate_dump(print, whitelist, separator_seconds, candump_format)
    # Print to file
    else:
        try:
            with open(args.file, "w") as output_file:
                global count
                count = 0

                # Write file header
                header = file_header()
                output_file.write(header)

                def write_line_to_file(line):
                    global count
                    count += 1
                    print("\rMessages printed to file: {0}".format(count), end="")
                    output_file.write("{0}\n".format(line))
                    stdout.flush()

                initiate_dump(write_line_to_file, whitelist, separator_seconds, candump_format)
        except IOError as e:
            print("IOError: {0}".format(e))
