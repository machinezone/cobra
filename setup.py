"""Module used for python packaging

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
"""
from __future__ import absolute_import

import os
import sys

from setuptools import find_packages, setup


def computeVersion():
    fullVersion = os.popen('git describe', 'r').read().splitlines()[0]
    assert fullVersion[0] == 'v'

    parts = fullVersion.split('-')
    majorMinor = parts[0][1:]
    if len(parts) > 1:
        patch = parts[1]
    else:
        patch = 0

    version = f'{majorMinor}.{patch}'
    return version


if sys.version_info[:2] < (3, 7):
    print("Error: Cobra requires Python 3.7")
    sys.exit(1)

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

VERSION = computeVersion()


dev_requires = ["wheel", "isort", "mypy", "twine", "black", "pre-commit"]

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="cobras",
    version=VERSION,
    author="Benjamin Sergeant",
    author_email="bsergean@gmail.com",
    url="https://github.com/machinezone/cobra",
    description="A realtime messaging server using WebSockets and Redis.",
    long_description=open(os.path.join(ROOT, "README.md")).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={"dev": dev_requires},
    license="BSD 3",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "cobra = cobras.runner:main",
            "bavarde = cobras.bavarde.runner:main",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
