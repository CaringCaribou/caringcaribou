from can_actions import *
from sys import stdout


# Dictionary of XCP error codes, mapping (code -> (error, description))
XCP_ERROR_CODES = dict([
    (0x00, ("ERR_CMD_SYNC", "Command processor synchronisation.")),
    (0x10, ("ERR_CMD_BUSY", "Command was not executed.")),
    (0x11, ("ERR_DAQ_ACTIVE", "Command rejected because DAQ is running.")),
    (0x12, ("ERR_PGM_ACTIVE", "Command rejected because PGM is running.")),
    (0x20, ("ERR_CMD_UNKNOWN", "Unknown command or not implemented optional command.")),
    (0x21, ("ERR_CMD_SYNTAX", "Command syntax invalid.")),
    (0x22, ("ERR_OUT_OF_RANGE", "Command syntax valid but command parameter(s) out of range.")),
    (0x23, ("ERR_WRITE_PROTECTED", "The memory location is write protected.")),
    (0x24, ("ERR_ACCESS_DENIED", "The memory location is not accessible.")),
    (0x25, ("ERR_ACCESS_LOCKED", "Access denied, Seed & Key is required.")),
    (0x26, ("ERR_PAGE_NOT_VALID", "Selected page not available.")),
    (0x27, ("ERR_MODE_NOT_VALID", "Selected page mode not available.")),
    (0x28, ("ERR_SEGMENT_NOT_VALID", "Selected segment not valid.")),
    (0x29, ("ERR_SEQUENCE", "Sequence error.")),
    (0x2A, ("ERR_DAQ_CONFIG", "DAQ configuration not valid.")),
    (0x30, ("ERR_MEMORY_OVERFLOW", "Memory overflow error.")),
    (0x31, ("ERR_GENERIC", "Generic error.")),
    (0x32, ("ERR_VERIFY", "The slave internal program verify routine detects an error."))
    ])


def decode_xcp_error(error_message):
    """
    Decodes an XCP error message and prints a short description.

    :param error_message: The error message
    """
    data = error_message.data
    if not data[0] == 0xfe:
        print("Not a valid error message: {0}".format(error_message))
        return
    error_lookup = XCP_ERROR_CODES.get(data[1], ("UNKNOWN", "Unknown error"))
    print("Received error message:\n{0}".format(error_message))
    print("Error code (0x{0:02x}): {1}\nDescription: {2}\n".format(data[1], error_lookup[0], error_lookup[1]))


def decode_connect_response(response_message):
    """
    Decodes an XCP connect response and prints the response information.

    :param data: The response message
    """
    print("> DECODE CONNECT RESPONSE")
    print(response_message)
    data = response_message.data
    print("-" * 20)
    print("Resource protection status\n")  # Note: sometimes referred to as RESSOURCE (sic) in specification
    resource_bits = ["CAL/PAG", "X (bit 1)", "DAQ", "STIM", "PGM", "X (bit 5)", "X (bit 6)", "X (bit 7)"]
    for i in range(8):
        print("{0:<12}{1}".format(resource_bits[i], bool(data[1] & 2**i)))
    print("-" * 20)
    print("COMM_MODE_BASIC\n")
    comm_mode_bits = ["BYTE_ORDER", "ADDRESS_GRANULARITY_0", "ADDRESS_GRANULARITY_1", "X (bit 3)",
                       "X (bit 4)", "X (bit 5)", "SLAVE_BLOCK_MODE", "OPTIONAL"]
    for i in range(8):
        print("{0:<24}{1}".format(comm_mode_bits[i], int(bool(data[2] & 2**i))))
    print("\nAddress granularity: {0} byte(s) per address".format(2 ** ((data[2] & 4) * 2 + data[2] & 2)))
    print("-" * 20)
    print("Max CTO message length: {0} bytes".format(data[3]))
    print("Max DTO message length: {0} bytes".format(data[5] * 16 + data[4]))
    print("Protocol layer version: {0}".format(data[6]))
    print("Transport layer version: {0}\n".format(data[7]))


def decode_get_comm_mode_info_response(response_message):
    """
    Decodes an XCP GET_COMM_MODE_INFO response and prints the response information.

    :param data: The response message
    """
    print("> DECODE GET COMM MODE INFO")
    print(response_message)
    data = response_message.data
    print("Reserved: 0x{0:02x}".format(data[1]))
    print("-" * 20)
    print("COMM_MODE_OPTIONAL")
    comm_mode_optional_bits = ["MASTER_BLOCK_MODE", "INTERLEAVED_MODE"] + ["X (bit {0})".format(i) for i in range(2,8)]
    for i in range(8):
        print("{0:<20}{1}".format(comm_mode_optional_bits[i], bool(data[2] & 2**i)))
    print("-" * 20)
    print("Reserved: 0x{0:02x}".format(data[3]))
    print("MAX_BS (master block mode): {0} command packets".format(data[4]))
    print("MIN_ST (minimum separation time): {0} * 100 us".format(data[5]))
    print("QUEUE_SIZE (interleaved mode): {0} command packets".format(data[6]))
    print("XCP Driver version: 0x{0:02x}\n".format(data[7]))


def decode_get_status_response(response_message):
    print("> DECODE GET STATUS")
    print(response_message)
    data = response_message.data
    print("-" * 20)
    print("CURRENT_SESSION_STATUS")
    current_session_status_bits = ["STORE_CAL_REQ", "X (bit 1)", "STORE_DAQ_REQ", "CLEAR_DAQ_REQ",
                                   "X (bit 4)", "X (bit 5)", "DAQ_RUNNING", "RESUME"]
    for i in range(8):
        print("{0:<16}{1}".format(current_session_status_bits[i], int(bool(data[1] & 2**i))))
    print("-" * 20)
    print("RESOURCE PROTECTION STATUS | Seed/key required")
    resource_protection_bits = ["CAL/PAG", "X (bit 1)", "DAQ", "STIM", "PGM", "X (bit 5)", "X (bit 6)", "X (bit 7)"]
    for i in range(8):
        print("{0:<27}| {1}".format(resource_protection_bits[i], bool(data[2] & 2**i)))
    print("-" * 20)
    print("Reserved: 0x{0:02x}".format(data[3]))
    print("Session configuration ID: {0}\n".format(2 ** ((data[5] & 4) * 2 + data[4] & 2)))



def xcp_arbitration_id_discovery():
    """
    Scans for XCP support by brute forcing XCP connect messages against different arbitration IDs.
    """
    can_wrap = CanActions()
    print("Starting XCP discovery")

    def response_analyser_wrapper(arb_id):
        print "\rSending XCP connect to {0:04x}".format(arb_id),
        stdout.flush()

        def response_analyser(msg):
            # Handle positive response
            if msg.data[0] == 0xff:
                print("\nFound XCP at arbitration ID {0:04x}!".format(arb_id))
                can_wrap.bruteforce_stop()
                decode_connect_response(msg)
            # Handle negative response
            elif msg.data[0] == 0xfe:
                print("\nFound XCP (but with a bad reply) at arbitration ID {0:03x}".format(arb_id))
                can_wrap.bruteforce_stop()
                decode_xcp_error(msg)
        return response_analyser

    can_wrap.bruteforce_arbitration_id([0xff], response_analyser_wrapper, min_id=0x300, max_id=0x400)  # FIXME values


def xcp_get_basic_information(send_arb_id, rcv_arb_id):
    def handle_description_file(msg):  # FIXME better handling - related to reply from 0xfa, 0x0*
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            can_wrap.notifier.listeners = []
            print("Desc file response:\n{0}".format(msg))
            print("".join([chr(x) for x in msg.data[1:]]))
            # TODO Handle, send next
        else:
            print("Weird get status reply: {0}\n".format(msg))

    def handle_get_id_reply(msg):  # FIXME better handling - related to reply from 0xfa, 0x0*
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            can_wrap.notifier.listeners = []
            print("GET ID response:\n{0}".format(msg))
            can_wrap.send_single_message_with_callback([0xf5, msg.data[4]], handle_description_file)
            # TODO Handle, send next
        else:
            print("Weird get status reply: {0}\n".format(msg))

    def handle_get_status_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            decode_get_status_response(msg)
            can_wrap.send_single_message_with_callback([0xfa, 0x01], handle_get_id_reply)  # FIXME: Different values (1=ASAM-MC2 filename etc)
        else:
            print("Weird get status reply: {0}\n".format(msg))

    def handle_get_comm_mode_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            decode_get_comm_mode_info_response(msg)
            can_wrap.send_single_message_with_callback([0xfd], handle_get_status_reply)
        else:
            print("Weird comm mode reply: {0}\n".format(msg))

    def handle_connect(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            can_wrap.send_single_message_with_callback([0xfb], handle_get_comm_mode_reply)
        else:
            print("Weird connect reply: {0}\n".format(msg))

    can_wrap = CanActions(arb_id=send_arb_id)
    can_wrap.send_single_message_with_callback([0xff], handle_connect)
    time.sleep(2)
    print("End of sequence")


def xcp_memory_dump(send_arb_id, rcv_arb_id, start_address=0x00, length=0xff, dump_file=None):
    global byte_counter, bytes_left, dump_complete, segment_counter, idle_timeout
    # Timeout timer
    idle_timeout = 3.0
    dump_complete = False
    # Counters for data length
    byte_counter = 0
    segment_counter = 0

    def handle_upload_reply(msg):
        global byte_counter, bytes_left, dump_complete, idle_timeout, segment_counter
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            # Reset timeout timer
            idle_timeout = 3.0
            # Calculate end index of data to handle
            end_index = min(8, bytes_left + 1)

            # print(" ".join(["{0:02x}".format(i) for i in msg.data[1:end_index]]))  # FIXME remove?
            if dump_file:
                with open(dump_file, "ab") as outfile:
                    outfile.write(bytearray(msg.data[1:end_index]))
            # Update counters
            byte_counter += 7
            bytes_left -= 7
            if bytes_left < 1:
                print "\rDumping segment {0} ({1} b, 0 b left)".format(segment_counter, length)
                print("Dump complete!")
                dump_complete = True
            elif byte_counter > 251:
                # Dump another segment
                segment_counter += 1
                # print("--- SEGMENT {0} ---".format(segment_counter))  # FIXME Remove
                # Print progress
                print "\rDumping segment {0} ({1} b, {2} b left)".format(segment_counter, ((segment_counter+1)*0xf5+byte_counter), bytes_left),
                stdout.flush()

                byte_counter = 0
                can_wrap.send_single_message_with_callback([0xf5, min(0xfc, bytes_left)], handle_upload_reply)

    def handle_set_mta_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("Set MTA acked")
            print("Dumping data:")
            # Initiate dumping
            print "\rDumping segment 0",
            can_wrap.send_single_message_with_callback([0xf5, min(0xfc, bytes_left)], handle_upload_reply)
        else:
            print("Unexpected reply: {0}\n".format(msg))

    def handle_connect_reply(msg):
        if msg.arbitration_id != rcv_arb_id:
            return
        if msg.data[0] == 0xfe:
            decode_xcp_error(msg)
            return
        if msg.data[0] == 0xff:
            print("Connected")
            can_wrap.send_single_message_with_callback([0xf6, 0x00, 0x00, 0x00, r[0], r[1], r[2], r[3]],
                                                       handle_set_mta_reply)
        else:
            print("Weird connect reply: {0}\n".format(msg))

    # Calculate address bytes (4 bytes, least significant first)
    r = []
    n = start_address
    bytes_left = length
    n &= 0xFFFFFFFF
    for i in range(4):
        r.append(n & 0xFF)
        n >>= 8
    # Make sure dump_file can be opened if specified (clearing it if it already exists)
    if dump_file:
        with open(dump_file, "w") as tmp:
            pass
    # Initialize
    can_wrap = CanActions(arb_id=send_arb_id)
    print("Attempting XCP memory dump")
    # Connect and prepare for dump
    can_wrap.send_single_message_with_callback([0xff], handle_connect_reply)
    # Idle timeout handling
    while idle_timeout > 0.0 and not dump_complete:
        time.sleep(0.5)
        idle_timeout -= 0.5
    if not dump_complete:
        print("\nERROR: Dump ended due to idle timeout")
    can_wrap.notifier.listeners = []  # TODO: Always do this before shutting down in order to prevent crashie crashie


if __name__ == "__main__":
    try:
        xcp_memory_dump(0x3e8, 0x3e9, start_address=0x1fffb000, length=0x4800, dump_file="dump_file.hex")  # Complete bootloader
        #xcp_memory_dump(0x3e8, 0x3e9, start_address=0x08000000, length=0x3F33F, dump_file="flash.hex")  # Flash
        #xcp_memory_dump(0x3e8, 0x3e9, start_address=0x1fffb000, length=0x123, dump_file="dump_file.hex")
        time.sleep(0.5)
        #xcp_get_basic_information(0x3e8, 0x3e9)
        #xcp_arbitration_id_discovery()  # FIXME
    except KeyboardInterrupt:
        print("\n\nTerminated by user")