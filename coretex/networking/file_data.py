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

from typing import Optional, Tuple, Union, BinaryIO
from typing_extensions import Self
from pathlib import Path
from contextlib import ExitStack

from ..utils import guessMimeType


class FileData:

    """
        Class which describes file which will be uploaded
        using NetworkManager.genericUpload function.
        To upload a file either its "filePath" or "fileBytes"
        must be set, otherwise it will raise an exception.
        "filePath" will upload the file from the specified path, while
        "fileBytes" will upload the file directly from the memory.
        If both parameters have value "fileBytes" will be used.

        Objects of this class should not be instantiated directly,
        use either "FileData.createFromPath" or "FileData.createFromBytes"
        to instantiate the object.

        Properties
        ----------
        parameterName : str
            Name of the form-data parameter
        fileName : str
            Name of the file which will be uploaded
        mimeType : str
            Mime type of the file which will be uploaded
        filePath : Optional[str]
            Path to the file which will be uploaded
        fileBytes : Optional[bytes]
            Bytes of the file which will be uploaded
    """

    def __init__(
        self,
        parameterName: str,
        fileName: str,
        mimeType: str,
        filePath: Optional[Path] = None,
        fileBytes: Optional[bytes] = None
    ) -> None:

        if filePath is None and fileBytes is None:
            raise ValueError(">> [Coretex] Either \"filePath\" or \"fileData\" have to provided for file upload. \"fileData\" will be used if both are provided")

        self.parameterName = parameterName
        self.fileName = fileName
        self.mimeType = mimeType
        self.filePath = filePath
        self.fileBytes = fileBytes

    @classmethod
    def createFromPath(
        cls,
        parameterName: str,
        filePath: Union[Path, str],
        fileName: Optional[str] = None,
        mimeType: Optional[str] = None
    ) -> Self:

        """
            Creates "FileData" object from the specified file path. Use
            this function if you want to upload a file directly from path.

            Parameters
            ----------
            parameterName : str
                Name of the form-data parameter
            filePath : Union[Path, str]
                Path to the file which will be uploaded
            fileName : Optional[str]
                Name of the file which will be uploaded, if None it will
                be extracted from the "filePath" parameter
            mimeType : Optional[str]
                Mime type of the file which will be uploaded, if None it will
                be guessed. If it is not possible to guess an exception will be
                raised. In that case provide the mime type manually.

            Returns
            -------
            Self -> on object which describes how a path should be uploaded from path

            Raises
            ------
            ValueError -> if "filePath" is not a valid file
        """

        if isinstance(filePath, str):
            filePath = Path(filePath)

        if not filePath.is_file():
            raise ValueError(">> [Coretex] \"filePath\" is not a valid file")

        if fileName is None:
            fileName = filePath.stem

        if mimeType is None:
            mimeType = guessMimeType(filePath)

        return cls(parameterName, fileName, mimeType, filePath = filePath)

    @classmethod
    def createFromBytes(
        cls,
        parameterName: str,
        fileBytes: bytes,
        fileName: str,
        mimeType: Optional[str] = None
    ) -> Self:

        """
            Creates "FileData" object from the provided bytes. Use this
            function if you want to upload a file directly from memory.

            Parameters
            ----------
            parameterName : str
                Name of the form-data parameter
            fileBytes : bytes
                Bytes of the file which will be uploaded
            fileName : str
                Name of the file which will be uploaded, if None it will
                be extracted from the "filePath" parameter
            mimeType : Optional[str]
                Mime type of the file which will be uploaded, if None it will
                be set to "application/octet-stream".

            Returns
            -------
            Self -> on object which describes how a path should be uploaded from memory
        """

        if mimeType is None:
            mimeType = "application/octet-stream"

        return cls(parameterName, fileName, mimeType, fileBytes = fileBytes)

    def __getFileData(self, exitStack: ExitStack) -> Union[bytes, BinaryIO]:
        if self.fileBytes is not None:
            return self.fileBytes

        if self.filePath is not None:
            return exitStack.enter_context(self.filePath.open("rb"))

        raise ValueError(">> [Coretex] Either \"filePath\" or \"fileData\" have to provided for file upload. \"fileData\" will be used if both are provided")

    def prepareForUpload(self, exitStack: ExitStack) -> Tuple[str, Tuple[str, Union[bytes, BinaryIO], str]]:
        """
            Converts the "FileData" object into a format which can be used
            by the requests library for uploading files.

            Parameters
            ----------
            exitStack : ExitStack
                Context stack which contains the context of files
                opened by the "FileData" object. Used to join multiple file
                contexts, so if one raises an exception all the files will
                properly get closed.

            Returns
            -------
            Tuple[str, Tuple[str, Any, str]] -> Format accepted by the requests
            library for uploading files.
        """

        return self.parameterName, (self.fileName, self.__getFileData(exitStack), self.mimeType)
