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
from typing import Optional

import re
import random
import logging

from ..networking import networkManager, NetworkRequestError


class EntityTagType(IntEnum):

    model   = 1
    dataset = 2


class Taggable:

    def _getTagId(self, tagName: str, projectId: int, entityTypeEnum: int) -> Optional[int]:
        parameters = {
            "name": tagName,
            "type": int(entityTypeEnum),
            "project_id": projectId,
        }

        response = networkManager.get("tag", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to check existing tags")

        tags = response.getJson(dict)["data"]
        if len(tags) == 0:
            return None

        tagId: int = tags[0]["id"]

        return tagId


    def addTagToEntity(self, tag: str, entityId: int, projectId: int, entityTypeEnum: int, color: Optional[str] = None) -> None:
        if re.match(r"^[a-z0-9-]{1,10}$", tag) is None:
            raise ValueError(">> [Coretex] Tag has to be alphanumeric")

        if color is None:
            color = f"#{random.randint(0, 0xFFFFFF):06x}"
        else:
            if re.match(r'^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$', color) is None:
                raise ValueError(">> [Coretex] Tag color has to follow hexadecimal color code")

        parameters = {
            "entity_id": entityId,
            "type": entityTypeEnum,
            "tags": {}
        }

        tagId = self._getTagId(tag, projectId, entityTypeEnum)
        if tagId is not None:
            parameters["tags"]["existing"] = [tagId]  # type: ignore[index]
        else:
            parameters["tags"]["new"] = [{  # type: ignore[index]
                "name": tag,
                "color": color
            }]

        response = networkManager.post("tag/entity", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to create tag")

    def removeTagFromEntity(self, tag: str, entityId: int, projectId: int, entityTypeEnum: int) -> None:
        tagId = self._getTagId(tag, projectId, entityTypeEnum)
        if tagId is None:
            logging.error(f">> [Coretex] Tag \"{tag}\" not found on entity id {entityId}")
            return

        parameters = {
            "entity_id": entityId,
            "tag_id": tagId,
            "type": entityTypeEnum
        }

        response = networkManager.post("tag/remove", parameters)
        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to remove tag")
