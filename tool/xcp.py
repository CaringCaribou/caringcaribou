from can_actions import *


def discovery():
    can_wrap = CanActions()
    print("Starting XCP discovery")

    def response_analyser_wrapper(arb_id):
        print("Sending XCP connect to {0:03x}".format(arb_id))

        def response_analyser(msg):
            if msg.data[0] == 0xff:
                print("Found XCP at arbitration ID {0:03x}".format(arb_id))
                print(msg)
                can_wrap.bruteforce_stop()
        return response_analyser

    can_wrap.bruteforce_arbitration_id([0xff], response_analyser_wrapper, min_id=0x100, max_id=0x400)

if __name__ == "__main__":
    discovery()