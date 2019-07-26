'''Compute our authentication hash with an hmac

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import base64
import hashlib
import hmac


def computeHash(secret: bytes, nonce: bytes) -> str:
    binary_hash = hmac.new(secret, nonce, hashlib.md5).digest()
    ascii_hash = base64.b64encode(binary_hash)

    h = ascii_hash.decode('ascii')

    # print(f'hmac({secret}, {nonce}) => {h}')
    return h
