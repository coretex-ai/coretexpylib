#     Copyright (C) 2023  BioMech LLC

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
from ..network_sample import NetworkSample
from ....networking import networkManager, ChunkUploadSession, MAX_CHUNK_SIZE


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
        filePath: Union[Path, str],
        mimeType: Optional[str] = None
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
            filePath : str
                path to the sample
            mimeType : Optional[str]
                mime type of the file, if None mime type guessing will be performed

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

        uploadSession = ChunkUploadSession(MAX_CHUNK_SIZE, filePath, mimeType)
        uploadId = uploadSession.run()

        parameters = [
            ("name",       (None, name)),
            ("dataset_id", (None, datasetId)),
            ("file_id",    (None, uploadId))
        ]

        # files parameter can accept parameters that are not files, this way we can
        # send form-data requests without actual files
        response = networkManager.genericUpload("session/import", files = parameters)
        if response.hasFailed():
            return None

        return cls.decode(response.json)
