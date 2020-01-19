#!/usr/bin/env python
# Released under GNU General Public License v3
# https://github.com/CaringCaribou/caringcaribou
import argparse
import can
import errno
import lib.can_actions
import importlib
import traceback
import os

VERSION = "0.3"

# Find the right "modules" directory, even if the script is run from another directory
MODULES_DIR = "modules"


def show_script_header():
    """Show script header"""
    print(r"""
-------------------
CARING CARIBOU v{0}
-------------------
""".format(VERSION))


def fancy_header():
    """
    Returns a fancy header string.

    :rtype: str
    """
    return r"""-------------------
CARING CARIBOU v{0}
\_\_    _/_/
    \__/
    (oo)\_______
    (__)\       )\/
        ||-----||
        ||     ||
-------------------

""".format(VERSION)


def available_modules():
    """
    Get a string showing available CaringCaribou modules.

    :return: A string listing available modules
    :rtype: str
    """
    blacklisted_files = ["__init__.py"]
    modules = [m[:-3] for m in os.listdir(MODULES_DIR) if m.endswith(".py") and m not in blacklisted_files]
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

    :param str module_name: Name of the module to import (without file extension)
                            e.g. "listener" if module is stored in "./modules/listener.py"
    :return: a loaded module on success, None otherwise
    """
    # Clean module name (since module location is decided by MODULES_DIR, we don't take a full path)
    clean_mod_name = os.path.basename(module_name)
    package = "{0}.{1}".format(MODULES_DIR, clean_mod_name)
    try:
        # Import module
        py_mod = importlib.import_module(package)
        print("Loaded module '{0}'\n".format(clean_mod_name))
        return py_mod
    except ImportError as e:
        print("Load module failed: {0}".format(e))
        return None


def main():
    """Main execution handler"""
    # Parse and validate arguments
    args = parse_arguments()
    # Show header
    show_script_header()
    # Save interface to can_actions, for use in modules
    if args.interface:
        lib.can_actions.DEFAULT_INTERFACE = args.interface
    # Dynamically load module
    mod = load_module(args.module)
    if mod is not None:
        func_name = "module_main"
        func_exists = func_name in dir(mod) and callable(getattr(mod, func_name))
        if func_exists:
            # Run module, passing any remaining arguments
            mod.module_main(args.module_args)
        else:
            # Print error message if module_main is missing
            print("ERROR: Module '{0}' does not contain a '{1}' function.".format(args.module, func_name))


# Main wrapper
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
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
