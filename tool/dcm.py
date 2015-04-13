import can_actions

services = {
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
