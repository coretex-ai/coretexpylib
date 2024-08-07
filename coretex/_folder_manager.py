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
        samplesFolder : Path
            folder where samples are stored
        modelsFolder : Path
            folder where models are stored
        temp : Path
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
        """
            Creates temp folder which is deleted once
            the run has finished executing

            Parameters
            ----------
            name : str
                name of the folder

            Returns
            -------
            Path -> path to the created folder

            Raises
            ------
            FileExistsError -> if the temp folder already exists

            Example
            -------
            >>> from coretex import folder_manager
            \b
            >>> dummyFolderPath = folder_manager.createTempFolder("dummyTempFolder")
            >>> print(dummyFolderPath)
            "/Users/X/.coretex/temp/dummyTempFolder"
        """

        tempFolderPath = self.temp / name

        if tempFolderPath.exists():
            raise FileExistsError

        tempFolderPath.mkdir()
        return tempFolderPath

    def getArtifactsFolder(self, taskRunId: int) -> Path:
        """
            Retrieves the path to where the artifacts are stored
            for the specified TaskRuns

            Parameters
            ----------
            taskRunId : int
                id of the TaskRun

            Returns
            -------
            Path -> path to the TaskRun artifacts local storage

            Example
            -------
            >>> from coretex.folder_management import FolderManager
            \b
            >>> artifactsFolderPath = FolderManager.instance().getArtifactsFolder(1023)
            >>> print(artifactsFolderPath)
            Path("/Users/bogdanbm/.coretex/artifacts/1023")
        """

        return self._artifactsFolder / str(taskRunId)

    def clearDirectory(self, path: Path) -> None:
        shutil.rmtree(path)
        path.mkdir()

    def clearTempFiles(self) -> None:
        """
            Deletes all temp files and folders (including artifacts)
        """

        self.clearDirectory(self.temp)
        self.clearDirectory(self._artifactsFolder)

    def getRunLogsDir(self, taskRunId: int) -> Path:
        taskRunLogsDir = self.runsLogDirectory / str(taskRunId)
        taskRunLogsDir.mkdir(parents = True, exist_ok = True)

        return taskRunLogsDir

    @contextmanager
    def tempFile(self, name: Optional[str] = None) -> Iterator[Path]:
        """
            Returns a path to temporary file and deletes
            it if it exists once the context is exited.

            Parameters
            ----------
            name : Optional[str]
                Name of the file. If not specified a random uuid4
                will be generated and used as the name

            Returns
            -------
            Iterator[Path] -> path to the file
        """

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
