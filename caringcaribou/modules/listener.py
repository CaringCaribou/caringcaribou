from __future__ import print_function
from caringcaribou.utils.can_actions import CanActions
from sys import stdout
from collections import Counter
import argparse


def start_listener(falling_sort):
    """
    Counts messages per arbitration ID. Prints a list of IDs afterwards, sorted by number of hits.

    :param falling_sort: bool indicating whether results should be sorted in falling order
    """
    found_arb_ids = Counter()
    try:
        # Listen for messages
        print("Running listener (press Ctrl+C to exit)")
        with CanActions(notifier_enabled=False) as can_wrap:
            for msg in can_wrap.bus:
                if msg.arbitration_id not in found_arb_ids:
                    print("\rLast ID: 0x{0:08x} ({1} unique arbitration IDs found)".format(
                        msg.arbitration_id, len(found_arb_ids) + 1), end=" ")
                    stdout.flush()
                found_arb_ids[msg.arbitration_id] += 1
    except KeyboardInterrupt:
        # Print results
        if len(found_arb_ids) > 0:
            print("\n\nDetected arbitration IDs:")
            for (arb_id, hits) in sorted(found_arb_ids.items(),
                                         key=lambda x: x[1],
                                         reverse=falling_sort):
                print("Arb id 0x{0:08x} {1} hits".format(arb_id, hits))
        else:
            print("\nNo arbitration IDs were detected.")


def parse_args(args):
    """
    Argument parser for the listener module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="ccn.py listener",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Passive listener module for CaringCaribouNext")
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
    reverse = args.reverse
    start_listener(reverse)
