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

from typing import Dict, Any
from typing_extensions import override
from pathlib import Path

from .base import BaseCustomDataset
from ..network_dataset import NetworkDataset, _chunkSampleImport
from ...sample import CustomSample
from ....codable import KeyDescriptor


class CustomDataset(BaseCustomDataset, NetworkDataset[CustomSample]):

    """
        Custom Dataset class which is used for Other Task
        Represents the collection of archived samples
    """

    @override
    def __init__(self) -> None:
        super().__init__(CustomSample)

    @classmethod
    @override
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["samples"] = KeyDescriptor("sessions", CustomSample, list)

        return descriptors

    @override
    def _uploadSample(self, samplePath: Path, sampleName: str, **metadata: Any) -> CustomSample:
        return _chunkSampleImport(self._sampleType, sampleName, samplePath, self.id)
