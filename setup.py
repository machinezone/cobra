"""Module used for python packaging

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
"""
from __future__ import absolute_import

import os
import sys

from setuptools import find_packages, setup

if sys.version_info[:2] < (3, 7):
    print("Error: Rcc requires Python 3.7")
    sys.exit(1)

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, "DOCKER_VERSION")) as f:
    VERSION = f.read().strip()


dev_requires = ["wheel", "isort", "mypy", "twine", "black", "pre-commit"]

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="rcc",
    version=VERSION,
    author="Benjamin Sergeant",
    author_email="bsergean@gmail.com",
    url="https://github.com/bsergean/rcc",
    description="A simple Redis client.",
    long_description=open(os.path.join(ROOT, "README.md")).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={"dev": dev_requires},
    license="BSD 3",
    include_package_data=True,
    entry_points={"console_scripts": ["rcc = rcc.runner:main"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
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
