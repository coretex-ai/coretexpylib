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

from typing import List, Dict, Any
from enum import IntEnum
from abc import abstractmethod, ABC
from pathlib import Path
from zipfile import ZipFile

import os
import json
import logging

from ...codable import Codable
from ...utils import generateSha256Checksum
from ...networking import networkManager, NetworkRequestError


def checkIfCoretexRepoExists() -> bool:
    print(Path.cwd().joinpath(".coretex"))
    return Path.cwd().joinpath(".coretex").exists()


class EntityCoretexRepositoryType(IntEnum):

    task   = 1


class CoretexRepository(ABC, Codable):

    id: int
    projectId: int

    @property
    def __initialMetadataPath(self) -> Path:
        return Path(f"{self.id}/.metadata.json")

    @property
    def coretexMetadataPath(self) -> Path:
        return Path(f"{self.id}/.coretex.json")

    @property
    @abstractmethod
    def entityCoretexRepositoryType(self) -> EntityCoretexRepositoryType:
        pass

    @property
    @abstractmethod
    def paramKey(self) -> str:
        pass

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    def pull(self) -> bool:
        params = {
            self.paramKey: self.id
        }

        zipFilePath = f"{self.id}.zip"
        response = networkManager.download(f"{self.endpoint}/download", zipFilePath, params)

        if response.hasFailed():
            logging.getLogger("coretexpylib").error(f">> [Coretex] {self.entityCoretexRepositoryType.name.capitalize()} download has failed")
            return False

        with ZipFile(zipFilePath) as zipFile:
            zipFile.extractall(str(self.id))

        os.unlink(zipFilePath)

        return not response.hasFailed()

    def getRemoteMetadata(self) -> List:
        # getRemoteMetadata downloads only .metadata file, this was needed so we can
        # synchronize changes if multiple people work on the same Entity at the same time

        params = {
            self.paramKey: self.id
        }

        response = networkManager.get(f"{self.endpoint}/metadata", params)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to fetch task metadata.")

        return response.getJson(list, force = True)

    def createMetadata(self) -> None:
        # createMetadata() function will store metadata of files that backend returns
        # currently all files on backend (that weren't uploaded after checksum calculation change
        # for files that is implemented recently on backend) return null/None for their checksum
        # if backend returns None for checksum of some file we need to calculate initial checksum of
        # the file so we can track changes

        with self.__initialMetadataPath.open("r") as initialMetadataFile:
            initialMetadata = json.load(initialMetadataFile)

            # if backend returns null for checksum of file, generate checksum
            for file in initialMetadata:
                if file["checksum"] is None:
                    filePath = self.__initialMetadataPath.parent.joinpath(file["path"])
                    if filePath.exists():
                        file["checksum"] = generateSha256Checksum(filePath)

        newMetadata = {
            "checksums": initialMetadata
        }

        with self.coretexMetadataPath.open("w") as coretexMetadataFile:
            json.dump(newMetadata, coretexMetadataFile, indent = 4)

    def fillMetadata(self) -> None:
        # fillMetadata() function will update initial metadata returned from backend
        # (file paths and their checksums) with other important Entity info (e.g. name, id, description...)

        localMetadata: Dict[str, Any] = {}
        metadata = self.encode()

        with self.coretexMetadataPath.open("r") as coretexMetadataFile:
            localMetadata = json.load(coretexMetadataFile)

        localMetadata.update(metadata)

        with self.coretexMetadataPath.open("w") as coretexMetadataFile:
            json.dump(localMetadata, coretexMetadataFile, indent = 4)

        self.__initialMetadataPath.unlink()

    def getDiff(self) ->  List[Dict[str, Any]]:
        # getDiff() checks initial checksums of files stored in .coretex file
        # and compares them with their current checksums, based on that we know what files have changes

        with self.coretexMetadataPath.open("r") as localMetadataFile:
            localMetadata = json.load(localMetadataFile)

        localChecksums = {file["path"]: file["checksum"] for file in localMetadata["checksums"]}

        differences = []

        remoteMetadata = self.getRemoteMetadata()
        for remoteFile in remoteMetadata:
            remotePath = remoteFile["path"]
            remoteChecksum = remoteFile["checksum"]

            localChecksum = localChecksums.get(remotePath)

            if localChecksum != remoteChecksum:
                differences.append({
                    "path": remotePath,
                    "local_checksum": localChecksum,
                    "remote_checksum": remoteChecksum
                })

        return differences
