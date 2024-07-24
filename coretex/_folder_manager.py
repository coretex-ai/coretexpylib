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

from typing import Iterator, Optional, Union
from pathlib import Path
from contextlib import contextmanager

import os
import shutil
import uuid


class FolderManager:

    """
        Used for handling everything related to local storage
        when working with Coretex

        Contains
        --------
        samplesFolder : str
            folder where samples are stored
        modelsFolder : str
            folder where models are stored
        temp : str
            folder where temp files and folders are stored,
            this is deleted when the run has finished executing

        datasetsFolder : Path
            folder where datasets are stored (samples are symlinked for datasets)
        cache : Path
            folder where cache module stores items
        logs : Path
            folder where node and run logs are stored
        environments : Path
            folder where node stores python environments
    """

    def __init__(self, storagePath: Union[Path, str]):
        if isinstance(storagePath, str):
            storagePath = Path(storagePath)

        self._root = storagePath.expanduser()

        self.samplesFolder = self._createFolder("samples")
        self.modelsFolder = self._createFolder("models")
        self.datasetsFolder = self._createFolder("datasets")
        self.cache = self._createFolder("cache")
        self.logs = self._createFolder("logs")
        self.environments = self._createFolder("environments")
        self.temp = self._createFolder("temp")
        self._artifactsFolder = self._createFolder("artifacts")

        self.runsLogDirectory = self.logs / "runs"
        self.runsLogDirectory.mkdir(exist_ok = True)

        self.coretexpylibLogs = self.logs / "coretexpylib"
        self.coretexpylibLogs.mkdir(exist_ok = True)

    def _createFolder(self, name: str) -> Path:
        path = self._root / name

        if not path.exists():
            path.mkdir(parents = True, exist_ok = True)

        return path

    def createTempFolder(self, name: str) -> Path:
        tempFolderPath = self.temp / name

        if tempFolderPath.exists():
            raise FileExistsError

        tempFolderPath.mkdir()
        return tempFolderPath

    def getArtifactsFolder(self, taskRunId: int) -> Path:
        return self._artifactsFolder / str(taskRunId)

    def clearDirectory(self, path: Path) -> None:
        shutil.rmtree(path)
        path.mkdir()

    def clearTempFiles(self) -> None:
        self.clearDirectory(self.temp)
        self.clearDirectory(self._artifactsFolder)

    def getRunLogsDir(self, taskRunId: int) -> Path:
        taskRunLogsDir = self.runsLogDirectory / str(taskRunId)
        taskRunLogsDir.mkdir(parents = True, exist_ok = True)

        return taskRunLogsDir

    @contextmanager
    def tempFile(self, name: Optional[str] = None) -> Iterator[Path]:
        if name is None:
            name = str(uuid.uuid4())

        path = self.temp / name
        if path.exists():
            raise FileExistsError(path)
        try:
            yield path
        finally:
            path.unlink(missing_ok = True)


folder_manager = FolderManager(os.environ["CTX_STORAGE_PATH"])


@contextmanager
def currentFolderManager(storagePath: Path) -> Iterator[None]:
    global folder_manager
    originalManager = folder_manager
    folder_manager = FolderManager(storagePath)
    try:
        yield None
    finally:
        folder_manager = originalManager
