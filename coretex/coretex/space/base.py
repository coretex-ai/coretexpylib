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

from .space_task import SpaceTask
from ...codable import KeyDescriptor
from ...networking import NetworkObject


class BaseObject(NetworkObject):

    """
        Represents the base class for Space/Project objects from Coretex.ai

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
        spaceTask : SpaceTask
            space task of created object
    """

    name: str
    description: Optional[str]
    createdOn: datetime
    createdById: str
    spaceTask: SpaceTask

    @classmethod
    def _endpoint(cls) -> str:
        return "project"

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["spaceTask"] = KeyDescriptor("project_task", SpaceTask)

        return descriptors

    def rename(self, name: str) -> bool:
        """
            Renames the Space/Project

            Parameters
            ----------
            name : str
                new name

            Returns
            -------
            bool -> True if Space/Project was renamed, False if Space/Project was not renamed
        """

        if self.name == name:
            return False

        success = self.update(
            parameters = {
                "name": name
            }
        )

        if success:
            self.name = name

        return success

    def updateDescription(self, description: str) -> bool:
        """
            Updates the Space/Project's description

            Parameters
            ----------
            description : str
                new description

            Returns
                bool -> True if Space/Project's description was updated,
                False if Space/Project's description was not updated
        """

        if self.description == description:
            return False

        success = self.update(
            parameters = {
                "description": description
            }
        )

        if success:
            self.description = description

        return success
