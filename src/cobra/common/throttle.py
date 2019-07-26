'''Class to used to throttle function calls, so that something isn't called too
often

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

from datetime import datetime, timedelta


class Throttle(object):
    def __init__(self,
                 seconds: int = 1,
                 minutes: int = 0,
                 hours: int = 0) -> None:
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min

    def exceedRate(self) -> bool:
        now = datetime.now()
        time_since_last_call = now - self.time_of_last_call

        if time_since_last_call > self.throttle_period:
            self.time_of_last_call = now
            return False
        else:
            return True
