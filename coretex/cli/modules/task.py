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

from zipfile import ZipFile

import os
import json

from ...entities import TaskRun
from ...networking import networkManager, NetworkRequestError


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


def createMetadata(id: int) -> None:
    with open(f"{id}/.metadata.json", "r") as initialMetadataFile:
        initialMetadata = json.load(initialMetadataFile)

    with open(f"{id}/.coretex.json", "w") as metadataFile:
        json.dump(initialMetadata, metadataFile, indent = 4)
