from __future__ import print_function
from lib import iso15765_2
import can
import can_actions
import datetime
import unittest


class MatchingMessages:
    # TODO Doesn't work - look into this, callback and send_and_get_response logic
    arbitration_id = None
    messages = []


def callback(message):
    # TODO - Move or delete
    assert isinstance(message, can.Message)
    if message.arbitration_id == MatchingMessages.arbitration_id:
        MatchingMessages.messages.append(message)


def send_and_get_response(send_data, send_arb_id, recv_arb_id, number_of_responses=1, timeout_seconds=1):
    # TODO - Move or delete
    MatchingMessages.arbitration_id = recv_arb_id
    with can_actions.CanActions(arb_id=send_arb_id) as can_wrap:
        can_wrap.send_single_message_with_callback(data=send_data, callback=callback)
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout_seconds)
        while datetime.datetime.now() < end_time and len(MatchingMessages.messages) < number_of_responses:
            pass
    result = MatchingMessages.messages
    MatchingMessages.messages = []
    return result


class IsoTpTestCase(unittest.TestCase):

    ARB_ID_REQUEST = 0x2000
    ARB_ID_RESPONSE = 0x4000

    def test_create_iso_tp(self):
        with iso15765_2.IsoTp(self.ARB_ID_REQUEST, self.ARB_ID_RESPONSE) as tp:
            self.assertTrue(isinstance(tp, iso15765_2.IsoTp), "Failed to initialize ISO-15765-2")

    # def test_send_single_frame(self):
    #    # TODO implement
    #    single_frame_data = [0x10, 0x20, 0x30, 0x40]
    #    messages = send_and_get_response(single_frame_data, 0x123, 0x456, 2)
    #    for m in messages:
    #        print(m)


if __name__ == '__main__':
    unittest.main()
