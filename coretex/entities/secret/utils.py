#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import base64
import hashlib
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def sha256(value: bytes) -> bytes:
    return hashlib.sha256(value).digest()


def getKey() -> bytes:
    if not "CTX_SECRET_KEY" in os.environ:
        raise RuntimeError("Secret encryption key not found")

    key = os.environ["CTX_SECRET_KEY"]
    return sha256(key.encode())


def decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend = default_backend()
    )

    decryptor = cipher.decryptor()
    padded = decryptor.update(data) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def decryptSecretValue(value: str) -> str:
    iv = base64.b64decode(value[:24])
    data = base64.b64decode(value[24:])

    return decrypt(getKey(), data, iv).decode()
