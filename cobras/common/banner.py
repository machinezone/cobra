import psutil
import os
import time
import platform
from cobras.common.version import getVersion


def getBanner():
    p = psutil.Process(os.getpid())
    createTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.create_time()))

    banner = r'''
   ___      _
  / __\___ | |__  _ __ __ _
 / /  / _ \| '_ \| '__/ _` |
/ /__| (_) | |_) | | | (_| |
\____/\___/|_.__/|_|  \__,_|

Cobra is a realtime messaging server using Python3, WebSockets and Redis.

Version {}
Running on {}
Start time {}
    '''.format(
        getVersion(), platform.uname().node, createTime
    )
    return banner
