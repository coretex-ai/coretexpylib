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

from typing import Generator
from pathlib import Path

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .constants import DEFAULT_CHUNK_SIZE, AES_KEY_SIZE, IV_SIZE, AES_BLOCK_SIZE
from .utils import DataBuffer


class StreamDecryptor:

    """
        Implements functionality for decrypting a stream of bytes
        using AES 256.
    """

    def __init__(self, key: bytes, iv: bytes, chunkSize: int = DEFAULT_CHUNK_SIZE) -> None:
        if len(key) != AES_KEY_SIZE:
            raise ValueError(f"AES key size: {len(key)}, but {AES_KEY_SIZE} expected")

        if len(iv) != IV_SIZE:
            raise ValueError(f"IV size: {len(iv)}, but {IV_SIZE} expected")

        self._key = key
        self._decryptor = Cipher(algorithms.AES256(self._key), modes.CBC(iv)).decryptor()
        self._buffer = DataBuffer()

        self.iv = iv
        self.chunkSize = chunkSize

    def feed(self, data: bytes) -> Generator[bytes, None, None]:
        """
            Decrypts the data using AES 256.

            Parameters
            ----------
            data : bytes
                data which should be decrypted

            Returns
            -------
            Generator[bytes, None, None] -> yields decrypted data in chunks
        """

        self._buffer.append(data)

        while self._buffer.remaining >= self.chunkSize:
            chunk = self._buffer.getBytes(self.chunkSize)
            yield self._decryptor.update(chunk)

    def flush(self) -> bytes:
        """
            Decrypts any remaining data using AES 256.

            Returns
            -------
            bytes -> decrypted data
        """

        # Decrypt chunk
        chunk = self._buffer.getRemaining()
        chunk = self._decryptor.update(chunk) + self._decryptor.finalize()

        # Unpad chunk
        try:
            unpadder = padding.PKCS7(AES_BLOCK_SIZE * 8).unpadder()
            return unpadder.update(chunk) + unpadder.finalize()
        except ValueError:
            # If unpadding failed either the key is wrong or
            # the padding was not performed during encryption
            # because ciphertext bytes were divisible by AES
            # block size so there was no need for padding
            return chunk


def decryptFile(key: bytes, sourcePath: Path, destinationPath: Path) -> None:
    """
        Decrypts a file using AES 256.

        Parameters
        ----------
        key : bytes
            key which will be used for decrypting
        sourcePath : Path
            path to the file which will be decrypted
        destinationPath : Path
            path to the decrypted file
    """

    with sourcePath.open("rb") as source, destinationPath.open("wb") as destination:
        iv = source.read(IV_SIZE)
        decryptor = StreamDecryptor(key, iv)

        while (chunk := source.read(DEFAULT_CHUNK_SIZE)):
            for decryptedData in decryptor.feed(chunk):
                destination.write(decryptedData)

        destination.write(decryptor.flush())
