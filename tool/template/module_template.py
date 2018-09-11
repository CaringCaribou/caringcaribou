# module_template.py
#
# This file contains a template for a simple CaringCaribou module.
# The module's entry point is the 'module_main' function.
#
# Steps to add this module to CaringCaribou and run it:
#
# 1. Copy this file to caringcaribou/tool/modules/
#      $ cp module_template.py ../modules/
#
# 2. Go to caringcaribou/tool
#      $ cd ..
#
# 3. Run the following command to run module and show usage instructions:
#      $ ./cc.py module_template -h
#

from can_actions import CanActions, int_from_str_base
from time import sleep
import argparse


def foo(arb_id):
    """
    Performs some example operations, such as sending and receiving CAN messages.

    :param arb_id: The arbitration id to use when sending message 1
    """

    # Define a callback function which will handle incoming messages
    def example_response_handler(msg):
        print("Callback handler: Incoming message!")
        print(msg)
        # Examples of how to filter data
        if msg.data[0] > 0x0F:
            print("First byte is not very small ({0})".format(msg.data[0]))
        if msg.arbitration_id < 0x10:
            print("Low arbitration ID on this one ({0})".format(msg.arbitration_id))
        print("---")

    print("Setting up")
    # Create an instance of CanActions, which we can use to send and receive messages.
    with CanActions(arb_id) as can_wrap:
        # EXAMPLE 1 - SEND MESSAGE WITH CALLBACK
        # Define message contents
        message1 = [0x11, 0x22, 0x33, 0x44]
        # Number of seconds for callback handler to be active
        callback_handler_duration = 3
        print("Sending message 1 and adding callback function")
        # Send the message on the CAN bus (using default arbitration ID) and register a callback
        # handler for incoming messages
        can_wrap.send_single_message_with_callback(message1, example_response_handler)
        print("Letting callback handler be active for {0} seconds".format(callback_handler_duration))
        # Wait for three seconds before closing the CanActions instance. This means we have three
        # seconds to handle incoming messages through the callback function.
        sleep(callback_handler_duration)
        # Manually remove the callback function. This is only needed since we want to proceed
        # without keeping the callback handler in the next example - otherwise it would be
        # automatically removed once can_wrap is closed.
        can_wrap.clear_listeners()
        print("Removed callback handler")

        # EXAMPLE 2 - SEND MESSAGE TO CUSTOM ARBITRATION ID
        # Define message contents
        message2 = [0x55, 0x66, 0x77, 0x88, 0x99, 0xAA]
        # Define custom arbitration ID
        my_arb_id = 0x123
        print("Sending message 2")
        # Send message on the CAN bus using the custom arbitration ID
        can_wrap.send(message2, my_arb_id)
    # When we reach here, can_wrap has been closed
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
  cc.py module_template -arbId 123
  cc.py module_template -arbId 0x1FF""")

    parser.add_argument("-arbId", default="0", help="arbitration ID to use")

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
        # Parse arbitration ID from the arguments (this function resolves both base 10 and hex values)
        arbitration_id = int_from_str_base(args.arbId)
        # Time to actually do stuff
        foo(arbitration_id)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
