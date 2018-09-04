from __future__ import print_function
from lib.can_actions import CanActions
from sys import stdout
from collections import Counter
import argparse

found_arb_ids = Counter()


def message_handler(msg):
    """
    Message handler which counts hits against all arbitration IDs

    :param msg: Can message
    """
    if msg.arbitration_id not in found_arb_ids:
        print("\rLast ID: 0x{0:03x} ({1} unique arbitration IDs found)".format(
            msg.arbitration_id, len(found_arb_ids) + 1), end="")
        stdout.flush()
    found_arb_ids[msg.arbitration_id] += 1


def start_listener(handler, args):
    """
    Adds a CAN message handler which should add found data to found_arb_ids.
    Prints all of these afterwards, sorted by the number of hits.

    :param handler: Message handler function
    :param args: Argument namespace (reversed sorting applied if args.reverse)
    """
    try:
        print("Starting listener (press Ctrl+C to exit)")
        with CanActions() as can_wrap:
            can_wrap.add_listener(handler)
            while True:
                pass
    finally:
        if len(found_arb_ids) > 0:
            print("\n\nDetected arbitration IDs:")
            for (arb_id, hits) in sorted(found_arb_ids.items(),
                                         key=lambda x: x[1],
                                         reverse=args.reverse):
                print("Arb id 0x{0:03x} {1} hits".format(arb_id, hits))
        else:
            print("No arbitration IDs were detected.")


def parse_args(args):
    """
    Argument parser for the listener module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py listener",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Passive listener module for CaringCaribou")
    parser.add_argument("-r", "--reverse",
                        action="store_true",
                        help="Reversed sorting of results")
    args = parser.parse_args(args)
    return args


def module_main(args):
    """
    Listener module main wrapper.

    :param args: List of module arguments
    """
    args = parse_args(args)
    start_listener(message_handler, args)
