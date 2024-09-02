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

from typing import Optional, Dict
from typing_extensions import Self
from zipfile import ZipFile

import os
import logging

from .base import BaseObject
from ..utils import isEntityNameValid
from ...codable import KeyDescriptor
from ...networking import networkManager, NetworkResponse


class Task(BaseObject):

    """
        Represents the task entity from Coretex.ai\n
        Contains properties that describe the task
    """

    isDefault: bool
    taskId: int

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["taskId"] = KeyDescriptor("parentId")

        return descriptors

    @classmethod
    def createTask(cls, name: str, projectId: int, description: Optional[str]=None) -> Optional[Self]:
        """
            Creates a new task with the provided name and description
            Task is added to the project with provided project id

            Parameters
            ----------
            name : str
                task name
            projectId : int
                project id the task belongs to
            description : Optional[str]
                task description

            Returns
            -------
            Optional[Self] -> The created task object

            Example
            -------
            >>> from coretex import Task
            \b
            >>> dummyTask = Task.createTask(
                    name = "dummyTask",
                    projectId = 23,
                    description = "This is dummy task"
                )
            >>> if dummyTask is None:
                    print("Failed to create task")
        """

        if not isEntityNameValid(name):
            raise ValueError(">> [Coretex] Task name is invalid. Requirements: alphanumeric characters (\"a-z\", and \"0-9\") and dash (\"-\") with length between 3 to 50")

        return cls.create(
            name = name,
            parent_id = projectId,
            description = description
        )

    def getMetadata(self) -> Optional[list]:
        params = {
            "sub_project_id": self.id
        }

        response = networkManager.get("workspace/metadata", params)

        if response.hasFailed():
            logging.getLogger("coretexpylib").error(">> [Coretex] Failed to fetch task metadata")
            return None

        return response.getJson(list, force = True)

    def pull(self) -> bool:
        params = {
            "sub_project_id": self.id
        }

        zipFilePath = f"{self.id}.zip"
        response = networkManager.download(f"workspace/download", zipFilePath, params)

        if response.hasFailed():
            logging.getLogger("coretexpylib").error(">> [Coretex] Task download has failed")
            return False

        with ZipFile(zipFilePath) as zipFile:
            zipFile.extractall(str(self.id))

        # remove zip file after extract
        os.unlink(zipFilePath)

        return not response.hasFailed()
