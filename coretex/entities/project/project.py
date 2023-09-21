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

from typing import Optional, Any, List, Dict
from typing_extensions import Self

from .base import BaseObject
from .task import Task
from .project_type import ProjectType


class Project(BaseObject):

    """
        Represents the project entity from Coretex.ai\n
        Contains properties that describe the project
    """

    tasks: List[Task]

    @classmethod
    def createProject(cls, name: str, projectType: ProjectType, description: Optional[str] = None) -> Optional[Self]:
        """
            Creates a new project with the provided name and description

            Parameters
            ----------
            name : str
                project name
            description : Optional[str]
                project description

            Returns
            -------
            Optional[Self] -> The created project object

            Example
            -------
            >>> from coretex import Project, ProjectType
            \b
            >>> dummyProject = Project.createProject(
                    name = "dummyProject",
                    projectType = ProjectType.other,
                    description = "This is dummy Coretex Project"
                )
            >>> if dummyProject is None:
                    print("Failed to create project")
        """

        return cls.create(parameters={
            "name": name,
            "project_task": projectType.value,
            "description": description
        })

    @classmethod
    def decode(cls, encodedObject: Dict[str, Any]) -> Self:
        obj = super().decode(encodedObject)
        obj.tasks = Task.fetchAll(queryParameters=[
            f"parentId={obj.id}"
        ])

        return obj

    def addTask(self, name: str, description: Optional[str]) -> bool:
        """
            Adds new task to the project

            Parameters
            ----------
            name : str
                task name
            description : Optional[str]
                task description

            Returns
            -------
            bool -> True if the task was added. False if the task was not added
        """

        task = Task.createTask(name, self.id, description)
        if task is None:
            return False

        self.tasks.append(task)
        return True
