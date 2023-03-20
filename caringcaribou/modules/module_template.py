'''
module_template.py

This file contains a template for a simple CaringCaribou module.
The module's entry point is the 'module_main' function.

Steps to add this module to CaringCaribou and run it:

1. Copy this template into the `caringcaribou/modules` directory:

    $ cp module_template.py my_module.py

2. In `setup.py`, add an entry under `caringcaribou.modules`, 
   referencing your new module like:
   `my_module = caringcaribou.modules.my_module`  

3. Run: `setup.py install`

4. Verify that the module is available,
   it should be listed in the output of `cc.py -h`

5. Run the following command to run module and show usage instructions:

    $ cc.py my_module -h
'''
from __future__ import print_function
import argparse
import time
from caringcaribou.utils.can_actions import CanActions
from caringcaribou.utils.common import list_to_hex_str, parse_int_dec_or_hex


def do_stuff(my_arbitration_id):
    """
    Performs some example operations, such as sending and receiving CAN messages.

    :param my_arbitration_id: The default arbitration id to use when sending messages
    :type my_arbitration_id: int
    """
    # The notifier should only be enabled when handling incoming traffic using callbacks
    use_notifier = False
    # Setup CanActions wrapper to use for receiving and sending messages
    with CanActions(arb_id=my_arbitration_id, notifier_enabled=use_notifier) as can_wrap:
        # Define message contents
        my_message = [0x11, 0x22, 0x33, 0x44]
        # Send message using the default arbitration ID for can_wrap
        can_wrap.send(data=my_message)

        # Send the same message again, but on a custom arbitration ID this time
        my_custom_arbitration_id = 0x123ABC
        can_wrap.send(data=my_message, arb_id=my_custom_arbitration_id)

        # Listen for incoming traffic for a while
        duration_seconds = 1.0
        start_time = time.time()
        end_time = start_time + duration_seconds
        while time.time() < end_time:
            # Check if a message is available
            msg = can_wrap.bus.recv(0)
            if msg is None:
                # No message was available right now - continue listening loop
                continue
            # If we reach here, a message was received. Let's print it!
            print("Received a message on channel", msg.channel)
            print("  Arb ID: 0x{0:x} ({0})".format(msg.arbitration_id))
            data_string = list_to_hex_str(msg.data, ".")
            print("  Data:  ", data_string)
            # Module logic for message handling goes here
            if msg.arbitration_id < 0x10:
                print("  That was a low arbitration ID!")

    # When we reach here, can_wrap has been closed
    print("\nDone!")


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
  cc.py module_template
  cc.py module_template -id 123
  cc.py module_template -id 0x1FF""")
    parser.add_argument("-id", type=parse_int_dec_or_hex,
                        default=0, help="arbitration ID to use")
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
        # Parse arbitration ID from the arguments
        arbitration_id = args.id
        # Time to actually do stuff
        do_stuff(arbitration_id)
    except KeyboardInterrupt:
        print("\n\nTerminated by user")
