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

from typing import Optional, Union
from typing_extensions import Self
from pathlib import Path

from .custom_sample_data import CustomSampleData
from .local_custom_sample import LocalCustomSample
from ..utils import chunkSampleImport
from ..network_sample import NetworkSample


class CustomSample(NetworkSample[CustomSampleData], LocalCustomSample):

    """
        Represents the custom Sample object from Coretex.ai\n
        Custom samples are used when working with Other Task\n
        Custom sample must be an archive
    """

    def __init__(self) -> None:
        NetworkSample.__init__(self)

    @classmethod
    def createCustomSample(
        cls,
        name: str,
        datasetId: int,
        filePath: Union[Path, str]
    ) -> Optional[Self]:
        """
            Creates a new custom sample with specified properties\n
            For creating custom sample, sample must be an archive

            Parameters
            ----------
            name : str
                sample name
            datasetId : int
                id of dataset to which the sample will be added
            filePath : Union[Path, str]
                path to the sample

            Returns
            -------
            Optional[Self] -> The created sample object or None if creation failed

            Raises
            ------
            NetworkRequestError, ValueError -> if some kind of error happened during
            the upload of the provided file

            Example
            -------
            >>> from coretex import CustomSample
            \b
            >>> sample = CustomSample.createCustomSample("name", 1023, "path/to/file")
            >>> if sample is None:
                    print("Failed to create custom sample")
        """

        response = chunkSampleImport(name, datasetId, filePath)
        return cls.decode(response.getJson(dict))
