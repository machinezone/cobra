'''Utility to make sure that exceptions are handled and logged to sentry

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio

from sentry_sdk import capture_exception


def addTaskCleanup(task):
    def exception_logging_done_cb(fut):
        try:
            e = fut.exception()
        except asyncio.CancelledError:
            return

        if e is not None:
            # Sentry
            capture_exception(e)

            # Normal exception business
            asyncio.get_event_loop().call_exception_handler({
                'message': 'Unhandled exception in async future',
                'future': fut,
                'exception': e,
            })

    task.add_done_callback(exception_logging_done_cb)
