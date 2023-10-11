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

from typing import Any, Dict, List, Optional
from typing_extensions import Self

from ...networking import NetworkObject, networkManager, NetworkRequestError


class Secret(NetworkObject):

    @classmethod
    def _endpoint(cls) -> str:
        return "secret"

    def refresh(self, jsonObject: Optional[Dict[str, Any]] = None) -> bool:
        """
            Secret does not support this method
        """

        return NotImplemented

    def update(self, parameters: Dict[str, Any]) -> bool:
        """
            Secret does not support this method
        """

        return NotImplemented

    @classmethod
    def fetchById(cls, objectId: int, queryParameters: Optional[List[str]] = None) -> Self:
        """
            Secret does not support this method
        """

        return NotImplemented

    @classmethod
    def fetchByName(cls, name: str) -> Self:
        """
            Fetches a single Secret with the matching name

            Parameters
            ----------
            name : str
                name of the Secret which is fetched

            Returns
            -------
            Self -> fetched Secret

            Raises
            ------
            NetworkRequestError -> If the request for fetching failed
        """

        response = networkManager.get(f"{cls._endpoint()}/data", {
            "name": name
        })

        if response.hasFailed():
            raise NetworkRequestError(response, "Failed to fetch secret")

        return cls.decode(response.json)
