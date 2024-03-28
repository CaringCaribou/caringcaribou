## Did you find a bug?
* If the bug is a security vulnerability, please refer to the [Security Policy](https://github.com/CaringCaribou/caringcaribou/blob/master/SECURITY.md)
* Check if a solution is present in the [Troubleshooting guide](https://github.com/CaringCaribou/caringcaribou/blob/master/documentation/troubleshooting.md)
* Check if the bug is already reported under [Issues](https://github.com/CaringCaribou/caringcaribou/issues)
* If there is no open issue addressing the problem, [open a new one](https://github.com/CaringCaribou/caringcaribou/issues/new)

## Do you intend to add a new feature or change an existing one?
Please open an issue with a high-level description of the change, to request feedback before submitting a pull request

## Before submitting a Pull Request
* Make sure the PR only adds/changes/fixes a single thing
* Make sure the change does not break the test suite (by running `caringcaribou -i <INTERFACE> test`)
* Make sure the code adheres to [PEP - 8 (Style Guide for Python Code)](https://peps.python.org/pep-0008/)
* Avoid [magic numbers](https://en.wikipedia.org/wiki/Magic_number_(programming)) in the code when possible
* Avoid changes that break other users' setups (such as dropping currently supported Python versions or hardcoding values for your favorite ECU)
