#!/usr/bin/env python
"""
Caring Caribou Next
===================
- This work was initiated as part of the research project HEAVENS (HEAling Vulnerabilities to ENhance Software Security and Safety), and was forked to act as a quick way to perform changes for personal use, and for people that are intrested on those changes.
- While caringcaribou is not perfect, it can act as a quick evaluation utility, which can help with exploration of a target ECU over several target networks/interfaces. This project is not meant to be a complete one button solution, but a tool that can give researchers a quick and easy head start into the path of ECU exploration.
"""

from setuptools import find_packages, setup

version = "1"
dl_version = "master" if "dev" in version else "v{}".format(version)

print(r"""-----------------------------------
 Installing Caring Caribou version {0}
-----------------------------------
""".format(version))

setup(
    name="caringcaribounext",
    version=version,
    author="Thomas Sermpinis",
    # author_email="TBD",
    description="A fork of a friendly automotive security exploration tool",
    long_description=__doc__,
    keywords=["automotive", "security", "CAN", "automotive protocols", "fuzzing"],
    url="https://github.com/CaringCaribou/caringcaribou/",
    download_url="https://github.com/CaringCaribou/caringcaribou/tarball/{}".format(dl_version),
    license="GPLv3",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "python-can"
    ],
    entry_points={
        "console_scripts": [
            "ccn.py=caringcaribou.caringcaribou:main",
            "caringcaribou=caringcaribou.caringcaribou:main",
        ],
        "caringcaribou.modules": [
            "dcm = caringcaribou.modules.dcm",
            "doip = caringcaribou.modules.doip",
            "dump = caringcaribou.modules.dump",
            "fuzzer = caringcaribou.modules.fuzzer",
            "listener = caringcaribou.modules.listener",
            "send = caringcaribou.modules.send",
            "test = caringcaribou.modules.test",
            "uds_fuzz = caringcaribou.modules.uds_fuzz",
            "uds = caringcaribou.modules.uds",
            "xcp = caringcaribou.modules.xcp",
        ]
    }
)

print(r"""-----------------------------------------------------------
 Installation completed, run `ccn.py --help` to get started
-----------------------------------------------------------
""")
