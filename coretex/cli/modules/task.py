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

from typing import Dict, Any, Tuple, List
from pathlib import Path
from zipfile import ZipFile

import os
import json

from ...entities import Task
from ...networking import networkManager, NetworkRequestError
from ...utils.misc import generateSha256Checksum


def pull(id: int) -> None:
    params = {
        "sub_project_id": id
    }

    zipFilePath = f"{id}.zip"
    response = networkManager.download(f"workspace/download", zipFilePath, params)

    if response.hasFailed():
        raise NetworkRequestError(response, ">> [Coretex] Task download has failed")

    with ZipFile(zipFilePath) as zipFile:
        zipFile.extractall(str(id))

    # remove zip file after extract
    os.unlink(zipFilePath)


def createMetadata(initialMetadataPath: Path, coretexMetadataPath: Path) -> None:
    with open(initialMetadataPath, "r") as initialMetadataFile:
        initialMetadata = json.load(initialMetadataFile)

        # if backend returns null for checksum of file, generate checksum
        for file in initialMetadata:
            if file["checksum"] is None:
                filePath = initialMetadataPath.parent.joinpath(file["path"])
                if filePath.exists():
                    file["checksum"] = generateSha256Checksum(filePath)

    newMetadata = {
        "checksums": initialMetadata
    }

    with open(coretexMetadataPath, "w") as coretexMetadataFile:
        json.dump(newMetadata, coretexMetadataFile, indent = 4)


def fillTaskMetadata(task: Task, initialMetadataPath: Path, coretexMetadataPath: Path) -> None:
    metadata = task.encode()

    with coretexMetadataPath.open("r") as coretexMetadataFile:
        existing_metadata = json.load(coretexMetadataFile)

    existing_metadata.update(metadata)

    with coretexMetadataPath.open("w") as coretexMetadataFile:
        json.dump(existing_metadata, coretexMetadataFile, indent=4)

    initialMetadataPath.unlink()


def checkMetadataDifference(remoteMetadata: list, coretexMetadataPath: Path) -> List[Dict[str, Any]]:
    with coretexMetadataPath.open("r") as localMetadataFile:
        localMetadata = json.load(localMetadataFile)

    localChecksums = {file['path']: file['checksum'] for file in localMetadata['checksums']}

    differences = []

    for remoteFile in remoteMetadata:
        remotePath = remoteFile['path']
        remoteChecksum = remoteFile['checksum']

        localChecksum = localChecksums.get(remotePath)

        if localChecksum != remoteChecksum:
            differences.append({
                'path': remotePath,
                'local_checksum': localChecksum,
                'remote_checksum': remoteChecksum
            })

    return differences
