#!/usr/bin/env python
"""
Caring Caribou
==============
- A friendly automotive security exploration tool, initiated as part of the research project HEAVENS (HEAling Vulnerabilities to ENhance Software Security and Safety), now a stand-alone project.
- A zero-knowledge tool that can be dropped onto an automotive network and collect information regarding what services and vulnerabilities exist.
"""

from setuptools import find_packages, setup

version = "0.4"
dl_version = "master" if "dev" in version else "v{}".format(version)

print(r"""-----------------------------------
 Installing Caring Caribou version {0}
-----------------------------------
""".format(version))

setup(
    name="caringcaribou",
    version=version,
    author="Kasper Karlsson",
    # author_email="TBD",
    description="A friendly automotive security exploration tool",
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
            "cc.py=caringcaribou.caringcaribou:main",
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
 Installation completed, run `cc.py --help` to get started
-----------------------------------------------------------
""")
