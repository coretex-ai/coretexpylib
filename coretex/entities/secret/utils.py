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
    """
        Hashes the provided value using SHA256 hashing algorithm.

        Parameters
        ----------
        value : bytes
            Value which will be hashed

        Returns
        -------
        bytes -> Hashed value
    """

    return hashlib.sha256(value).digest()


def getKey() -> bytes:
    """
        Retrieves secrets key stored in "CTX_SECRETS_KEY"
        environment variable. This key is used for decrypting
        Coretex Secrets.

        Returns
        -------
        bytes -> Hashed secrets key
    """

    if not "CTX_SECRETS_KEY" in os.environ:
        raise RuntimeError("Secret encryption key not found")

    key = os.environ["CTX_SECRETS_KEY"]
    return sha256(key.encode())


def decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    """
        Decrypts data encrypted using AES in CBC
        mode with PKCS7 padding.

        Parameters
        ----------
        key : bytes
            Key which will be used for decryption. Must be a
            valid AES key (128, 192, or 256 bits) otherwise an
            error will be raised.
        iv : bytes
            Initialization vector used for randomizing the input
            data of the encryption. Must be 16 bytes long.
        data : bytes
            Data which will be decrypted.

        Returns
        -------
        bytes -> Decrypted data
    """

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
    """
        Decrypts Coretex Secret value.

        Parameters
        ----------
        value : str
            A concatenated base64 string of IV and cipher.
            Both values must be encoded with base64 and concatenated.

        Returns
        -------
        str -> Decrypted value of Coretex Secret
    """

    iv = base64.b64decode(value[:24])
    data = base64.b64decode(value[24:])

    return decrypt(getKey(), iv, data).decode()
