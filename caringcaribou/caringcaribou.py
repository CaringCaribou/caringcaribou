#!/usr/bin/env python
# Released under GNU General Public License v3
# https://github.com/CaringCaribou/caringcaribou
import argparse
import can
import errno
from .utils import can_actions
import sys
import traceback
import importlib
import importlib.resources


VERSION = "0.7"


def show_script_header():
    """Show script header"""
    print(r"""
{0}
CARING CARIBOU v{1} - python {2}
{0}
""".format("-"*(16 + len(VERSION)), VERSION, sys.version))


def fancy_header():
    """
    Returns a fancy header string.

    :rtype: str
    """
    return r"""{0}
CARING CARIBOU v{1} - python {2}
\_\_    _/_/
    \__/
    (oo)\_______
    (__)\       )\/
        ||-----||
        ||     ||
{0}

""".format("-"*(16 + len(VERSION)), VERSION, sys.version)


def show_missing_canrc_instruction():
    print("\nThis error is most likely due to missing a '.canrc' file for python-can in your home directory.\n"
          "For Linux setups using a SocketCAN interface, try running the following command:\n\n"
          "$ printf \"[default]\\n"
          "interface = socketcan\\n"
          "channel = can0\" > $HOME/.canrc\n\n"
          "Additional supported interface types are listed at "
          "https://python-can.readthedocs.io/en/stable/configuration.html#configuration-file")


def available_modules_dict():
    modules = dict()
    package_name = 'caringcaribou.modules'

    # List all the available resources in the package
    module_names = importlib.resources.contents(package_name)
    module_names = [name for name in module_names if name.endswith(".py") and name != "__init__.py"]

    for module_name in module_names:
        nice_name = module_name[:-3]  # Strip the .py extension
        module_full_name = f"{package_name}.{nice_name}"
        modules[nice_name] = module_full_name
    return modules


def available_modules():
    """
    Get a string showing available CaringCaribou modules.
    Modules are listed in setup.py: entry_points['caringcaribou.modules']

    :return: A string listing available modules
    :rtype: str
    """
    modules = list(available_modules_dict().keys())
    modules.sort()
    mod_str = "available modules:\n  "
    mod_str += ", ".join(modules)
    return mod_str
    

def parse_arguments():
    """
    Argument parser for interface, module name and module arguments.

    :return: Namespace containing module name and arguments
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="{0}A friendly car security exploration tool".format(fancy_header()),
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=available_modules())
    parser.add_argument("-i", dest="interface", default=None,
                        help="force interface, e.g. 'can1' or 'vcan0'")
    parser.add_argument("module",
                        help="Name of the module to run")
    parser.add_argument("module_args", metavar="...", nargs=argparse.REMAINDER,
                        help="Arguments to module")
    args = parser.parse_args()
    return args


def load_module(module_name):
    """
    Dynamically imports module_name from the folder specified by MODULES_DIR.

    :param str module_name: Name of the module to import as referenced in entry_points
                            e.g. "dcm", "uds", "listener"
    :return: a module on success, None otherwise
    """
    try:
        print("Loading module '{0}'\n".format(module_name))
        full_module_name = available_modules_dict()[module_name]
        cc_mod = importlib.import_module(full_module_name)
        return cc_mod
    except KeyError as e:
        print("Load module failed: module {0} is not available".format(e))
        return None


def main():
    """Main execution handler"""
    # Parse and validate arguments
    args = parse_arguments()
    # Show header
    show_script_header()
    # Save interface to can_actions, for use in modules
    if args.interface:
        can_actions.DEFAULT_INTERFACE = args.interface
    try:
        # Load module
        cc_mod = load_module(args.module)
        cc_mod.module_main(args.module_args)
    except AttributeError:
        pass
    except KeyboardInterrupt:
        pass
    except can.exceptions.CanInterfaceNotImplementedError as e:
        # This error is likely caused by missing python-can configuration file
        print("\n---\n\nCanInterfaceNotImplementedError: {0}".format(e))
        show_missing_canrc_instruction()
    except can.CanError as e:
        print("\nCanError: {0}".format(e))
    except IOError as e:
        if e.errno is errno.ENODEV:
            # Specifically catch "[Errno 19] No such device", which is caused by using an invalid interface
            print("\nIOError: {0}. This might be caused by an invalid or inactive CAN interface.".format(e))
        else:
            # Print original stack trace
            traceback.print_exc()
    finally:
        print("")


# Main wrapper
if __name__ == '__main__':
    main()
