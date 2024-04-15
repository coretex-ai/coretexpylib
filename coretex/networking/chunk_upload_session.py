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

import logging

from .network_manager_base import FileData
from .network_manager import networkManager
from .network_response import NetworkRequestError


MAX_CHUNK_SIZE = 128 * 1024 * 1024  # 128 MiB


def _loadChunk(filePath: Path, start: int, chunkSize: int) -> bytes:
    with filePath.open("rb") as file:
        file.seek(start)
        return file.read(chunkSize)


class ChunkUploadSession:

    """
        A class which splits a file into chunks and uploades it
        chunk by chunk. This class should be used for uploading
        files larger than 2 GiB, since Python does not support
        uploading files with a larger size.

        Maximum chunk size is 128 MiB.

        Properties
        ----------
        chunkSize : int
            size of chunks into which the file will be split
            maximum value is 128 MiB, while the minimum value is 1
        filePath : Union[Path, str]
            path to the file which will be uploaded
        fileSize : int
            size of the file which will be uploaded
    """

    def __init__(self, chunkSize: int, filePath: Union[Path, str]) -> None:
        if chunkSize <= 0 or chunkSize > MAX_CHUNK_SIZE:
            raise ValueError(f">> [Coretex] Invalid \"chunkSize\" value \"{chunkSize}\". Value must be in range 0-{MAX_CHUNK_SIZE}")

        if isinstance(filePath, str):
            filePath = Path(filePath)

        self.chunkSize = chunkSize
        self.filePath = filePath
        self.fileSize = filePath.lstat().st_size

    def __start(self) -> str:
        parameters = {
            "size": self.fileSize
        }

        response = networkManager.post("upload/start", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to start chunked upload for \"{self.filePath}\"")

        uploadId = response.getJson(dict).get("id")

        if not isinstance(uploadId, str):
            raise ValueError(f">> [Coretex] Invalid API response, invalid value \"{uploadId}\" for field \"id\"")

        return uploadId

    def __uploadChunk(self, uploadId: str, start: int, end: int) -> None:
        parameters = {
            "id": uploadId,
            "start": start,
            "end": end - 1  # API expects start/end to be inclusive
        }

        chunk = _loadChunk(self.filePath, start, self.chunkSize)
        files = [
            FileData.createFromBytes("file", chunk, self.filePath.name)
        ]

        response = networkManager.formData("upload/chunk", parameters, files)
        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to upload file chunk with byte range \"{start}-{end}\"")

        logging.getLogger("coretexpylib").debug(f">> [Coretex] Uploaded chunk with range \"{start}-{end}\"")

    def run(self) -> str:
        """
            Uploads the file to Coretex.ai

            Returns
            -------
            str -> ID of the uploaded file

            Raises
            ------
            NetworkRequestError, ValueError -> if some kind of error happened during
            the upload of the provided file

            Example
            -------
            >>> from coretex.networking import ChunkUploadSession, NetworkRequestError
            \b
            >>> chunkSize = 16 * 1024 * 1024  # chunk size: 16 MiB
            >>> uploadSession = ChunkUploadSession(chunkSize, path/fo/file.ext)
            \b
            >>> try:
                    uploadId = uploadSession.run()
                    print(uploadId)
                except NetworkRequestError, ValueError:
                    print("Failed to upload file")
        """
        logging.getLogger("coretexpylib").debug(f">> [Coretex] Starting upload for \"{self.filePath}\"")

        uploadId = self.__start()

        chunkCount = self.fileSize // self.chunkSize
        if self.fileSize % self.chunkSize != 0:
            chunkCount += 1

        for i in range(chunkCount):
            start = i * self.chunkSize
            end = min(start + self.chunkSize, self.fileSize)

            self.__uploadChunk(uploadId, start, end)

        return uploadId


def fileChunkUpload(path: Path, chunkSize: int = MAX_CHUNK_SIZE) -> str:
    """
        Uploads file in chunks to Coretex.ai server.
        Should be used when uploading large files.

        Parameters
        ----------
        path : Path
            File which will be uploaded in chunks
        chunkSize : int
            Size of the chunks into which file will be split
            before uploading. Maximum value is 128 MiBs

        Returns
        -------
        str -> id of the file which was uploaded
    """

    if not path.is_file():
        raise ValueError(f"{path} is not a file")

    if chunkSize > MAX_CHUNK_SIZE:
        chunkSize = MAX_CHUNK_SIZE

    uploadSession = ChunkUploadSession(MAX_CHUNK_SIZE, path)
    return uploadSession.run()
