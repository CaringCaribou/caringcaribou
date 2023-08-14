#!/usr/bin/env python
# Released under GNU General Public License v3
# https://github.com/CaringCaribou/caringcaribou
import argparse
import can
import errno
from .utils import can_actions
import traceback
import pkg_resources


VERSION = "0.4"


def show_script_header():
    """Show script header"""
    print(r"""
{0}
CARING CARIBOU v{1}
{0}
""".format("-"*(16 + len(VERSION)), VERSION))


def fancy_header():
    """
    Returns a fancy header string.

    :rtype: str
    """
    return r"""{0}
CARING CARIBOU v{1}
\_\_    _/_/
    \__/
    (oo)\_______
    (__)\       )\/
        ||-----||
        ||     ||
{0}

""".format("-"*(16 + len(VERSION)), VERSION)


def available_modules_dict():
    modules = dict()
    for entry_point in pkg_resources.iter_entry_points("caringcaribou.modules"):
        nice_name = str(entry_point).split("=")[0].strip()
        modules[nice_name] = entry_point
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
        cc_mod = available_modules_dict()[module_name]
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
        cc_mod = load_module(args.module).load()
        cc_mod.module_main(args.module_args)
    except AttributeError:
        pass


# Main wrapper
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    except can.CanError as ex:
        print("\nCanError: {0}".format(ex))
    except IOError as ex:
        if ex.errno is errno.ENODEV:
            # Specifically catch "[Errno 19] No such device", which is caused by using an invalid interface
            print("\nIOError: {0}. This might be caused by an invalid or inactive CAN interface.".format(ex))
        else:
            # Print original stack trace
            traceback.print_exc()
    finally:
        print("")
