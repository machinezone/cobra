'''256 bits AES encryption

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import base64

import pyaes


def encrypt(plaintext: str, key: str) -> str:
    key = key.zfill(32)
    aes = pyaes.AESModeOfOperationCTR(key.encode())
    cipher = aes.encrypt(plaintext.encode())
    encoded = base64.b64encode(cipher).decode()  # make it a string
    return encoded


def decrypt(ciphertext: str, key: str) -> str:
    if key is None:
        return f'<cannot decrypt: {ciphertext} -> Missing password>'

    key = key.zfill(32)
    aes = pyaes.AESModeOfOperationCTR(key.encode())
    try:
        binary = base64.b64decode(ciphertext)
        plaintext = aes.decrypt(binary).decode()
        return plaintext
    except Exception as e:
        return f'<cannot decrypt: {ciphertext} -> {e}>'
