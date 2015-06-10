from can_actions import CanActions, int_from_str_base
from time import sleep
from sys import exit
import argparse


def parse_messages(msgs):
    """
    Parses a list of message strings and returns them in a [(arb_id, [data_byte])] format.

    :param msgs: List of message strings
    :return: List of (arb_id, [data_byte]) tuples
    """
    message_list = []
    try:
        for msg in msgs:
            msg_parts = msg.split("#", 1)
            arb_id = int_from_str_base(msg_parts[0])
            msg_data = []
            # Check data length
            byte_list = msg_parts[1].split(".")
            if not 0 < len(byte_list) <= 8:
                raise ValueError("Invalid data length: {0}".format(len(byte_list)))
            # Validate data bytes
            for byte in byte_list:
                byte_int = int(byte, 16)
                if not 0x00 <= byte_int <= 0xff:
                    raise ValueError("Invalid byte value: '{0}'".format(byte))
                msg_data.append(byte_int)
            fixed_msg = arb_id, msg_data
            message_list.append(fixed_msg)
        return message_list
    except ValueError as e:
        print("Invalid message at position {0}: '{1}'\nFailure reason: {2}".format(len(message_list), msg, e))
        exit()


def send_messages(messages, delay_between_messages):
    """
    Sends a list of messages separated by a given delay.

    :param messages: List of messages, where a message has the format (arb_id, [data_byte])
    :param delay_between_messages: Delay in seconds between each transmitted message
    """
    with CanActions() as can_wrap:
        for arb_id, message_data in messages:
            print("  Arb_id: 0x{0:03x}, data: {1}".format(arb_id, ["{0:02x}".format(a) for a in message_data]))
            can_wrap.send(message_data, arb_id)
            sleep(delay_between_messages)



def parse_args(args):
    """
    Argument parser for the send module.

    :param args: List of arguments
    :return: Argument namespace
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(prog="cc.py send",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="Raw message transmission module for CaringCaribou",
                                     epilog="""Example usage:
  cc.py send 0x7a0#c0.ff.ee.00.11.22.33.44
  cc.py send -d 0.5 123#de.ad.be.ef 124#01.23.45""")
    parser.add_argument("msg", nargs="+", help="Message on format ARB_ID#DATA where ARB_ID is interpreted "
                                               "as hex if it starts with 0x and decimal otherwise. DATA "
                                               "consists of 1-8 bytes written in hex and separated by dots.")
    parser.add_argument("--delay", "-d", metavar="D", type=float, default=0, help="Delay between messages in seconds")
    args = parser.parse_args(args)
    return args


def module_main(args):
    """
    Send module main wrapper.

    :param args: List of module arguments
    """
    args = parse_args(args)
    print("Parsing messages")
    messages = parse_messages(args.msg)
    print("Sending messages")
    send_messages(messages, args.delay)
