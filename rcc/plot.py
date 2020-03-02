'''Plot ascii charts'''
from __future__ import print_function

import os
import sys

import click


def asciiPlot(title, items):

    click.secho('== {} =='.format(title), fg='cyan')

    values = ['{} {}'.format(key, value) for key, value in items.items()]

    # -p for percent
    # -A to aggregate (required)
    barChart = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'vendor', 'bar_chart.py'
    )
    os.system(
        "echo '%s' | %s %s -A -v -r" % ("\n".join(values), sys.executable, barChart)
    )
    print()
