from __future__ import print_function
from lib.globals import DEFAULT_INTERFACE
import unittest


def print_interface_header():
    """Prints a header showing which interface is used"""
    interface_str = DEFAULT_INTERFACE if DEFAULT_INTERFACE is not None else "default"
    message = "Running tests using CAN interface '{0}'\n".format(interface_str)
    print(message)


def module_main(_):
    """Runs all Caring Caribou unit tests"""
    print_interface_header()
    # Run tests
    test_suite = unittest.TestLoader().discover("./tests")
    unittest.TextTestRunner(verbosity=2).run(test_suite)
