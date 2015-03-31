import can
import time


MESSAGE_DELAY = 0.1

ARBITRATION_ID_MIN = 0x0
ARBITRATION_ID_MAX = 0x7FF


def pad_data(data):
    return list(data) + [0] * ( 8 - len(data))

class CanActions():
    def __init__(self, arb_id=None):
        self.bus = can.interface.Bus()
        #self.callbacks = []
        self.notifier = can.Notifier(self.bus, listeners=[])
        self.arb_id = arb_id
        self.bruteforce_running = False

    def send(self, *data):
        if len(data) > 8:
            raise IndexError("Invalid CAN message length: {0}".format(len(data)))
        full_data = pad_data(data)
        msg = can.Message(arbitration_id=self.arb_id,
                          data=full_data, extended_id=False)
        self.bus.send(msg)

    def bruteforce_arbitration_id(self, data, callback, min_id=ARBITRATION_ID_MIN, max_id=ARBITRATION_ID_MAX):
        self.bruteforce_running = True
        for arb_id in range(min_id, max_id+1):
            self.notifier.listeners = [callback(arb_id)]
            msg = can.Message(arbitration_id=arb_id, data=pad_data(data), extended_id=False)
            self.bus.send(msg)
            time.sleep(MESSAGE_DELAY)
            if not self.bruteforce_running:
                break

    def bruteforce_stop(self):
        self.bruteforce_running = False