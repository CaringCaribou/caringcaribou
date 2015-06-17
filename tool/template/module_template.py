from can_actions import CanActions
import argparse
from time import sleep


def foo(arbId):
    """
    Stub function that sends a single message on the can bus and attempts to wait for a response

    :param arbId: The arbitration id to send a message on
    """
    def responseHandler(msg):
        print("Got some response")
        print(msg.data)

    with CanActions(arbId) as can_wrap:
        message = [0x11,0x22,0x33,0x44]
        can_wrap.send_single_message_with_callback(message, responseHandler)
        sleep(3)


def parse_args(args):
    """
    Argument parser for the template module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py module_template",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Descriptive message for the template module",
                                     epilog="""Example usage:
  cc.py module_template -arbId 1""")

    parser.add_argument("-arbId", type=int, default=0)

    args = parser.parse_args(args)
    return args

def module_main(arg_list):
    """
    Module main wrapper.

    :param arg_list: Module argument list
    """
    try:
        args = parse_args(arg_list)
        foo(args.arbId)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
