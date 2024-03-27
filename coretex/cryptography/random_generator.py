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

from cryptography.hazmat.primitives import hashes


class ByteBuffer:

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def update(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def get(self) -> int:
        if self.position >= len(self.data):
            raise OverflowError

        byte = self.data[self.position]
        self.position += 1

        return byte


class Random:

    def __init__(self, seed: bytes, algorithm: hashes.HashAlgorithm) -> None:
        self.algorithm = algorithm

        numberGenerator = hashes.Hash(algorithm)
        numberGenerator.update(seed)

        self._currentState = numberGenerator.finalize()
        self._buffer = ByteBuffer(self._currentState)

    def getRandomByte(self) -> int:
        try:
            return self._buffer.get()
        except OverflowError:
            # Raised when all bytes from current state have been exhausted
            # so we need to generate new bytes
            numberGenerator = hashes.Hash(self.algorithm)
            numberGenerator.update(self._currentState)

            self._currentState = numberGenerator.finalize()
            self._buffer.update(self._currentState)

            return self.getRandomByte()

    def getRandomBytes(self, count: int) -> bytes:
        values = bytearray(count)

        for i in range(count):
            values[i] = self.getRandomByte()

        return values
