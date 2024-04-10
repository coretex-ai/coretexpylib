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

from typing import Optional, Generator
from pathlib import Path

import os

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .constants import DEFAULT_CHUNK_SIZE, AES_KEY_SIZE, IV_SIZE, AES_BLOCK_SIZE
from .utils import DataBuffer


class StreamEncryptor:

    """
        Implements functionality for encrypting a stream of bytes
        using AES 256.
    """

    def __init__(self, key: bytes, iv: Optional[bytes] = None, chunkSize: int = DEFAULT_CHUNK_SIZE) -> None:
        if len(key) != AES_KEY_SIZE:
            raise ValueError(f"AES key size: {len(key)}, but {AES_KEY_SIZE} expected")

        if iv is None:
            # generate random secure IV (initialization vector) if one wasn't provided
            iv = os.urandom(IV_SIZE)

        if len(iv) != IV_SIZE:
            raise ValueError(f"IV size: {len(iv)}, but {IV_SIZE} expected")

        self._key = key
        self._encryptor = Cipher(algorithms.AES256(self._key), modes.CBC(iv)).encryptor()
        self._buffer = DataBuffer()

        self.iv = iv
        self.chunkSize = chunkSize

    def feed(self, data: bytes) -> Generator[bytes, None, None]:
        """
            Encrypts the data using AES 256.

            Parameters
            ----------
            data : bytes
                data which should be encrypted

            Returns
            -------
            Generator[bytes, None, None] -> yields encrypted data in chunks
        """

        self._buffer.append(data)

        while self._buffer.remaining >= self.chunkSize:
            chunk = self._buffer.getBytes(self.chunkSize)
            yield self._encryptor.update(chunk)

    def flush(self) -> bytes:
        """
            Encrypts any remaining data using AES 256.

            Returns
            -------
            bytes -> encrypted data
        """

        chunk = self._buffer.getRemaining()

        # Pad the data if needed
        if len(chunk) % AES_BLOCK_SIZE != 0:
            padder = padding.PKCS7(AES_BLOCK_SIZE * 8).padder()
            chunk = padder.update(chunk) + padder.finalize()

        return self._encryptor.update(chunk) + self._encryptor.finalize()


def encryptFile(key: bytes, sourcePath: Path, destinationPath: Path) -> None:
    """
        Encrypts a file using AES 256. IV gets stored as the first 16 bytes
        of the encrypted file. IV is generated using "os.urandom".

        Parameters
        ----------
        key : bytes
            key which will be used for encrypting
        sourcePath : Path
            path to the file which will be encrypted
        destinationPath : Path
            path to the encrypted file

        Raises
        ------
        RuntimeError -> if file size % AES_BLOCK_SIZE has remainder
    """

    with sourcePath.open("rb") as source, destinationPath.open("wb") as destination:
        encryptor = StreamEncryptor(key)
        destination.write(encryptor.iv)

        while (chunk := source.read(DEFAULT_CHUNK_SIZE)):
            for encryptedData in encryptor.feed(chunk):
                destination.write(encryptedData)

        destination.write(encryptor.flush())

    if destinationPath.stat().st_size % AES_BLOCK_SIZE != 0:
        raise RuntimeError("File was corrupted during encryption")
