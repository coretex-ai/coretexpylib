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

class DataBuffer:

    def __init__(self) -> None:
        self.data = bytearray()
        self.position = 0

    @property
    def remaining(self) -> int:
        return len(self.data) - self.position

    def append(self, data: bytes) -> None:
        """
            Appends new data to the end of the buffer

            Parameters
            ----------
            data : bytes
                data which will be appended
        """

        self.data.extend(data)

    def get(self) -> int:
        """
            Reads one byte from the buffer and increments
            its internal state by 1

            Returns
            -------
            int -> byte which was read

            Raises
            ------
            OverflowError -> if there are no more bytes to read
        """

        if len(self.data) <= self.position:
            raise OverflowError("All data was extracted from buffer")

        value = self.data[self.position]
        self.position += 1

        return value

    def getBytes(self, count: int) -> bytes:
        """
            Reads N number of bytes from the buffer and increments
            its internal state by N

            Parameters
            ----------
            count : int
                number of bytes to read

            Returns
            -------
            bytes -> bytes which were read

            Raises
            ------
            OverflowError -> if count exceeds number of available bytes
        """

        if len(self.data) < (self.position + count):
            raise OverflowError("Tried to extract more than than what the buffer has")

        values = self.data[self.position:self.position + count]
        self.position += count

        return values

    def getRemaining(self) -> bytes:
        """
            Reads remaining bytes from the buffer

            Returns
            -------
            bytes -> bytes which were read
        """

        remaining = len(self.data) - self.position
        return self.getBytes(remaining)
