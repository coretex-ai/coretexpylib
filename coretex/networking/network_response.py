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

from typing import Union, Type, TypeVar, Optional, Iterator, Any
from http import HTTPStatus

from requests import Response
from requests.structures import CaseInsensitiveDict


JsonType = TypeVar("JsonType", bound = Union[list, dict])


class NetworkResponse:

    """
        Represents Coretex backend response to network request

        Properties
        ----------
        response : Response
            python.requests HTTP reponse
        endpoint : str
            endpoint to which the request was sent
    """

    def __init__(self, response: Response, endpoint: str):
        self._raw = response
        self.endpoint = endpoint

    @property
    def statusCode(self) -> int:
        """
            Status code of the HTTP response
        """

        return self._raw.status_code

    @property
    def headers(self) -> CaseInsensitiveDict:
        """
            HTTP Response headers
        """

        return self._raw.headers

    def hasFailed(self) -> bool:
        """
            Checks if request has failed

            Returns
            -------
            bool -> True if request has failed, False if request has not failed
        """

        return not self._raw.ok

    def isUnauthorized(self) -> bool:
        """
            Checks if request was unauthorized

            Returns
            -------
            bool -> True if status code is 401 and request has failed, False if not
        """

        return self.statusCode == HTTPStatus.UNAUTHORIZED and self.hasFailed()

    def getJson(self, type_: Type[JsonType]) -> JsonType:
        """
            Converts HTTP response body to json

            Parameters
            ----------
                type_: Type[JsonType]
                    list or dict types to which the json should be cast

            Returns
            -------
            JsonType -> Either a list or a dict object depending on type_ parameter

            Raises
            ------
            ValueError -> If "Content-Type" header was not "application/json"
            TypeError -> If it was not possible to convert body to type of passed "type_" parameter
        """

        if not "application/json" in self.headers.get("Content-Type", ""):
            raise ValueError(f">> [Coretex] Trying to convert request response to json but response \"Content-Type\" was \"{self.headers.get('Content-Type')}\"")

        value = self._raw.json()
        if not isinstance(value, type_):
            raise TypeError(f">> [Coretex] Expected json response to be of type \"{type_.__name__}\", received \"{type(value).__name__}\"")

        return value

    def getContent(self) -> bytes:
        """
            Returns
            -------
            bytes -> body of the request as bytes
        """

        return self._raw.content

    def stream(self, chunkSize: Optional[int] = 1, decodeUnicode: bool = False) -> Iterator[Any]:
        """
            Downloads HTTP response in chunks and returns them as they are being downloaded

            Parameters
            ----------
            chunkSize : Optional[int]
                A value of None will function differently depending on the value of stream.
                stream = True will read data as it arrives in whatever size the chunks are
                received. If stream = False, data is returned as a single chunk.
            decodeUnicode : bool
                If decode_unicode is True, content will be decoded using the best
                available encoding based on the response

            Returns
            -------
            Iterator[Any] -> HTTP response as chunks
        """

        return self._raw.iter_content(chunkSize, decodeUnicode)


class NetworkRequestError(Exception):

    """
        Exception which is raised when an request fails.
        Request is marked as failed when the http code is: >= 400
    """

    def __init__(self, response: NetworkResponse, message: str) -> None:
        if not response.hasFailed():
            raise ValueError(">> [Coretex] Invalid request response")

        try:
            # This will raise ValueError if response is not of type application/json
            # which is the case for response (mostly errors) returned by nginx which are html
            responseJson = response.getJson(dict)

            if "message" in responseJson:
                responseMessage = responseJson["message"]
            else:
                responseMessage = response._raw.content.decode()
        except ValueError:
            responseMessage = response._raw.content.decode()

        super().__init__(f">> [Coretex] {message}. Reason: {responseMessage}")

        self.response = response
