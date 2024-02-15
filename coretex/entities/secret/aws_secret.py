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

from typing import Dict, Tuple

from .secret import Secret
from ...codable import KeyDescriptor


class AWSSecret(Secret):

    """
        Represents AWS Secret entity from Coretex.ai

        Properties
        ----------
        key : str
            AWS Access Key ID
        value : str
            AWS Secret Access Key
    """

    key: str
    value: str

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["value"] = KeyDescriptor("secret")

        return descriptors

    def _encryptedFields(self) -> Tuple[str, ...]:
        return ("key", "value")
