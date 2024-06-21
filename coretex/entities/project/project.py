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
from .project_visibility import ProjectVisibility
from ..entity_visibility_type import EntityVisibilityType
from ..utils import isEntityNameValid
from ...networking import networkManager, NetworkResponse, NetworkRequestError


class Project(BaseObject):

    """
        Represents the project entity from Coretex.ai\n
        Contains properties that describe the project
    """

    tasks: List[Task]
    visibility: ProjectVisibility

    @classmethod
    def createProject(
        cls,
        name: str,
        projectType: ProjectType,
        visiblity: ProjectVisibility = ProjectVisibility.private,
        description: Optional[str] = None
    ) -> Self:
        """
            Creates a new project with the provided name and description

            Parameters
            ----------
            name : str
                project name
            projectType : ProjectType
                type of the created Project
            visibility : ProjectVisibility
                visibility of the created Project
            description : Optional[str]
                project description

            Returns
            -------
            Self -> The created project object

            Raises
            ------
            NetworkRequestError -> If project creation failed

            Example
            -------
            >>> from coretex import Project, ProjectType
            \b
            >>> try:
            >>>     dummyProject = Project.createProject(
                        name = "dummyProject",
                        projectType = ProjectType.other,
                        description = "This is dummy Coretex Project"
                    )
                except:
                    print("Failed to create project.")
        """

        if not isEntityNameValid(name):
            raise ValueError(">> [Coretex] Project name is invalid. Requirements: alphanumeric characters (\"a-z\", and \"0-9\") and dash (\"-\") with length between 3 to 50")

        return cls.create(
            name = name,
            project_task = projectType,
            description = description,
            visiblity = visiblity
        )

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

    @classmethod
    def fetchByName(cls, name: str) -> Self:
        """
            Fetches Project based on specified name

            Parameters
            ----------
            name : str
                The name of the Project to fetch

            Returns
            -------
            Self -> Fetched Project

            Raises
            ------
            RuntimeError -> If the Project with specified name is not found
        """

        results = cls.fetchAll(name = f"={name}")
        if len(results) == 0:
            raise ValueError(f"Project with name \"{name}\" not found.")

        return results[0]

    def updateVisibility(self, visibility: ProjectVisibility) -> None:
        """
            Updates visibility of the project

            Parameters
            ----------
            visibility : ProjectVisibility
                visibility of the project

            Raises
            ------
            NetworkRequestError -> If request for updating the Project visibility failed
        """

        parameters = {
            "entity_id": self.id,
            "type": EntityVisibilityType.project,
            "visibility": visibility
        }

        response = networkManager.post("entity-visibility", parameters)

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to update visibility of the Project.")

        self.visibility = visibility
