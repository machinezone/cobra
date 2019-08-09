'''Module used for python packaging

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''
from __future__ import absolute_import

import platform
import os
import sys
from setuptools import find_packages, setup

if sys.version_info[:2] < (3, 7):
    print('Error: Cobra requires Python 3.7')
    sys.exit(1)

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

with open(os.path.join(ROOT, 'DOCKER_VERSION')) as f:
    VERSION = f.read().strip()


dev_requires = [
    'flake8',
    'isort',
    'honcho',
    'mypy',
    'aiojobs==0.1.0',
    'twine',
    'yapf'
]

tests_require = [
    'pytest',
    'pytest-cov',
    'pytest-xdist',
    'coverage'
]

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='cobras',
    version=VERSION,
    author='Benjamin Sergeant',
    author_email='bsergean@gmail.com',
    url='https://github.com/machinezone/cobra',
    description='A realtime messaging server using WebSockets and Redis.',
    long_description=open(os.path.join(ROOT, 'README.md')).read(),
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
        'dev': dev_requires
    },
    license='BSD 3',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'cobra = cobras.runner:main',
            'bavarde = cobras.bavarde.runner:main'
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)
