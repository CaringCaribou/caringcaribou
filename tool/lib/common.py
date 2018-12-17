
def parse_int_dec_or_hex(value):
    """Parses an integer on base 10 (decimal) or 16 (hex with "0x" prefix)

    Examples:
    parse_int_dec_or_hex("1234") -> 1234
    parse_int_dec_or_hex("0xa7") -> 167

    :param value: the value to parse
    :type value: str
    :rtype int
    """
    return int(value, 0)


def str_to_int_list(s):
    """Converts a string representing CAN message data into a list of ints.

    Example:
    str_to_int_list("0102c0ffee") -> [01, 02, 0xc0, 0xff, 0xee]

    :param s: string representation of hex data
    :type s: str
    :return: list of byte values representing 's'
    :rtype: [int]
    """
    return [int(s[i * 2:i * 2 + 2], 16) for i in range(len(s) // 2)]


def int_from_byte_list(byte_values, start_index=0, length=None):
    """Parses a range of unsigned-up-to-8-bit-ints (bytes) from a list into a single int

    Example:
    int_from_byte_list([0x11, 0x22, 0x33, 0x44], 1, 2) = 0x2233 = 8755

    :param byte_values: list of byte values
    :param start_index: index of first byte in 'byte_values' to parse
    :param length: number of bytes to parse (None means "parse all")
    :type byte_values: [int]
    :type start_index: int
    :type length: int
    :return: int representation of parsed bytes
    :rtype int
    """
    if length is None:
        length = len(byte_values)
    value = 0
    for i in (range(start_index, start_index+length)):
        value = value << 8
        value += byte_values[i]
    return value


def list_to_hex_str(data, delimiter=""):
    """Returns a hex string representation of the int values
    in 'data', separated with 'delimiter' between each byte

    Example:
    list_to_hex_str([10, 100, 200]) -> 0a.64.c8
    list_to_hex_str([0x07, 0xff, 0x6c], "") -> 07ff6c
    :param data: iterable of values
    :param delimiter: separator between values in output
    :type data: [int]
    :type delimiter: str
    :return: hex string representation of data
    :rtype str
    """
    data_string = delimiter.join(["{0:02x}".format(i) for i in data])
    return data_string


def hex_str_to_nibble_list(data):
    """
    Converts a hexadecimal str values into a list of int nibbles.

    Example:
    hex_str_to_nibble_list("12ABF7") -> [0x1, 0x2, 0xA, 0xB, 0xF, 0x7]

    :param data: str of hexadecimal values
    :type data: str
    :return: list of int nibbles
    :rtype [int]
    """
    if data is None:
        return None
    data_ints = []
    for nibble_str in data:
        nibble_int = int(nibble_str, 16)
        data_ints.append(nibble_int)
    return data_ints


def msg_to_candump_format(msg):
    """Converts a CAN message to a string on candump format

    :param msg: message to convert
    :type msg: can.Message
    :return: candump format representation of 'msg'
    :rtype str
    """
    if msg.is_extended_id:
        output = "({0:.6f}) {1} {2:08X}#{3}"
    else:
        output = "({0:.6f}) {1} {2:03X}#{3}"
    data = list_to_hex_str(msg.data, "")
    candump = output.format(msg.timestamp, msg.channel, msg.arbitration_id, data)
    return candump
