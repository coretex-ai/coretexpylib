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

from typing import Union
from pathlib import Path

from ...networking import NetworkResponse, NetworkRequestError, networkManager, ChunkUploadSession, MAX_CHUNK_SIZE
from ...utils import file as file_utils


def chunkSampleImport(
    name: str,
    datasetId: int,
    filePath: Union[Path, str]
) -> NetworkResponse:

    """
        Creates a new sample with specified properties\n
        When performing chunked sample import the provided
        path must be an archive

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
        NetworkResponse -> response of the session/import request

        Raises
        ------
        NetworkRequestError, ValueError -> if some kind of error happened during
        the upload of the provided file

        Example
        -------
        >>> from coretex import chunkSampleImport
        >>> chunkSampleImport("name", 1023, "path/to/archive.ext")
    """

    if isinstance(filePath, str):
        filePath = Path(filePath)

    if not file_utils.isArchive(filePath):
        raise ValueError(">> [Coretex] File must be a compressed archive [.zip, .tar.gz]")

    uploadSession = ChunkUploadSession(MAX_CHUNK_SIZE, filePath)
    uploadId = uploadSession.run()

    parameters = {
        "name": name,
        "dataset_id": datasetId,
        "file_id": uploadId
    }

    response = networkManager.formData("session/import", parameters)
    if response.hasFailed():
        raise NetworkRequestError(response, f"Failed to create sample from \"{filePath}\"")

    return response
