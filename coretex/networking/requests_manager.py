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

from typing import Final, Any, Optional, Dict, List, Union
from contextlib import ExitStack
from pathlib import Path

import os
import logging

from requests import Session

from .network_response import NetworkResponse
from .request_type import RequestType
from .file_data import FileData


class RequestFailedError(RuntimeError):

    def __init__(self) -> None:
        super().__init__(">> [Coretex] Failed to execute request after retrying")


class RequestsManager:

    """
        Represents class that is used for handling requests
    """

    MAX_RETRY_COUNT: Final = 3

    def __init__(self, connectionTimeout: int, readTimeout: int):
        self.__connectionTimeout: Final = connectionTimeout
        self.__readTimeout: Final = readTimeout
        self.__session: Final = Session()

    @property
    def isAuthSet(self) -> bool:
        return self.__session.auth is not None

    @classmethod
    def serverUrl(cls) -> str:
        serverUrl = os.environ["CTX_API_URL"]
        return f"{serverUrl}api/v1/"

    def __url(self, endpoint: str) -> str:
        return self.serverUrl() + endpoint

    def genericRequest(
        self,
        requestType: RequestType,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        files: Any = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Sends generic HTTP request

            Parameters
            ----------
            requestType : RequestType
                request type
            endpoint : str
                API endpoint
            headers : Optional[Dict[str, str]]
                headers (not required)
            data : Any
                (not required)
            files : Any
                (not required)
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object as response content to request
        """

        logging.getLogger("coretexpylib").debug(f"Sending request {requestType}, {self.__url(endpoint)}, HEADERS: {headers}, DATA: {data}")

        try:
            requestsResponse = self.__session.request(
                method = requestType.value,
                url = self.__url(endpoint),
                headers = headers,
                data = data,
                files = files
                # timeout = (self.__connectionTimeout, self.__readTimeout)
            )

            return NetworkResponse(requestsResponse, endpoint)
        except:
            if retryCount < RequestsManager.MAX_RETRY_COUNT:
                RequestsManager.__logRetry(requestType, endpoint, retryCount)
                return self.genericRequest(requestType, endpoint, headers, data, files, retryCount = retryCount + 1)

            raise RequestFailedError

    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        jsonObject: Any = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Sends HTTP get request

            Parameters
            ----------
            endpoint : str
                API endpoint
            headers : Optional[Dict[str, str]]
                headers (not required)
            data : Any
                (not required)
            jsonObject : Any
                (not required)
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object as response content to request
        """

        logging.getLogger("coretexpylib").debug(f"Sending request {self.__url(endpoint)}, HEADERS: {headers}, DATA: {data}, JSON_OBJECT: {jsonObject}")

        try:
            requestsResponse = self.__session.get(
                url = self.__url(endpoint),
                headers = headers,
                data = data,
                json = jsonObject
                # timeout = (self.__connectionTimeout, self.__readTimeout)
            )

            return NetworkResponse(requestsResponse, endpoint)
        except:
            if retryCount < RequestsManager.MAX_RETRY_COUNT:
                RequestsManager.__logRetry(RequestType.get, endpoint, retryCount)
                return self.get(endpoint, headers, data, jsonObject, retryCount = retryCount + 1)

            raise RequestFailedError

    def post(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        jsonObject: Any = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Sends HTTP post request

            Parameters
            ----------
            endpoint : str
                API endpoint
            headers : Optional[Dict[str, str]]
                headers (not required)
            data : Any
                (not required)
            jsonObject : Any
                (not required)
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object as response content to request
        """

        logging.getLogger("coretexpylib").debug(f"Sending request {self.__url(endpoint)}, HEADERS: {headers}, DATA: {data}, JSON_OBJECT: {jsonObject}")

        try:
            requestsResponse = self.__session.post(
                url = self.__url(endpoint),
                headers = headers,
                data = data,
                json = jsonObject
                # timeout = (self.__connectionTimeout, self.__readTimeout)
            )

            return NetworkResponse(requestsResponse, endpoint)
        except:
            if retryCount < RequestsManager.MAX_RETRY_COUNT:
                RequestsManager.__logRetry(RequestType.post, endpoint, retryCount)
                return self.post(endpoint, headers, data, jsonObject, retryCount = retryCount + 1)

            raise RequestFailedError

    def streamingDownload(
        self,
        endpoint: str,
        destinationPath: Union[str, Path],
        ignoreCache: bool,
        headers: Dict[str, str],
        parameters: Dict[str, Any],
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Downloads a file from endpoint to destinationPath in chunks of 8192 bytes

            Parameters
            ----------
            endpoint : str
                API endpoint
            destination : Union[str, Path]
                path to save file
            ignoreCache : bool
                whether to overwrite local cache
            headers : Any
                headers for get
            parameters : int
                json for get

            Returns
            -------
            NetworkResponse -> NetworkResponse object as response content to request
        """

        try:
            with self.__session.get(
                self.__url(endpoint),
                stream = True,
                headers = headers,
                json = parameters
            ) as response:

                response.raise_for_status()

                if isinstance(destinationPath, str):
                    destinationPath = Path(destinationPath)

                if destinationPath.is_dir():
                    raise RuntimeError(">> [Coretex] Destination is a directory not a file")

                if destinationPath.exists():
                    if int(response.headers["Content-Length"]) == destinationPath.stat().st_size and not ignoreCache:
                        return NetworkResponse(response, endpoint, ignoreContent = True)

                    destinationPath.unlink()

                with destinationPath.open("wb") as downloadedFile:
                    for chunk in response.iter_content(chunk_size = 8192):
                        downloadedFile.write(chunk)

                return NetworkResponse(response, endpoint)
        except:
            if retryCount < RequestsManager.MAX_RETRY_COUNT:
                RequestsManager.__logRetry(RequestType.get, endpoint, retryCount)
                return self.streamingDownload(
                    endpoint,
                    destinationPath,
                    ignoreCache,
                    headers,
                    parameters,
                    retryCount = retryCount + 1
                )

            raise RequestFailedError

    def upload(
        self,
        endpoint: str,
        headers: Dict[str, str],
        files: List[FileData],
        parameters: Optional[Dict[str, Any]] = None,
        retryCount: int = 0
    ) -> NetworkResponse:
        """
            Sends generic HTTP request

            Parameters
            ----------
            endpoint : str
                API endpoint
            headers : Dict[str, str]
                request headers
            files : List[FileData]
                files which will be uploaded and their metadata
            parameters : Optional[Dict[str, Any]]
                request parameters (not required)
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> NetworkResponse object as response content to request
        """

        if "Content-Type" in headers:
            del headers['Content-Type']

        logging.getLogger("coretexpylib").debug(f"Sending upload request {endpoint}, HEADERS: {headers}, FILES: {files}, PARAMETERS: {parameters}")

        try:
            # ExitStack lets us combine multiple contexts when opening files
            # and if anything failes then the ExitStack will properly close
            # all open file handles
            with ExitStack() as stack:
                requestsResponse = self.__session.request(
                    method = RequestType.post.value,
                    url = self.__url(endpoint),
                    headers = headers,
                    data = parameters,
                    files = [file.prepareForUpload(stack) for file in files]
                    # timeout = (self.__connectionTimeout, self.__readTimeout)
                )

            return NetworkResponse(requestsResponse, endpoint)
        except:
            if retryCount < RequestsManager.MAX_RETRY_COUNT:
                RequestsManager.__logRetry(RequestType.post, endpoint, retryCount)
                return self.upload(endpoint, headers, files, parameters, retryCount + 1)

            raise RequestFailedError

    def setAuth(self, username: str, password: str) -> None:
        self.__session.auth = (username, password)

    @staticmethod
    def __logRetry(requestType: RequestType, endpoint: str, retryCount: int) -> None:
        """
            Logs the information about request retry
        """

        logging.getLogger("coretexpylib").debug(
            f">> [Coretex] Retry {retryCount + 1} for ({requestType.name} -> {endpoint})",
            exc_info = True
        )

    def reset(self) -> None:
        self.__session.auth = None
