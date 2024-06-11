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
from datetime import datetime

from .project_type import ProjectType
from ..utils import isEntityNameValid
from ...codable import KeyDescriptor
from ...networking import NetworkObject


class BaseObject(NetworkObject):

    """
        Represents the base class for Project/Task objects from Coretex.ai

        Properties
        ----------
        name : str
            name of object
        description : Optional[str]
            description of object
        createdOn : datetime
            date of creation of object
        createdById : str
            id of user that created object
        projectType : ProjectType
            project type of created object
    """

    name: str
    description: Optional[str]
    createdOn: datetime
    createdById: str
    projectType: ProjectType

    @classmethod
    def _endpoint(cls) -> str:
        return "project"

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["projectType"] = KeyDescriptor("project_task", ProjectType)

        return descriptors

    def rename(self, name: str) -> bool:
        """
            Renames the Project/Task

            Parameters
            ----------
            name : str
                new name

            Returns
            -------
            bool -> True if Project/Task was renamed, False if Project/Task was not renamed
        """

        if not isEntityNameValid(name):
            raise ValueError(">> [Coretex] Object name is invalid. Requirements: alphanumeric characters (\"a-z\", and \"0-9\") and dash (\"-\") with length between 3 to 50")

        if self.name == name:
            return False

        success = self.update(name = name)

        if success:
            self.name = name

        return success

    def updateDescription(self, description: str) -> bool:
        """
            Updates the Project/Task's description

            Parameters
            ----------
            description : str
                new description

            Returns
                bool -> True if Project/Task's description was updated,
                False if Project/Task's description was not updated
        """

        if self.description == description:
            return False

        success = self.update(description = description)
        if success:
            self.description = description

        return success
