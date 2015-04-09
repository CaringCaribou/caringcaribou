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


def xcp_arbitration_id_discovery():
    """
    Scans for XCP support by bruteforcing XCP connect messages against different arbitration IDs.
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

if __name__ == "__main__":
    xcp_arbitration_id_discovery()