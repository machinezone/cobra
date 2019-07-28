'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import time

from cobras.common.throttle import Throttle


def test_throttle():
    throttle = Throttle(1)
    assert not throttle.exceedRate()
    time.sleep(1)

    # FIXME(bug !)
    assert not throttle.exceedRate()

    # Second exceedRate should succeed, not third
    assert throttle.exceedRate()
