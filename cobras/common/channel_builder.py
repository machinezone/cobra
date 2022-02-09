'''Manipulate and create extra channel names based on rules defined in apps config

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import logging
import random
from cobras.common.algorithm import extractAttributeFromDict


def updateMsg(rules, msg):
    if rules is None or len(rules) == 0:
        return msg

    body = msg.get('body')
    if body is None:  # invalid cobra schema
        return msg

    message = body.get('message')
    if message is None or not isinstance(message, dict):  # invalid cobra schema
        return msg

    channels = body.get('channels')
    if channels is not None and not isinstance(channels, list):  # invalid cobra schema
        return msg

    if channels is None:
        channels = []

    channel = body.get('channel')
    if channel is not None:
        channels.append(channel)

    # Now loop through each rules in the app config
    # TODO extract the rule validation so it only executes once to sanitize the input
    # instead of every time we update a message
    for ruleName, rule in rules.items():
        if not isinstance(ruleName, str):
            logging.warning(f'Invalid rule name \'{ruleName}\', should be a string')
            continue

        if rule is None or not isinstance(rule, dict):
            logging.warning(f'Invalid rule \'{rule}\', should be a dict')
            continue

        kind = rule.get('kind')
        if not isinstance(kind, str):
            logging.warning(f'Invalid rule kind \'{kind}\', should be a string')
            continue

        if kind == 'compose2':
            separator = rule.get('separator')
            field1 = rule.get('field1')
            field2 = rule.get('field2')

            if separator is None or field1 is None or field2 is None:
                logging.warning(f'Invalid compose2 rule \'{rule}\'')
            else:
                field1 = extractAttributeFromDict(message, field1)
                if field1 is None or field1 == {}:
                    continue

                field2 = extractAttributeFromDict(message, field2)
                if field2 is None or field2 == {}:
                    continue

                channel = f'{field1}{separator}{field2}'
            channels.append(channel)

        elif kind == 'add_shard':
            shards = rule.get('shards')
            if not (isinstance(kind, (int, str)) and str(shards).isdigit()):
                logging.warning(
                    f'Invalid {kind} rule, " \
                                "\'shards\' should be a positive integer, got {shards}'
                )
                continue

            channel = rule.get('channel')
            if not isinstance(channel, str):
                logging.warning(f'Invalid {kind} rule, \'channel\' should be a string')
                continue

            shard = random.randrange(start=0, stop=shards)
            channels.append(channel.format(shard=shard))

        elif kind == 'add':
            channel = rule.get('channel')
            if not isinstance(channel, str):
                logging.warning(f'Invalid {kind} rule, \'channel\' should be a string')
                continue

            channels.append(channel)

        elif kind == 'remove':
            prefix = rule.get('prefix')
            channels = {chan for chan in channels if not chan.startswith(prefix)}
            channels = list(channels)

        else:
            logging.warning(f'Invalid rule kind \'{kind}\'')
            continue

    msg['body']['channels'] = list(set(channels))

    return msg
