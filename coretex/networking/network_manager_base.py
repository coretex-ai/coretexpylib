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

from typing import Optional, Any, Dict, List, Union
from pathlib import Path
from abc import ABC, abstractmethod
from importlib.metadata import version as getLibraryVersion

import json
import logging
import platform

from .requests_manager import RequestsManager
from .request_type import RequestType
from .network_response import HttpCode, NetworkResponse
from .file_data import FileData


class NetworkManagerBase(ABC):

    MAX_RETRY_COUNT = 3

    def __init__(self) -> None:
        self._requestManager = RequestsManager(20, 30)

        # Override NetworkManager to update values
        self.loginEndpoint: str = "user/login"
        self.refreshEndpoint: str = "user/refresh"

        self.apiTokenHeaderField: str = "api-token"

        self.apiTokenKey: str = "token"
        self.refreshTokenKey: str = "refresh_token"

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

    def _requestHeader(self) -> Dict[str, str]:
        header = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip, deflate",
            "Content-Length": "0",
            "Connection": "keep-alive",
            "cache-control": "no-cache",
            "X-User-Agent": self.userAgent
        }

        if self._apiToken is not None:
            header[self.apiTokenHeaderField] = self._apiToken

        return header

    def _authenticate(self) -> NetworkResponse:
        # authenticate using credentials stored in requests.Session.auth

        response = self._requestManager.post(
            endpoint = self.loginEndpoint,
            headers = self._requestHeader()
        )

        if self.apiTokenKey in response.json:
            self._apiToken = response.json[self.apiTokenKey]

        if self.refreshTokenKey in response.json:
            self._refreshToken = response.json[self.refreshTokenKey]

        return response

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

        self._requestManager.setAuth(username, password)

        # authenticate using credentials stored in requests.Session.auth
        return self._authenticate()

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

    def genericDownload(
        self,
        endpoint: str,
        destination: Union[Path, str],
        parameters: Optional[Dict[str, Any]] = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Downloads file to the given destination

            Parameters
            ----------
            endpoint : str
                API endpoint
            destination : Union[Path, str]
                path to save file
            parameters : Optional[dict[str, Any]]
                request parameters (not required)
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

        if destination.is_dir():
            raise RuntimeError(">> [Coretex] Destination is a directory not a file")

        headers = self._requestHeader()

        if parameters is None:
            parameters = {}

        response = self._requestManager.get(endpoint, headers, jsonObject = parameters)

        if self.shouldRetry(retryCount, response):
            print(">> [Coretex] Retry count: {0}".format(retryCount))
            return self.genericDownload(endpoint, destination, parameters, retryCount + 1)

        if response.raw.ok:
            if destination.exists():
                destination.unlink(missing_ok = True)

            destination.parent.mkdir(parents = True, exist_ok = True)

            with destination.open("wb") as downloadedFile:
                downloadedFile.write(response.raw.content)

        return response

    def sampleDownload(
        self,
        endpoint: str,
        destination: Union[str, Path],
        ignoreCache: bool,
        parameters: Optional[Dict[str, Any]] = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Downloads file to the given destination by chunks

            Parameters
            ----------
            endpoint : str
                API endpoint
            destination : Union[str, Path]
                path to save file
            ignoreCache : bool
                whether to overwrite local cache
            parameters : Optional[dict[str, Any]]
                request parameters (not required)
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
            >>> response = networkManager.sampleDownload(
                    endpoint = "dummyObject/download",
                    destination = "path/to/destination/folder"
                )
            >>> if response.hasFailed():
                    print("Failed to download the file")
        """

        headers = self._requestHeader()

        if parameters is None:
            parameters = {}

        networkResponse = self._requestManager.streamingDownload(
            endpoint,
            destination,
            ignoreCache,
            headers,
            parameters
        )

        if self.shouldRetry(retryCount, networkResponse):
            print(">> [Coretex] Retry count: {0}".format(retryCount))
            return self.sampleDownload(endpoint, destination, ignoreCache, parameters, retryCount + 1)

        return networkResponse

    def genericUpload(
        self,
        endpoint: str,
        files: List[FileData],
        parameters: Optional[Dict[str, Any]] = None,
        retryCount: int = 0
    ) -> NetworkResponse:

        """
            Sends a multipart form data request to Coretex.ai
            with files

            Parameters
            ----------
            endpoint : str
                API endpoint
            files : List[FileData]
                List of "FileData" objects which describe how
                should the files be uploaded to Coretex.ai
            parameters : dict[str, Any]
                request parameters - must be ordered to match
                expected values on Coretex.ai
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Example
            -------
            >>> from coretex import networkManager, FileData
            \b
            >>> with open("path/to/file_2.ext", "rb") as file:
                    fileBytes = file.read()
            \b
            >>> files = [
                    FileData.createFromPath("file_1", "path/to/file_1.ext"),
                    FileData.createFromBytes("file_2", fileBytes, fileName = "file_2")
                ]
            \b
            >>> response = networkManager.genericFormData(
                    endpoint = "dummy/form-data",
                    files = files,
                    parameters = {
                        "first": "first_value",
                        "second": "second_value"
                    }
                )
            >>> if response.hasFailed():
                    print("Failed to upload the provided files")
        """

        networkResponse = self._requestManager.upload(endpoint, self._requestHeader(), files, parameters)

        if self.shouldRetry(retryCount, networkResponse):
            return self.genericUpload(endpoint, files, parameters, retryCount + 1)

        return networkResponse

    def genericFormData(self, endpoint: str, parameters: Dict[str, Any], retryCount: int = 0) -> NetworkResponse:
        """
            Sends a form data request to Cortex.ai

            Parameters
            ----------
            endpoint : str
                API endpoint
            parameters : dict[str, Any]
                request parameters - must be ordered to match
                expected values on Coretex.ai
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.genericFormData(
                    endpoint = "dummy/form-data",
                    parameters = {
                        "first": "first_value",
                        "second": "second_value"
                    }
                )
            >>> if response.hasFailed():
                    print("Failed to execute form data request")
        """

        headers = self._requestHeader()
        del headers['Content-Type']

        # Map to correct form data parameter format
        formDataParameters = {
            key: (None, value)
            for key, value in parameters.items()
        }

        # RequestsManager.genericRequest files parameter can
        # accept parameters that are not files, this way we can
        # send form-data requests without actual files
        networkResponse = self._requestManager.genericRequest(RequestType.post, endpoint, headers, files = formDataParameters)

        if self.shouldRetry(retryCount, networkResponse):
            print(">> [Coretex] Retry count: {0}".format(retryCount))
            return self.genericFormData(endpoint, parameters, retryCount + 1)

        return networkResponse

    def genericDelete(
        self,
        endpoint: str
    ) -> NetworkResponse:
        """
            Deletes Cortex.ai objects

            Parameters
            ----------
            endpoint : str
                API endpoint

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.genericDelete(
                    endpoint = "dummyObject/delete"
                )
            >>> if response.hasFailed():
                    print("Failed to delete the object")
        """

        return self._requestManager.genericRequest(RequestType.delete, endpoint, self._requestHeader())

    def genericJSONRequest(
        self,
        endpoint: str,
        requestType: RequestType,
        parameters: Optional[Dict[str, Any]] = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Sends generic http request with specified parameters

            Parameters
            ----------
            endpoint : str
                API endpoint
            requestType : RequestType
                request type
            parameters : Optional[dict[str, Any]]
                request parameters (not required)
            headers : Optional[dict[str, str]]
                headers (not required)
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.genericJSONRequest(
                    endpoint = "dummy/add",
                    requestType = RequestType.post,
                    parameters = {
                        "object_id": 1,
                    }
                )
            >>> if response.hasFailed():
                    print("Failed to add the object")
        """

        if parameters is None:
            parameters = {}

        networkResponse = self._requestManager.genericRequest(requestType, endpoint, self._requestHeader(), json.dumps(parameters))

        if self.shouldRetry(retryCount, networkResponse):
            print(">> [Coretex] Retry count: {0}".format(retryCount))
            return self.genericJSONRequest(endpoint, requestType, parameters, retryCount + 1)

        return networkResponse

    def refreshToken(self) -> NetworkResponse:
        """
            Uses refresh token functionality to fetch new API access token

            Returns
            -------
            NetworkResponse -> NetworkResponse object containing the full response info
        """

        headers = self._requestHeader()

        if self._refreshToken is not None:
            headers[self.apiTokenHeaderField] = self._refreshToken

        networkResponse = self._requestManager.genericRequest(
            requestType = RequestType.post,
            endpoint = self.refreshEndpoint,
            headers = headers
        )

        if self.apiTokenKey in networkResponse.json:
            self._apiToken = networkResponse.json[self.apiTokenKey]
            logging.getLogger("coretexpylib").debug(">> [Coretex] API token refresh was successful. API token updated")

        return networkResponse

    def shouldRetry(self, retryCount: int, response: NetworkResponse) -> bool:
        """
            Checks if network request should be repeated based on the number of repetitions
            as well as the response from previous repetition

            Parameters
            ----------
            retryCount : int
                number of repeated function calls
            response : NetworkResponse
                generated response after sending the request

            Returns
            -------
            bool -> True if the function call needs to be repeated,
            False if function was called 3 times or if request has not failed
        """

        # Limit retry count to 3 times
        if retryCount == NetworkManagerBase.MAX_RETRY_COUNT:
            return False

        # If we get unauthorized maybe API token is expired
        if response.isUnauthorized():
            refreshTokenResponse = self.refreshToken()
            return not refreshTokenResponse.hasFailed()

        return (
            response.statusCode == HttpCode.internalServerError or
            response.statusCode == HttpCode.serviceUnavailable
        )

    def reset(self) -> None:
        """
            Removes api and refresh token
        """

        self._apiToken = None
        self._refreshToken = None
        self._requestManager.reset()
