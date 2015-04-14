from can_actions import *
from sys import stdout

DCM_SERVICE_NAMES = {
    0x10: 'DIAGNOSTIC_SESSION_CONTROL',
    0x11: 'ECU_RESET',
    0x14: 'CLEAR_DIAGNOSTIC_INFORMATION',
    0x19: 'READ_DTC_INFORMATION',
    0x22: 'READ_DATA_BY_IDENTIFIER',
    0x23: 'READ_MEMORY_BY_ADDRESS',
    0x24: 'READ_SCALING_DATA_BY_IDENTIFIER',
    0x27: 'SECURITY_ACCESS',
    0x28: 'COMMUNICATION_CONTROL',
    0x2A: 'READ_DATA_BY_PERIODIC_IDENTIFIER',
    0x2C: 'DYNAMICALLY_DEFINE_DATA_IDENTIFIER',
    0x2E: 'WRITE_DATA_BY_IDENTIFIER',
    0x2F: 'INPUT_OUTPUT_CONTROL_BY_IDENTIFIER',
    0x31: 'ROUTINE_CONTROL',
    0x34: 'REQUEST_DOWNLOAD',
    0x35: 'REQUEST_UPLOAD',
    0x36: 'TRANSFER_DATA',
    0x37: 'REQUEST_TRANSFER_EXIT',
    0x38: 'REQUEST_FILE_TRANSFER',
    0x3D: 'WRITE_MEMORY_BY_ADDRESS',
    0x3E: 'TESTER_PRESENT',
    0x7F: 'NEGATIVE_RESPONSE',
    0x83: 'ACCESS_TIMING_PARAMETER',
    0x84: 'SECURED_DATA_TRANSMISSION',
    0x85: 'CONTROL_DTC_SETTING',
    0x86: 'RESPONSE_ON_EVENT',
    0x87: 'LINK_CONTROL'
}

NRC = {
    0x10: 'generalReject',
    0x11: 'serviceNotSupported',
    0x12: 'sub-functionNotSupported',
    0x13: 'incorrectMessageLengthOrInvalidFormat',
    0x21: 'busyRepeatRequest',
    0x22: 'conditionsNotCorrect',
    0x31: 'requestOutOfRange',
    0x33: 'securityAccessDenied',
    0x72: 'generalProgrammingFailure',
    0x78: 'requestCorrectlyReceivedResponsePending',
    0x7F: 'serviceNotSupportedInActiveSession'
}


def dcm_discovery():
    """
    Scans for DCM support by brute forcing diagnostic session control messages against different arbitration IDs.
    """
    can_wrap = CanActions()
    print("Starting DCM service discovery")

    def response_analyser_wrapper(arb_id):
        print "\rSending DCM Tester Present to {0:04x}".format(arb_id),
        stdout.flush()

        def response_analyser(msg):
            # Catch both ok and negative response
            if msg.data[1] == 0x50 or msg.data[1] == 0x7F:
                print("\nFound DCM at arbitration ID {0:04x}, reply at {1:04x}".format(arb_id, msg.arbitration_id))
                can_wrap.bruteforce_stop()
        return response_analyser

    def none_found():
        print("\nDCM could not be found")

    # Message to bruteforce - [length, session control, default session]
    message = insert_message_length([0x10, 0x01])
    can_wrap.bruteforce_arbitration_id(message, response_analyser_wrapper,
                                       min_id=0x720, max_id=0x740, callback_not_found=none_found)  # FIXME values


def service_discovery(send_arb_id, rcv_arb_id):
    """
    Scans for supported DCM services. Prints a list of all supported services afterwards.

    :param send_arb_id: Arbitration ID used for outgoing messages
    :param rcv_arb_id: Arbitration ID expected for incoming messages
    :return:
    """
    can_wrap = CanActions(arb_id=send_arb_id)
    print("Starting DCM service discovery")
    supported_services = []

    def response_analyser_wrapper(service_id):
        print "\rProbing service 0x{0:02x} ({1} found)".format(service_id, len(supported_services)),
        stdout.flush()

        def response_analyser(msg):
            # Skip incoming messages with wrong arbitration ID
            if msg.arbitration_id != rcv_arb_id:
                return
            # Skip replies where service is not supported
            if msg.data[3] == 0x11:
                return
            # Service supported - add to list
            supported_services.append(msg.data[2])
        return response_analyser

    def done():
        print("\nDone!")

    # Message to bruteforce - [length, service id]
    msg = insert_message_length([0x00])
    # Index of service id byte in message
    service_index = 1
    try:
        # Initiate bruteforce
        can_wrap.bruteforce_data(msg, service_index, response_analyser_wrapper, callback_not_found=done)
    finally:
        # Clear listeners
        can_wrap.notifier.listeners = []
        print("")
        # Print id and name of all found services
        for service in supported_services:
            service_name = DCM_SERVICE_NAMES.get(service, "Unknown service")
            print("Supported service 0x{0:02x}: {1}".format(service, service_name))


def subfunc_discovery(service_id, send_arb_id, rcv_arb_id):
    can_wrap = CanActions(arb_id=send_arb_id)
    print("Starting DCM sub function discovery")

    def response_analyser_wrapper(subfunc_id):
        print "\rTesting sub function {0:04x} of function {1:04x}".format(subfunc_id, service_id),
        stdout.flush()


        def response_analyser(msg):
            if msg.arbitration_id != rcv_arb_id:
                return
            # Catch both ok and ??? TODO - read iso 14229 spec to find out what 0x12 means
            if msg.data[1]-0x40 == service_id or (msg.data[1] == 0x7F and msg.data[3] == 0x12):
                print("\nFound valid subfunction {0:04x}".format(subfunc_id))
                print(msg)
        return response_analyser

    def finished():
        print("\nDone")

    # Message to bruteforce - [length, session control, default session]
    message = insert_message_length([service_id, 0x00])
    can_wrap.bruteforce_data_new(message, bruteforce_indices=2, callback=response_analyser_wrapper,
                             callback_not_found=finished)


if __name__ == "__main__":
    try:
        # dcm_discovery()
        service_discovery(0x733, 0x633)
        #subfunc_discovery(0x10, 0x733, 0x633)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
