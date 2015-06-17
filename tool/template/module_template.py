from can_actions import CanActions
from time import sleep
import argparse


def foo(arb_id):
    """
    Stub function that sends a single message on the can bus and prints incoming traffic for 3 seconds

    :param arb_id: The arbitration id to send a message on
    """

    # Define a callback function which will handle incoming messages
    def example_response_handler(msg):
        print("Incoming message!")
        print(msg)
        # Examples of how to filter data
        if msg.data[0] > 0x0F:
            print("First byte is not very small ({0})".format(msg.data[0]))
        if msg.arbitration_id < 0x10:
            print("Low arbitration ID on this one ({0})".format(msg.arbitration_id))
        print("---")

    print("Setting up")
    # Create an instance of CanActions, which we can use to send and receive messages.
    # In this example we set the arbitration ID for outgoing messages directly in the constructor.
    with CanActions(arb_id) as can_wrap:
        print("Sending message")
        # Define some message contents
        message = [0x11, 0x22, 0x33, 0x44]
        # Send the message on the CAN bus and register a callback handler for incoming messages
        can_wrap.send_single_message_with_callback(message, example_response_handler)
        # Wait for three seconds before closing the CanActions instance. This means we have three
        # seconds to handle incoming messages through the callback function.
        sleep(3)
    print("Done!")


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

    :param arg_list: Module argument list passed from cc.py
    """
    try:
        args = parse_args(arg_list)
        foo(args.arbId)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
