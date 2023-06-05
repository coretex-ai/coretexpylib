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


class Project(BaseObject):

    """
        Represents the project entity from Coretex.ai\n
        Contains properties that describe the project
    """

    isDefault: bool
    projectId: int

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["projectId"] = KeyDescriptor("parentId")

        return descriptors

    @classmethod
    def createProject(cls, name: str, spaceId: int, description: Optional[str]=None) -> Optional[Self]:
        """
            Creates a new project with the provided name and description
            Project is added to the space with provided space id

            Parameters
            ----------
            name : str
                project name
            spaceId : int
                space id the project belongs to
            description : Optional[str]
                project description

            Returns
            -------
            Optional[Self] -> The created project object

            Example
            -------
            >>> from coretex import Project
            \b
            >>> dummyProject = Project.createProject(
                    name = "dummyProject",
                    spaceId = 23,
                    description = "This is dummy project"
                )
            >>> if dummyProject is None:
                    print("Failed to create project")
        """

        return cls.create(parameters={
            "name": name,
            "parent_id": spaceId,
            "description": description
        })
