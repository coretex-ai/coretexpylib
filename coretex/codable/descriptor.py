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

from typing import Optional, Type, Final


class KeyDescriptor:

    """
        Defines how json filed should be represented in python
    """

    def __init__(
        self,
        jsonName: Optional[str] = None,
        pythonType: Optional[Type] = None,
        collectionType: Optional[Type] = None,
        isEncodable: bool = True,
        isDecodable: bool = True
    ) -> None:

        self.jsonName: Final = jsonName
        self.pythonType: Final = pythonType
        self.collectionType: Final = collectionType
        self.isEncodable: Final = isEncodable
        self.isDecodable: Final = isDecodable

    def isList(self) -> bool:
        """
            Checks if descriptor represents a list or not

            Returns
            -------
            bool -> True if it does, False otherwise
        """

        return self.collectionType is not None and issubclass(self.collectionType, list)
