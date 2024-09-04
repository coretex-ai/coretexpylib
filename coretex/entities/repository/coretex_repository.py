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

from typing import Optional, List, Dict, Any
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


INITIAL_METADATA_PATH = Path(f"{id}/.metadata.json")
CORETEX_METADATA_PATH = Path(f"{id}/.coretex.json")


class EntityCoretexRepositoryType(IntEnum):

    task   = 1


class CoretexRepository(ABC, Codable):

    id: int
    projectId: int


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

        # remove zip file after extract
        os.unlink(zipFilePath)

        return not response.hasFailed()

    def getRemoteMetadata(self) -> List:
        params = {
            self.paramKey: self.id
        }

        response = networkManager.get(f"{self.endpoint}/metadata", params)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to fetch task metadata.")

        return response.getJson(list, force = True)

    def createMetadata(self) -> None:
        with open(INITIAL_METADATA_PATH, "r") as initialMetadataFile:
            initialMetadata = json.load(initialMetadataFile)

            # if backend returns null for checksum of file, generate checksum
            for file in initialMetadata:
                if file["checksum"] is None:
                    filePath = INITIAL_METADATA_PATH.parent.joinpath(file["path"])
                    if filePath.exists():
                        file["checksum"] = generateSha256Checksum(filePath)

        newMetadata = {
            "checksums": initialMetadata
        }

        with open(CORETEX_METADATA_PATH, "w") as coretexMetadataFile:
            json.dump(newMetadata, coretexMetadataFile, indent = 4)

    def fillMetadata(self) -> None:
        localMetadata: Dict[str, Any] = {}
        metadata = self.encode()

        with CORETEX_METADATA_PATH.open("r") as coretexMetadataFile:
            localMetadata = json.load(coretexMetadataFile)

        localMetadata.update(metadata)

        with CORETEX_METADATA_PATH.open("w") as coretexMetadataFile:
            json.dump(localMetadata, coretexMetadataFile, indent = 4)

        INITIAL_METADATA_PATH.unlink()

    def getDiff(self) ->  List[Dict[str, Any]]:
        with CORETEX_METADATA_PATH.open("r") as localMetadataFile:
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
