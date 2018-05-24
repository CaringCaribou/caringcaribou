import time


class DynamicallyDefinedIdentifierArg(object):
    def __init__(self, source_data_identifier, position_in_source_data_record, memory_size):
        self.sourceDataIdentifier = source_data_identifier
        self.positionInSourceDataRecord = position_in_source_data_record
        self.memorySize = memory_size


class Iso14229_1_nrc(object):
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    GENERAL_PROGRAMMING_FAILURE = 0x72
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F


class Iso14229_1_id(object):
    ECU_RESET = 0x11
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F
    READ_MEMORY_BY_ADDRESS = 0x23
    WRITE_MEMORY_BY_ADDRESS = 0x3D
    NEGATIVE_RESPONSE = 0x7F


class Iso14229_1(object):
    P3_CLIENT = 5000

    def __init__(self, tp):
        self.tp = tp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def send_request(self, tmp):
        return self.tp.request(tmp)

    def get_service_response_id(self, identifier):
        return identifier + 0x40

    def receive_response(self, wait_window):
        start_time = time.clock()
        while True:
            stop_time = time.clock()
            if (stop_time - start_time) * 1000 > wait_window:
                return None

            response = self.tp.indication(wait_window)
            if response is not None and len(response) > 3:
                if response[0] == Iso14229_1_id.NEGATIVE_RESPONSE and \
                        response[2] == Iso14229_1_nrc.REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING:
                    continue
            break
        return response

    def is_positive_response(self, response):
        if response is not None and len(response) > 0 and response[0] != 0x7F:
            return True
        return False

    def read_data_by_identifier(self, identifier):
        response = []
        num_dids = len(identifier)
        if num_dids > 0:
            request = [0] * ((num_dids * 2) + 1)
            request[0] = Iso14229_1_id.READ_DATA_BY_IDENTIFIER
            for i in range(0, num_dids):
                request[i * 2 + 1] = (identifier[i] >> 8) & 0xFF
                request[i * 2 + 2] = identifier[i] & 0xFF
            self.tp.request(request)
            response = self.receive_response(self.P3_CLIENT)
        return response

    def read_memory_by_address(self, address_and_length_format, memory_address, memory_size):
        address_size_format = (address_and_length_format >> 4) & 0xF
        data_size_format = (address_and_length_format & 0xF)

        request = [0] * (1 + 1 + address_size_format + data_size_format)
        request[0] = Iso14229_1_id.READ_MEMORY_BY_ADDRESS
        request[1] = address_and_length_format
        offset = 2
        for i in (range(0, address_size_format)):
            request[address_size_format + offset - i - 1] = (memory_address & 0xFF)
            memory_address = (memory_address >> 8)

        offset += address_size_format

        for i in (range(0, data_size_format)):
            request[data_size_format + offset - i - 1] = (memory_size & 0xFF)
            memory_size = (memory_size >> 8)

        self.tp.request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def write_memory_by_address(self, address_and_length_format, memory_address, memory_size, data):
        address_size_format = (address_and_length_format >> 4) & 0xF
        data_size_format = (address_and_length_format & 0xF)

        request = [0] * (1 + 1 + address_size_format + data_size_format)
        request[0] = Iso14229_1_id.WRITE_MEMORY_BY_ADDRESS
        request[1] = address_and_length_format
        offset = 2
        for i in (range(0, address_size_format)):
            request[address_size_format + offset - i - 1] = (memory_address & 0xFF)
            memory_address = (memory_address >> 8)

        offset += address_size_format

        for i in (range(0, data_size_format)):
            request[data_size_format + offset - i - 1] = (memory_size & 0xFF)
            memory_size = (memory_size >> 8)

        request += data
        self.tp.request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def write_data_by_identifier(self, identifier, data):
        request = [0] * (1 + 2)

        request[0] = Iso14229_1_id.WRITE_DATA_BY_IDENTIFIER
        request[1] = (identifier >> 8) & 0xFF
        request[2] = identifier & 0xFF
        request += data

        self.tp.request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def input_output_control_by_identifier(self, identifier, data):
        request = [0] * (1 + 2)

        request[0] = Iso14229_1_id.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER
        request[1] = (identifier >> 8) & 0xFF
        request[2] = identifier & 0xFF
        request += data

        self.tp.request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def dynamically_define_data_identifier(self, identifier, sub_function, sub_function_arg):
        if identifier is None or sub_function is None or sub_function_arg is None:
            return None

        request = [0] * (1 + 1 + 2 + len(sub_function_arg) * 4)
        request[0] = Iso14229_1_id.DYNAMICALLY_DEFINE_DATA_IDENTIFIER
        request[1] = sub_function
        request[2] = (identifier >> 8) & 0xFF
        request[3] = identifier & 0xFF

        offset = 4
        for did in sub_function_arg:
            request[offset + 0] = (did.sourceDataIdentifier >> 8) & 0xFF
            request[offset + 1] = did.sourceDataIdentifier & 0xFF
            request[offset + 2] = did.positionInSourceDataRecord
            request[offset + 3] = did.memorySize
            offset += 4

        self.tp.request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def ecu_reset(self, sub_function):
        if sub_function is None:
            return None

        suppress_positive_response = False
        if (sub_function & 0x80) != 0:
            suppress_positive_response = True

        request = [0] * 2
        request[0] = Iso14229_1_id.ECU_RESET
        request[1] = sub_function

        self.tp.request(request)
        response = None

        if not suppress_positive_response:
            response = self.receive_response(self.P3_CLIENT)

        return response

    def read_data_by_periodic_identifier(self, transmission_mode, identifier):
        if transmission_mode is None or identifier is None or len(identifier) == 0:
            return None

        request = [0] * (2 + len(identifier))
        request[0] = Iso14229_1_id.READ_DATA_BY_PERIODIC_IDENTIFIER
        request[1] = transmission_mode

        for i in range(0, len(identifier)):
            request[2 + i] = identifier[i]

        self.tp.request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response
