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

from pathlib import Path

import os
import shutil

from .utils import file as file_utils


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


def _createFolder(name: str) -> Path:
    path = _root / name

    if not path.exists():
        path.mkdir(parents = True, exist_ok = True)

    return path


_root = Path(os.environ["CTX_STORAGE_PATH"]).expanduser()

samplesFolder    = _createFolder("samples")
modelsFolder     = _createFolder("models")
datasetsFolder   = _createFolder("datasets")
cache            = _createFolder("cache")
logs             = _createFolder("logs")
environments     = _createFolder("environments")
temp             = _createFolder("temp")
_artifactsFolder = _createFolder("artifacts")

runsLogDirectory = logs / "runs"
runsLogDirectory.mkdir(exist_ok = True)

coretexpylibLogs = logs / "coretexpylib"
coretexpylibLogs.mkdir(exist_ok = True)


def createTempFolder(name: str) -> Path:
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

    tempFolderPath = temp / name

    if tempFolderPath.exists():
        raise FileExistsError

    tempFolderPath.mkdir()
    return tempFolderPath


def getArtifactsFolder(taskRunId: int) -> Path:
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

    return _artifactsFolder / str(taskRunId)


def clearDirectory(path: Path) -> None:
    for element in file_utils.walk(path):
        if element.is_file():
            element.unlink()

        if element.is_dir():
            shutil.rmtree(element)


def clearTempFiles() -> None:
    """
        Deletes all temp files and folders (including artifacts)
    """

    clearDirectory(temp)
    clearDirectory(_artifactsFolder)


def getRunLogsDir(taskRunId: int) -> Path:
    taskRunLogsDir = runsLogDirectory / str(taskRunId)
    taskRunLogsDir.mkdir(parents = True, exist_ok = True)

    return taskRunLogsDir
