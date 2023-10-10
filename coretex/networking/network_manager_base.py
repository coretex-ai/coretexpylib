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

from typing import Optional, Any, Dict, List, Union, Tuple
from pathlib import Path
from abc import ABC, abstractmethod
from contextlib import ExitStack
from importlib.metadata import version as getLibraryVersion

import os
import logging
import platform
import requests

from .request_type import RequestType
from .network_response import HttpCode, NetworkResponse
from .file_data import FileData


RequestBodyType = Union[Dict[str, Any], List[Dict[str, Any]]]
RequestFormType = List[Tuple[str, Tuple[str, Any, str]]]

MAX_RETRY_COUNT = 3


class RequestFailedError(Exception):

    def __init__(self, endpoint: str, type_: RequestType) -> None:
        super().__init__(f">> [Coretex] \"{type_.name}\" request failed for endpoint \"{endpoint}\"")


class NetworkManagerBase(ABC):

    def __init__(self) -> None:
        self._session = requests.Session()

        # Override NetworkManager to update values
        self.loginEndpoint: str = "user/login"
        self.refreshEndpoint: str = "user/refresh"

        self.apiTokenHeaderField: str = "api-token"

        self.apiTokenKey: str = "token"
        self.refreshTokenKey: str = "refresh_token"

    @property
    def serverUrl(self) -> str:
        return os.environ["CTX_API_URL"]

    @property
    @abstractmethod
    def _apiToken(self) -> Optional[str]:
        pass

    @_apiToken.setter
    @abstractmethod
    def _apiToken(self, value: Optional[str]) -> None:
        pass

    @property
    @abstractmethod
    def _refreshToken(self) -> Optional[str]:
        pass

    @_refreshToken.setter
    @abstractmethod
    def _refreshToken(self, value: Optional[str]) -> None:
        pass

    @property
    def userAgent(self) -> str:
        coretexpylibVersion = getLibraryVersion("coretex")
        return f"coretexpylib;{coretexpylibVersion};python;{platform.python_version()}"

    @property
    def hasStoredCredentials(self) -> bool:
        """
            To use this functions call it using coretex.networking.networkManager

            Raises
            ------
            NotImplementedError
        """

        raise NotImplementedError

    def _headers(self, contentType: str = "application/json") -> Dict[str, str]:
        header = {
            "Content-Type": contentType,
            "Connection": "keep-alive",
            "X-User-Agent": self.userAgent
        }

        if self._apiToken is not None:
            header[self.apiTokenHeaderField] = self._apiToken

        return header

    def request(
        self,
        endpoint: str,
        requestType: RequestType,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[RequestBodyType] = None,
        files: Optional[RequestFormType] = None,
        auth: Optional[Tuple[str, str]] = None,
        stream: bool = False,
        retryCount: int = 0
    ) -> NetworkResponse:

        if headers is None:
            headers = self._headers()

        url = self.serverUrl + endpoint

        try:
            rawResponse = self._session.request(
                requestType.value,
                url,
                params = query,
                json = body,
                auth = auth,
                files = files,
                headers = headers
            )

            response = NetworkResponse(rawResponse, endpoint)
            if self.shouldRetry(retryCount, response):
                return self.request(endpoint, requestType, headers, query, body, files, auth, stream, retryCount + 1)

            return response
        except:
            if self.shouldRetry(retryCount, None):
                return self.request(endpoint, requestType, headers, query, body, files, auth, stream, retryCount + 1)

            raise RequestFailedError(endpoint, requestType)

    def post(self, endpoint: str, params: Optional[RequestBodyType] = None) -> NetworkResponse:
        return self.request(endpoint, RequestType.post, body = params)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> NetworkResponse:
        return self.request(endpoint, RequestType.get, query = params)

    def put(self, endpoint: str, params: Optional[RequestBodyType] = None) -> NetworkResponse:
        return self.request(endpoint, RequestType.put, body = params)

    def delete(self, endpoint: str) -> NetworkResponse:
        return self.request(endpoint, RequestType.delete)

    def formData(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[List[FileData]] = None
    ) -> NetworkResponse:

        if files is None:
            files = []

        with ExitStack() as stack:
            filesData = [file.prepareForUpload(stack) for file in files]

        headers = self._headers("multipart/form-data")
        return self.request(endpoint, RequestType.post, headers, body = params, files = filesData)

    def authenticate(self, username: str, password: str, storeCredentials: bool = True) -> NetworkResponse:
        """
            Authenticates user with provided credentials

            Parameters
            ----------
            username : str
                Coretex.ai username
            password : str
                Coretex.ai password
            storeCredentials : bool
                If true credentials will be stored in User object for reuse,
                ignored for all managers except coretex.networking.networkManager

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Example
            -------
            >>> from coretex.networking import networkManager
            \b
            >>> response = networkManager.authenticate(username = "dummy@coretex.ai", password = "123456")
            >>> if response.hasFailed():
                    print("Failed to authenticate")
        """

        # authenticate using credentials stored in requests.Session.auth

        response = self.request(self.loginEndpoint, RequestType.post, auth = (username, password))

        if self.apiTokenKey in response.json:
            self._apiToken = response.json[self.apiTokenKey]

        if self.refreshTokenKey in response.json:
            self._refreshToken = response.json[self.refreshTokenKey]

        return response

    def authenticateWithStoredCredentials(self) -> NetworkResponse:
        """
            To use this functions call it using coretex.networking.networkManager

            Raises
            ------
            NotImplementedError
        """

        raise NotImplementedError

    def authenticateWithRefreshToken(self, token: str) -> NetworkResponse:
        """
            Authenticates user with provided refresh token

            Parameters
            ----------
            token : str
                refresh token

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info
        """

        self._refreshToken = token
        return self.refreshToken()

    def download(
        self,
        endpoint: str,
        destination: Union[Path, str],
        params: Optional[Dict[str, Any]] = None
    ) -> NetworkResponse:

        """
            Downloads file to the given destination

            Parameters
            ----------
            endpoint : str
                API endpoint
            destination : Union[Path, str]
                path to save file

            Returns
            -------
            NetworkResponse as response content to request

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.genericDownload(
                    endpoint = "dummyObject/download",
                    destination = "path/to/destination/folder"
                )
            >>> if response.hasFailed():
                    print("Failed to download the file")
        """

        if isinstance(destination, str):
            destination = Path(destination)

        response = self.get(endpoint, params)
        if response.hasFailed():
            return response

        with destination.open("wb") as downloadedFile:
            downloadedFile.write(response.raw.content)

        return response

    def streamDownload(
        self,
        endpoint: str,
        destination: Union[Path, str],
        params: Optional[Dict[str, Any]] = None
    ) -> NetworkResponse:

        """
            Downloads file to the given destination

            Parameters
            ----------
            endpoint : str
                API endpoint
            destination : Union[Path, str]
                path to save file
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse as response content to request

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.genericDownload(
                    endpoint = "dummyObject/download",
                    destination = "path/to/destination/folder"
                )
            >>> if response.hasFailed():
                    print("Failed to download the file")
        """

        if isinstance(destination, str):
            destination = Path(destination)

        response = self.request(endpoint, RequestType.get, query = params, stream = True)
        if response.hasFailed():
            return response

        if destination.exists() and "Content-Length" in response.headers:
            contentLength = int(response.headers["Content-Length"])
            if contentLength == destination.stat().st_size:
                return response

            destination.unlink()

        with destination.open("wb") as file:
            for chunk in response.raw.iter_content():
                file.write(chunk)

        return response

    def refreshToken(self) -> NetworkResponse:
        """
            Uses refresh token functionality to fetch new API access token

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info
        """

        headers = self._headers()

        if self._refreshToken is not None:
            headers[self.apiTokenHeaderField] = self._refreshToken

        networkResponse = self.request(self.refreshEndpoint, RequestType.post, headers = headers)

        if self.apiTokenKey in networkResponse.json:
            self._apiToken = networkResponse.json[self.apiTokenKey]
            logging.getLogger("coretexpylib").debug(">> [Coretex] API token refresh was successful. API token updated")

        return networkResponse

    def shouldRetry(self, retryCount: int, response: Optional[NetworkResponse]) -> bool:
        """
            Checks if network request should be repeated based on the number of repetitions
            as well as the response from previous repetition

            Parameters
            ----------
            retryCount : int
                number of repeated function calls
            response : Optional[NetworkResponse]
                response of the request which is pending for retry

            Returns
            -------
            bool -> True if the function call needs to be repeated,
            False if function was called 3 times or if request has not failed
        """

        # Limit retry count to 3 times
        if retryCount == MAX_RETRY_COUNT:
            return False

        if response is not None:
            # If we get unauthorized maybe API token is expired
            if response.isUnauthorized():
                refreshTokenResponse = self.refreshToken()
                return not refreshTokenResponse.hasFailed()

            return (
                response.statusCode == HttpCode.internalServerError or
                response.statusCode == HttpCode.serviceUnavailable
            )

        return True

    def reset(self) -> None:
        """
            Removes api and refresh token
        """

        self._apiToken = None
        self._refreshToken = None
