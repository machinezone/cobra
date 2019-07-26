'''Setup cobra

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''
import click

from cobra.common.apps_config import AppsConfig, getDefaultAppsConfigPath
from cobra.runner.superuser import preventRootUsage


@click.command()
def init():
    '''Setup cobra
    '''

    preventRootUsage()

    path = getDefaultAppsConfigPath()
    appsConfig = AppsConfig(path)
    appsConfig.generateDefaultConfig()
