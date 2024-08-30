import pytest
from unittest.mock import patch, MagicMock
from caringcaribou.modules.listener import start_listener, parse_args


def mock_bus_generator():
    yield MagicMock(arbitration_id=0x123)
    yield MagicMock(arbitration_id=0x456)
    yield MagicMock(arbitration_id=0x123)
    raise KeyboardInterrupt


def test_parse_args_no_reverse():
    args = []
    parsed_args = parse_args(args)
    assert parsed_args.reverse is False


def test_parse_args_reverse():
    args = ["--reverse"]
    parsed_args = parse_args(args)
    assert parsed_args.reverse is True


@pytest.mark.parametrize("falling_sort, expected_output", [
    (
            True,
            (
                    'Running listener (press Ctrl+C to exit)\n\r'
                    'Last ID: 0x00000123 (1 unique arbitration IDs found) \r'
                    'Last ID: 0x00000456 (2 unique arbitration IDs found) \n\n'
                    'Detected arbitration IDs:\n'
                    'Arb id 0x00000123 2 hits\n'
                    'Arb id 0x00000456 1 hits\n'
            )
    ),
    (
            False,
            (
                    "Running listener (press Ctrl+C to exit)\n\r"
                    "Last ID: 0x00000123 (1 unique arbitration IDs found) \r"
                    "Last ID: 0x00000456 (2 unique arbitration IDs found) \n\n"
                    "Detected arbitration IDs:\n"
                    "Arb id 0x00000456 1 hits\n"
                    "Arb id 0x00000123 2 hits\n"
            )
    ),
])
def test_start_listener(falling_sort, expected_output):
    with (patch('caringcaribou.modules.listener.CanActions') as MockCanActions,
          patch('sys.stdout', new_callable=MagicMock) as mock_stdout):
        mock_bus = MagicMock()
        mock_bus.__iter__.side_effect = mock_bus_generator
        MockCanActions.return_value.__enter__.return_value.bus = mock_bus

        start_listener(falling_sort)

        output = ''.join(call.args[0] for call in mock_stdout.write.call_args_list)
        assert expected_output in output


def test_start_listener_keyboard_interrupt():
    with (patch('caringcaribou.modules.listener.CanActions') as MockCanActions,
          patch('sys.stdout', new_callable=MagicMock) as mock_stdout):
        mock_bus = MagicMock()
        mock_bus.__iter__.side_effect = KeyboardInterrupt
        MockCanActions.return_value.__enter__.return_value.bus = mock_bus

        start_listener(falling_sort=True)

        output = ''.join(call.args[0] for call in mock_stdout.write.call_args_list)
        assert "\nNo arbitration IDs were detected.\n" in output
