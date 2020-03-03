'''Hash Slot computation (~crc16)

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.

First python version adapted from https://pypi.org/project/aredis/
and just kept the python code (no C module)

Second version adapted from justredis. (turns out binascii already has a crc16)
'''

from binascii import crc_hqx


def getHashSlot(keyStr):
    key = keyStr.encode()

    start = key.find(b"{")
    if start > -1:
        end = key.find(b"}", start + 1)
        if end > -1 and end != start + 1:
            begin = start + 1
            key = key[begin:end]

    return crc_hqx(key, 0) % 16384
