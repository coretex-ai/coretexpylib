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

from typing import Optional, Any, Tuple, Union
from typing_extensions import Self
from pathlib import Path
from contextlib import ExitStack

from ..utils import guessMimeType


class FileData:

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

        if isinstance(filePath, str):
            filePath = Path(filePath)

        if fileName is None:
            fileName = filePath.stem

        if mimeType is None:
            mimeType = guessMimeType(filePath)

        return cls(parameterName, fileName, mimeType, filePath = filePath)

    @classmethod
    def createFromBytes(cls, parameterName: str, fileBytes: bytes, fileName: str) -> Self:
        return cls(parameterName, fileName, "application/octet-stream", fileBytes = fileBytes)

    def __getFileData(self, exitStack: ExitStack) -> Any:
        if self.fileBytes is not None:
            return self.fileBytes

        if self.filePath is not None:
            return exitStack.enter_context(self.filePath.open("rb"))

        raise ValueError(">> [Coretex] Either \"filePath\" or \"fileData\" have to provided for file upload. \"fileData\" will be used if both are provided")

    def prepareForUpload(self, exitStack: ExitStack) -> Tuple[str, Tuple[str, Any, str]]:
        return (self.parameterName, (self.fileName, self.__getFileData(exitStack), self.mimeType))
