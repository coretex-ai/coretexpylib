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

from enum import IntEnum
from typing import Optional, Dict, Any
from abc import abstractmethod, ABC

import re
import random
import logging

from ..networking import networkManager, NetworkRequestError


class EntityTagType(IntEnum):

    model   = 1
    dataset = 2


class Taggable(ABC):

    id: int
    projectId: int

    @property
    @abstractmethod
    def entityTagType(self) -> EntityTagType:
        pass

    def _getTagId(self, tagName: str) -> Optional[int]:
        parameters = {
            "name": tagName,
            "type": self.entityTagType.value,
            "project_id": self.projectId
        }

        response = networkManager.get("tag", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to check existing tags")

        tags = response.getJson(dict).get("data")
        if not isinstance(tags, list):
            raise NetworkRequestError(response, f"Field \"data\" from tag response must be dict, but got {type(tags)} instead")

        if len(tags) == 0:
            return None

        if not isinstance(tags[0], dict):
            raise NetworkRequestError(response, f"Tag object from response must be dict, but got {type(tags[0])} instead")

        tagId = tags[0].get("id")
        if not isinstance(tagId, int):
            raise NetworkRequestError(response, f"Tag object from response must have field id of type int, but got {type(tagId)} instead")

        return tagId


    def addTag(self, tag: str, color: Optional[str] = None) -> None:
        """
            Add a tag to this entity

            Parameters
            ----------
            tag : str
                name of the tag
            color : Optional[str]
                a hexadecimal color code for the new tag\n
                if tag already exists in project, this will be ignored\n
                if left empty and tag does not already exist, a random color will be picked

            Raises
            ------
            ValueError
                if tag name or color are invalid
            NetworkRequestError
                if request to add tag failed
        """

        if re.match(r"^[a-z0-9-]{1,30}$", tag) is None:
            raise ValueError(">> [Coretex] Tag has to be alphanumeric")

        if color is None:
            color = f"#{random.randint(0, 0xFFFFFF):06x}"
        else:
            if re.match(r"^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$", color) is None:
                raise ValueError(">> [Coretex] Tag color has to follow hexadecimal color code")

        tags: Dict[str, Any] = {}

        tagId = self._getTagId(tag)
        if tagId is not None:
            tags["existing"] = [tagId]
        else:
            tags["new"] = [{
                "name": tag,
                "color": color
            }]

        parameters = {
            "entity_id": self.id,
            "type": self.entityTagType.value,
            "tags": tags
        }

        response = networkManager.post("tag/entity", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create tag")

    def removeTag(self, tag: str) -> None:
        """
            Remove tag with provided name from the entity

            Parameters
            ----------
            tag : str
                name of the tag

            Raises
            ------
            NetworkRequestError
                if tag removal request failed
        """

        tagId = self._getTagId(tag)
        if tagId is None:
            logging.error(f">> [Coretex] Tag \"{tag}\" not found on entity id {self.id}")
            return

        parameters = {
            "entity_id": self.id,
            "tag_id": tagId,
            "type": self.entityTagType.value
        }

        response = networkManager.post("tag/remove", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to remove tag")
