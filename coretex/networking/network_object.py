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

from typing import Optional, Any, Dict, List
from typing_extensions import Self

import inflection

from .network_manager import networkManager
from .network_response import NetworkRequestError
from ..codable import Codable


DEFAULT_PAGE_SIZE = 100


class NetworkObject(Codable):

    """
        Base class for every Coretex.ai entity representation in Python

        Properties
        ----------
        id : int
            id of object
        isDeleted : bool
            boolean value that represents if object will be shown or not
    """

    id: int
    isDeleted: bool

    # Required init
    def __init__(self) -> None:
        pass

    @classmethod
    def _endpoint(cls) -> str:
        """
            Maps the entity endpoint to overriden value, else
            it uses inflection.underscode on the class name for endpoint

            Returns
            -------
            str -> Coretex.ai object endpoint for a given class
        """

        return inflection.underscore(cls.__name__)

    def entityUrl(self) -> str:
        """
            Maps the entity url to the frontend page url

            Returns
            -------
            str -> The URL path on Coretex for the entity.
        """

        return f"{type(self).__name__.lower()}/{self.id}"

    def __eq__(self, __o: object) -> bool:
        """
            Checks if the NetworkObjects which have id property
            defined are equal

            Parameter
            ---------
            __o : object
                object to which we are comparing self

            Returns
            -------
            bool -> True if ids are present and equal, False in any other case
        """

        # check if object parent class matches
        if isinstance(__o, NetworkObject):
            return self.id == __o.id

        return NotImplemented

    def __hash__(self) -> int:
        """
            Calculates hash of the object in a non-randomized manner

            Returns
            -------
            int -> hash of all the items defined on the self.__dict__ object
        """

        return hash(tuple(sorted(self.__dict__.items())))

    def refresh(self, jsonObject: Optional[Dict[str, Any]] = None) -> bool:
        """
            Updates objects fields to a provided value if set, otherwise
            fetches the object from the API and updates the values
            using the fetched object

            Parameters
            ----------
            jsonObject : Optional[Dict[str, Any]]
                A serialized json object to which the values should be updated, if provided

            Returns
            -------
            bool -> True if the update was successful, False otherwise
        """

        # Update from json if it exists
        if jsonObject is not None:
            self._updateFields(jsonObject)
            return True

        # Fetch from server otherwise
        try:
            obj = self.__class__.fetchById(self.id)
        except NetworkRequestError:
            return False

        for key, value in obj.__dict__.items():
            self.__dict__[key] = value

        return True

    def update(self, **kwargs: Any) -> bool:
        """
            Sends a PUT request to Coretex backend

            Parameters
            ----------
            **kwargs : Dict[str, Any]
                parameters which will be sent as request body

            Returns
            -------
            bool -> True if request was successful, False otherwise
        """

        if self.isDeleted:
            return False

        endpoint = f"{self._endpoint()}/{self.id}"
        return not networkManager.put(endpoint, kwargs).hasFailed()

    def delete(self) -> bool:
        """
            Sends a DELETE request to Coretex backend

            Returns
            -------
            bool -> True if request was successful, False otherwise
        """

        if self.isDeleted:
            return False

        endpoint = f"{self._endpoint()}/{self.id}"
        return not networkManager.delete(endpoint).hasFailed()

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        """
            Creates the entity linked to this class on Coretex backend

            Parameters
            ----------
            **kwargs : Dict[str, Any]
                parameters which will be sent as request body

            Returns
            -------
            Self -> created object if request was successful

            Raises
            ------
            NetworkRequestError -> If the request for creating failed
        """

        response = networkManager.post(cls._endpoint(), kwargs)
        if response.hasFailed():
            raise NetworkRequestError(response, f">> [Coretex] Failed to create \"{cls.__name__}\" with parameters \"{kwargs}\"")

        return cls.decode(response.getJson(dict))

    @classmethod
    def fetchAll(cls, **kwargs: Any) -> List[Self]:
        """
            Fetches all entities from Coretex backend which match
            the given predicate

            Parameters
            ----------
            **kwargs : Optional[Dict[str, Any]]
                query parameters (predicate) which will be appended to URL

            Returns
            -------
            List[Self] -> list of all fetched entities

            Raises
            ------
            NetworkRequestError -> If the request for fetching failed
        """

        if "page_size" not in kwargs:
            kwargs["page_size"] = DEFAULT_PAGE_SIZE

        response = networkManager.get(cls._endpoint(), kwargs)
        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to fetch \"{cls.__name__}\" with parameters \"{kwargs}\"")

        objects: List[Self] = []

        for obj in response.getJson(list):
            objects.append(cls.decode(obj))

        return objects

    @classmethod
    def fetchOne(cls, **kwargs: Any) -> Self:
        """
            Fetches one entity from Coretex backend which matches
            the given predicate

            Parameters
            ----------
            **kwargs : Optional[Dict[str, Any]]
                query parameters (predicate) which will be appended to URL

            Returns
            -------
            Self -> fetched entity

            Raises
            ------
            NetworkRequestError -> If the request for fetching failed
            ValueError -> If no object was fetched
        """

        kwargs["page_size"] = 1
        result = cls.fetchAll(**kwargs)

        if len(result) == 0:
            raise ValueError(f"Failed to fetch \"{cls.__name__}\" with parameters \"{kwargs}\"")

        return result[0]

    @classmethod
    def fetchById(cls, objectId: int, **kwargs: Any) -> Self:
        """
            Fetches a single entity with the matching id

            Parameters
            ----------
            objectId : int
                id of the object which is fetched
            **kwargs : Optional[Dict[str, Any]]
                query parameters (predicate) which will be appended to URL

            Returns
            -------
            Optional[Self] -> fetched object if request was successful, None otherwise

            Raises
            ------
            NetworkRequestError -> If the request for fetching failed
        """

        if "page_size" not in kwargs:
            kwargs["page_size"] = DEFAULT_PAGE_SIZE

        response = networkManager.get(f"{cls._endpoint()}/{objectId}", kwargs)

        if response.hasFailed():
            raise NetworkRequestError(response, f"Failed to fetch \"{cls.__name__}\" with ID \"{objectId}\"")

        return cls.decode(response.getJson(dict))
