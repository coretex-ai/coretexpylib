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

from .base import BaseObject
from ...codable import KeyDescriptor


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

        return cls.create(
            name = name,
            parent_id = projectId,
            description = description
        )
