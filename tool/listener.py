from can_actions import *
from sys import stdout
from collections import Counter


found_arb_ids = Counter()

def message_handler(msg):
    """
    Message handler which counts hits against all arbitration IDs

    :param msg: Can message
    :return:
    """
    if msg.arbitration_id not in found_arb_ids:
        print("New ID: 0x{0:03x}".format(msg.arbitration_id))
    found_arb_ids[msg.arbitration_id] += 1

def start_listener(handler):
    """
    Adds a CAN message handler which should add found data to found_arb_ids.
    Prints all of these afterwards, together with the number of hits.

    :param handler: Message handler function
    :return:
    """
    can_wrap = CanActions()
    can_wrap.add_listener(handler)
    try:
        while True:
            pass
    finally:
        can_wrap.clear_listeners()
        print("")
        for (arb_id, hits) in found_arb_ids.items():
            print("Arb id 0x{0:03x} {1} hits".format(arb_id, hits))
    time.sleep(0.2)


if __name__ == "__main__":
    try:
        start_listener(message_handler)
    except KeyboardInterrupt:
        pass
        #print("Interrupted")