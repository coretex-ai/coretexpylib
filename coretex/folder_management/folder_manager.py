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

from __future__ import annotations

from typing import Optional, Final, Union
from pathlib import Path
from threading import Lock

import os
import shutil


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
            this is deleted when the experiment has finished executing

        datasetsFolder : Path
            folder where datasets are stored (samples are symlinked for datasets)
        cache : Path
            folder where cache module stores items
        logs : Path
            folder where node and experiment logs are stored
        environments : Path
            folder where node stores python environments
    """

    __instanceLock = Lock()
    __instance: Optional[FolderManager] = None

    @classmethod
    def instance(cls) -> FolderManager:
        if cls.__instance is None:
            with cls.__instanceLock:
                if cls.__instance is None:
                    cls.__instance = cls()

        return cls.__instance

    def __init__(self) -> None:
        self._root: Final = Path(os.environ["CTX_STORAGE_PATH"]).expanduser()

        # These paths are str paths for backwards compatibility
        self.samplesFolder: Final = str(self.__createFolder("samples"))
        self.modelsFolder: Final = str(self.__createFolder("models"))
        self.temp: Final = str(self.__createFolder("temp"))

        # These paths are pathlib.Paths
        # pathlib is a std python library for handling paths
        self.datasetsFolder: Final = self.__createFolder("datasets")
        self.cache: Final = self.__createFolder("cache")
        self.logs: Final = self.__createFolder("logs")
        self.environments: Final = self.__createFolder("environments")

        self.__artifactsFolder: Final = self.__createFolder("artifacts")

    def createTempFolder(self, name: str) -> str:
        """
            Creates temp folder which is deleted once
            the experiment has finished executing

            Parameters
            ----------
            name : str
                name of the folder

            Returns
            -------
            str -> path to the created folder

            Raises
            ------
            FileExistsError -> if the temp folder already exists

            Example
            -------
            >>> from coretex.folder_management import FolderManager
            \b
            >>> dummyFolderPath = FolderManager.instance().createTempFolder("dummyTempFolder")
            >>> print(dummyFolderPath)
            "/Users/X/.coretex/temp/dummyTempFolder"
        """

        tempFolderPath = os.path.join(self.temp, name)

        if os.path.exists(tempFolderPath):
            raise FileExistsError

        os.mkdir(tempFolderPath)
        return tempFolderPath

    def getTempFolder(self, name: str) -> str:
        """
            Retrieves the path of the temp folder, does
            not check if the folder exists or not

            Parameters
            ----------
            name : str
                name of the folder

            Returns
            -------
            str -> path to the folder

            Example
            -------
            >>> from coretex.folder_management import FolderManager
            \b
            >>> dummyFolderPath = FolderManager.instance().getTempFolder("dummyTempFolder")
            >>> print(dummyFolderPath)
            "/Users/X/.coretex/temp/dummyTempFolder"
        """

        return os.path.join(self.temp, name)

    def getArtifactsFolder(self, experimentId: int) -> Path:
        """
            Retrieves the path to where the artifacts are stored
            for the specified experiment

            Parameters
            ----------
            experimentId : int
                id of the experiment

            Returns
            -------
            Path -> path to the experiment artifacts local storage

            Example
            -------
            >>> from coretex.folder_management import FolderManager
            \b
            >>> artifactsFolderPath = FolderManager.instance().getArtifactsFolder(1023)
            >>> print(artifactsFolderPath)
            Path("/Users/bogdanbm/.coretex/artifacts/1023")

        """

        return self.__artifactsFolder / str(experimentId)

    def clearTempFiles(self) -> None:
        """
            Deletes all temp files and folders (including artifacts)
        """

        self.__clearDirectory(self.temp)
        self.__clearDirectory(self.__artifactsFolder)

    def __createFolder(self, name: str) -> Path:
        path = self._root / name

        if not path.exists():
            path.mkdir(parents = True, exist_ok = True)

        return path

    def __clearDirectory(self, path: Union[Path, str]) -> None:
        for root, directories, files in os.walk(path):
            for file in files:
                os.unlink(os.path.join(root, file))

            for directory in directories:
                shutil.rmtree(os.path.join(root, directory))
