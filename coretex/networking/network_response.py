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

from typing import Final
from enum import IntEnum

import logging

from requests import Response


class HttpCode(IntEnum):

    """
        A enum class which represents code for specific http errors
    """

    unauthorized        = 401

    internalServerError = 500
    serviceUnavailable  = 503


class NetworkResponse:

    """
        Represents Coretex backend response to network request

        Properties
        ----------
        response : Response
            API response
        endpoint : endpoint
            name of API endpoint
        json : Any
            response in json format

    """

    def __init__(self, response: Response, endpoint: str):
        self.raw: Final = response
        self.headers: Final = response.headers

        try:
            self.json = response.json()
        except ValueError:
            self.json = {}

        if not response.ok:
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Request failed: (Endpoint: {endpoint}, Code: {response.status_code}, Message: {response.text})")

        logging.getLogger("coretexpylib").debug(f">> [Coretex] Request response: {self.json}")

    @property
    def statusCode(self) -> int:
        return self.raw.status_code

    def hasFailed(self) -> bool:
        """
            Checks if request has failed

            Returns
            -------
            bool -> True if request has failed, False if request has not failed
        """

        return not self.raw.ok

    def isUnauthorized(self) -> bool:
        """
            Checks if request was unauthorized

            Returns
            -------
            bool -> True if status code is 401 and request has failed, False if not
        """

        return self.statusCode == HttpCode.unauthorized and self.hasFailed()


class NetworkRequestError(Exception):

    """
        Exception which is raised when an request fails.
        Request is marked as failed when the http code is: >= 400
    """

    def __init__(self, response: NetworkResponse, message: str) -> None:
        if not response.hasFailed():
            raise RuntimeError(">> [Coretex] Invalid request response")

        if "message" in response.json:
            responseMessage = response.json["message"]
        else:
            responseMessage = response.raw.text

        super().__init__(f">> [Coretex] {message}. Reason: {responseMessage}")

        self.response: Final = response
