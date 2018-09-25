import time


class DynamicallyDefinedIdentifierArg(object):
    def __init__(self, source_data_identifier, position_in_source_data_record, memory_size):
        self.sourceDataIdentifier = source_data_identifier
        self.positionInSourceDataRecord = position_in_source_data_record
        self.memorySize = memory_size


class NegativeResponseCodes(object):
    """
    ISO-14229-1 negative response codes
    """
    POSITIVE_RESPONSE = 0x00
    # 0x01-0x0F ISO SAE Reserved
    GENERAL_REJECT = 0x10
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    RESPONSE_TOO_LONG = 0x14
    # 0x15-0x20 ISO SAE Reserved
    BUSY_REPEAT_REQUEST = 0x21
    CONDITIONS_NOT_CORRECT = 0x22
    # 0x23 ISO SAE Reserved
    REQUEST_SEQUENCE_ERROR = 0x24
    NO_RESPONSE_FROM_SUBNET_COMPONENT = 0x25
    FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION = 0x26
    # 0x27-0x30 ISO SAE Reserved
    REQUEST_OUT_OF_RANGE = 0x31
    # 0x32 ISO SAE Reserved
    SECURITY_ACCESS_DENIED = 0x33
    # 0x34 ISO SAE Reserved
    INVALID_KEY = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    # 0x38-0x4F Reserved by extended data link security document
    # 0x50-0x6F ISO SAE Reserved
    UPLOAD_DOWNLOAD_NOT_ACCEPTED = 0x70
    TRANSFER_DATA_SUSPENDED = 0x71
    GENERAL_PROGRAMMING_FAILURE = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER = 0x73
    # 0x74-0x77 ISO SAE Reserved
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78
    # 0x79-0x7D ISO SAE Reserved
    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F
    # 0x80 ISO SAE Reserved
    RPM_TOO_HIGH = 0x81
    RPM_TOO_LOW = 0x82
    ENGINE_IS_RUNNING = 0x83
    ENGINE_IS_NOT_RUNNING = 0x84
    ENGINE_RUN_TIME_TOO_LOW = 0x85
    TEMPERATURE_TOO_HIGH = 0x86
    TEMPERATURE_TOO_LOW = 0x87
    VEHICLE_SPEED_TOO_HIGH = 0x88
    VEHICLE_SPEED_TOO_LOW = 0x89
    THROTTLE_PEDAL_TOO_HIGH = 0x8A
    THROTTLE_PEDAL_TOO_LOW = 0x8B
    TRANSMISSION_RANGE_NOT_IN_NEUTRAL = 0x8C
    TRANSMISSION_RANGE_NOT_IN_GEAR = 0x8D
    # 0x8E ISO SAE Reserved
    BRAKE_SWITCHES_NOT_CLOSED = 0x8F
    SHIFT_LEVER_NOT_IN_PARK = 0x90
    TORQUE_CONVERTER_CLUTCH_LOCKED = 0x91
    VOLTAGE_TOO_HIGH = 0x92
    VOLTAGE_TOO_LOW = 0x93
    # 0x94-0xEF Reserved for specific conditions not correct
    # 0xF0-0xFE Vehicle manufacturer specific conditions not correct
    # 0xFF ISO SAE Reserved


class ServiceID(object):
    """
    ISO-14229-1 service ID definitions
    """
    DIAGNOSTIC_SESSION_CONTROL = 0x10
    ECU_RESET = 0x11
    CLEAR_DIAGNOSTIC_INFORMATION = 0x14
    READ_DTC_INFORMATION = 0x19
    READ_DATA_BY_IDENTIFIER = 0x22
    READ_MEMORY_BY_ADDRESS = 0x23
    READ_SCALING_DATA_BY_IDENTIFIER = 0x24
    SECURITY_ACCESS = 0x27
    COMMUNICATION_CONTROL = 0x28
    READ_DATA_BY_PERIODIC_IDENTIFIER = 0x2A
    DYNAMICALLY_DEFINE_DATA_IDENTIFIER = 0x2C
    WRITE_DATA_BY_IDENTIFIER = 0x2E
    INPUT_OUTPUT_CONTROL_BY_IDENTIFIER = 0x2F
    ROUTINE_CONTROL = 0x31
    REQUEST_DOWNLOAD = 0x34
    REQUEST_UPLOAD = 0x35
    TRANSFER_DATA = 0x36
    REQUEST_TRANSFER_EXIT = 0x37
    REQUEST_FILE_TRANSFER = 0x38
    WRITE_MEMORY_BY_ADDRESS = 0x3D
    TESTER_PRESENT = 0x3E
    ACCESS_TIMING_PARAMETER = 0x83
    SECURED_DATA_TRANSMISSION = 0x84
    CONTROL_DTC_SETTING = 0x85
    RESPONSE_ON_EVENT = 0x86
    LINK_CONTROL = 0x87


class Constants(object):
    # NR_SI (Negative Response Service Identifier) is a bit special, since it is not a service per se.
    # From ISO-14229-1 specification: "The NR_SI value is co-ordinated with the SI values. The NR_SI
    # value is not used as a SI value in order to make A_Data coding and decoding easier."
    NR_SI = 0x7F


class Iso14229_1(object):
    P3_CLIENT = 5

    def __init__(self, tp):
        self.tp = tp

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def get_service_response_id(identifier):
        """
        Returns the service response ID for 'identifier'

        :param identifier: Identifier
        :return: Service response ID for 'identifier'
        """
        return identifier + 0x40

    def send_request(self, data):
        """
        Sends a request message containing 'data' through the underlying TP layer

        :param data: The data to send
        :return: None
        """
        return self.tp.send_request(data)

    def send_response(self, data):
        """
        Sends a response message containing 'data' through the underlying TP layer

        :param data: The data to send
        :return: None
        """
        return self.tp.send_response(data)

    def receive_response(self, wait_window):
        """
        Attempts to receive a response through the underlying TP layer

        :param wait_window: Minimum time (in seconds) to wait before timeout
        :return: The received response if successful,
                 False otherwise
        """
        start_time = time.clock()
        while True:
            current_time = time.clock()
            if (current_time - start_time) > wait_window:
                return None

            response = self.tp.indication(wait_window)
            if response is not None and len(response) > 3:
                if response[0] == Constants.NR_SI and \
                        response[2] == NegativeResponseCodes.REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING:
                    continue
            break
        return list(response)

    @staticmethod
    def is_positive_response(response):
        """
        Returns a bool indicating whether 'response' is positive

        :param response: Response data
        :return: False if response is a NEGATIVE_RESPONSE,
                 True otherwise
        """
        if response is not None and len(response) > 0 and response[0] != Constants.NR_SI:
            return True
        return False

    def read_data_by_identifier(self, identifier):
        """
        Sends a "read data by identifier" request for 'identifier'

        :param identifier: Data identifier
        :return: Response data if successful,
                 None otherwise
        """
        response = []
        num_dids = len(identifier)
        if num_dids > 0:
            request = [0] * ((num_dids * 2) + 1)
            request[0] = ServiceID.READ_DATA_BY_IDENTIFIER
            for i in range(0, num_dids):
                request[i * 2 + 1] = (identifier[i] >> 8) & 0xFF
                request[i * 2 + 2] = identifier[i] & 0xFF
            self.tp.send_request(request)
            response = self.receive_response(self.P3_CLIENT)
        return response

    def read_memory_by_address(self, address_and_length_format, memory_address, memory_size):
        """
        Sends a "read memory by address" request for 'memory_address'

        :param address_and_length_format: Address and length format
        :param memory_address: Memory address
        :param memory_size: Memory size
        :return: Response data if successful,
                 None otherwise
        """
        address_size_format = (address_and_length_format >> 4) & 0xF
        data_size_format = (address_and_length_format & 0xF)

        request = [0] * (1 + 1 + address_size_format + data_size_format)
        request[0] = ServiceID.READ_MEMORY_BY_ADDRESS
        request[1] = address_and_length_format
        offset = 2
        for i in (range(0, address_size_format)):
            request[address_size_format + offset - i - 1] = (memory_address & 0xFF)
            memory_address = (memory_address >> 8)

        offset += address_size_format

        for i in (range(0, data_size_format)):
            request[data_size_format + offset - i - 1] = (memory_size & 0xFF)
            memory_size = (memory_size >> 8)

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def write_memory_by_address(self, address_and_length_format, memory_address, memory_size, data):
        """
        Sends a "write memory by address" request to write 'data' to 'memory_address'

        :param address_and_length_format: Address and length format
        :param memory_address: Memory address
        :param memory_size: Memory size
        :param data: The data to write to 'memory_address'
        :return: Response data if successful,
                 None otherwise
        """
        address_size_format = (address_and_length_format >> 4) & 0xF
        data_size_format = (address_and_length_format & 0xF)

        request = [0] * (1 + 1 + address_size_format + data_size_format)
        request[0] = ServiceID.WRITE_MEMORY_BY_ADDRESS
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
        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def write_data_by_identifier(self, identifier, data):
        """
        Sends a "write data by identifier" request to write 'data' to 'identifier'

        :param identifier: Data identifier
        :param data: Data to write to 'identifier'
        :return: Response data if successful,
                 None otherwise
        """
        request = [0] * (1 + 2)

        request[0] = ServiceID.WRITE_DATA_BY_IDENTIFIER
        request[1] = (identifier >> 8) & 0xFF
        request[2] = identifier & 0xFF
        request += data
        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def input_output_control_by_identifier(self, identifier, data):
        """
        Sends a "input output control by identifier" request for 'data' to 'identifier'

        :param identifier: Data identifier
        :param data: Data
        :return: Response data if successful,
                 None otherwise
        """
        request = [0] * (1 + 2)

        request[0] = ServiceID.INPUT_OUTPUT_CONTROL_BY_IDENTIFIER
        request[1] = (identifier >> 8) & 0xFF
        request[2] = identifier & 0xFF
        request += data

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def dynamically_define_data_identifier(self, identifier, sub_function, sub_function_arg):
        """
        Sends a "dynamically define data identifier" request for 'identifier'

        :param identifier: DDDID to set
        :param sub_function: Sub function
        :param sub_function_arg: Sub function arguments
        :return: Response data if successful,
                 None otherwise
        """
        if identifier is None or sub_function is None or sub_function_arg is None:
            return None

        request = [0] * (1 + 1 + 2 + len(sub_function_arg) * 4)
        request[0] = ServiceID.DYNAMICALLY_DEFINE_DATA_IDENTIFIER
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

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response

    def ecu_reset(self, sub_function):
        """
        Sends an "ECU reset" request for 'sub_function'

        :param sub_function: Sub function
        :return: Response data if successful AND positive responses are not suppressed by 'sub_function',
                 None otherwise
        """
        if sub_function is None:
            return None

        suppress_positive_response = False
        if (sub_function & 0x80) != 0:
            suppress_positive_response = True

        request = [0] * 2
        request[0] = ServiceID.ECU_RESET
        request[1] = sub_function

        self.tp.send_request(request)
        response = None

        if not suppress_positive_response:
            response = self.receive_response(self.P3_CLIENT)

        return response

    def read_data_by_periodic_identifier(self, transmission_mode, identifier):
        """
        Sends a "read data by periodic identifier" request for 'identifier'

        :param transmission_mode: Transmission mode
        :param identifier: Identifier
        :return: Response data if successful AND positive responses are not suppressed by 'sub_function',
                 None otherwise
        """
        if transmission_mode is None or identifier is None or len(identifier) == 0:
            return None

        request = [0] * (2 + len(identifier))
        request[0] = ServiceID.READ_DATA_BY_PERIODIC_IDENTIFIER
        request[1] = transmission_mode

        for i in range(0, len(identifier)):
            request[2 + i] = identifier[i]

        self.tp.send_request(request)
        response = self.receive_response(self.P3_CLIENT)

        return response
