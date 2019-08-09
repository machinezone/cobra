'''Bot

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import click

from cobras.bavarde.bot.bot import runBot


@click.command()
def bot():
    '''Bot
    '''

    runBot()
