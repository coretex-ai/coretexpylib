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
from http import HTTPStatus
from importlib.metadata import version as getLibraryVersion

import os
import json
import logging
import platform
import random
import time

import requests
import requests.adapters

from .utils import RequestBodyType, RequestFormType, logFilesData, logRequestFailure
from .request_type import RequestType
from .network_response import NetworkResponse, NetworkRequestError
from .file_data import FileData


REQUEST_TIMEOUT = 5
MAX_RETRY_COUNT = 5
LOGIN_ENDPOINT = "user/login"
REFRESH_ENDPOINT = "user/refresh"
API_TOKEN_HEADER = "api-token"
API_TOKEN_KEY = "token"
REFRESH_TOKEN_KEY = "refresh_token"

RETRY_STATUS_CODES = [
    HTTPStatus.TOO_MANY_REQUESTS,
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.SERVICE_UNAVAILABLE
]

TimeoutType = Optional[Union[int, Tuple[int, int]]]


def getDelayBeforeRetry(retryCount: int) -> int:
    # retryCount starts from 0 so we add +1/+2 to start/end
    # to make it have proper delay

    start = (retryCount + 1) ** 2
    end   = (retryCount + 2) ** 2

    return random.randint(start, end)


class RequestFailedError(Exception):

    def __init__(self, endpoint: str, type_: RequestType) -> None:
        super().__init__(f">> [Coretex] \"{type_.name}\" request failed for endpoint \"{endpoint}\"")


class NetworkManagerBase(ABC):

    def __init__(self) -> None:
        self._session = requests.Session()

        cpuCount = os.cpu_count()
        if cpuCount is None:
            cpuCount = 1

        # 10 is default, keep that value for machines which have <= 10 cores
        adapter = requests.adapters.HTTPAdapter(pool_maxsize = max(10, cpuCount))
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    @property
    def serverUrl(self) -> str:
        return os.environ["CTX_API_URL"] + "api/v1/"

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
        headers = {
            "Content-Type": contentType,
            "Connection": "keep-alive",
            "X-User-Agent": self.userAgent
        }

        if self._apiToken is not None:
            headers[API_TOKEN_HEADER] = self._apiToken

        return headers

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
            bool -> True if the request should be retried, False if not
        """

        # Limit retry count to 3 times
        if retryCount >= MAX_RETRY_COUNT:
            return False

        if response is not None:
            # If we get unauthorized maybe API token is expired
            # If refresh endpoint failed with unauthorized do not retry
            if response.isUnauthorized() and response.endpoint != REFRESH_ENDPOINT:
                refreshTokenResponse = self.refreshToken()
                return not refreshTokenResponse.hasFailed()

            return response.statusCode in RETRY_STATUS_CODES

        return True

    def request(
        self,
        endpoint: str,
        requestType: RequestType,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[RequestBodyType] = None,
        files: Optional[RequestFormType] = None,
        auth: Optional[Tuple[str, str]] = None,
        timeout: Optional[TimeoutType] = REQUEST_TIMEOUT,
        stream: bool = False,
        retryCount: int = 0
    ) -> NetworkResponse:

        """
            Sends an HTTP request with provided parameters
            This method is used as a base for all other networkManager methods

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            requestType : RequestType
                type of the request which is sent (get, post, put, delete, etc...)
            headers : Optional[Dict[str, Any]]
                headers which will be sent with request, if None default values will be used
            query : Optional[Dict[str, Any]]
                parameters which will be sent as query parameters
            body : Optional[RequestBodyType]
                parameters which will be sent as request body
            files : Optional[RequestFormType]
                files which will be sent as a part of form data request
            auth : Optional[Tuple[str, str]]
                credentials which will be send as basic auth header
            stream : bool
                defines if request body will be downloaded as a stream or not
            retryCount : int
                retry number of request - only for internal use

            Returns
            -------
            NetworkResponse -> object containing the request response

            Raises
            ------
            RequestFailedError -> if request failed due to connection issues
        """

        if headers is None:
            headers = self._headers()

        url = self.serverUrl + endpoint

        # Log request debug data
        logging.getLogger("coretexpylib").debug(f">> [Coretex] Sending request to \"{url}\"")
        logging.getLogger("coretexpylib").debug(f"\tType: {requestType}")
        logging.getLogger("coretexpylib").debug(f"\tHeaders: {headers}")
        logging.getLogger("coretexpylib").debug(f"\tQuery: {query}")
        logging.getLogger("coretexpylib").debug(f"\tBody: {body}")
        logging.getLogger("coretexpylib").debug(f"\tFiles: {logFilesData(files)}")
        logging.getLogger("coretexpylib").debug(f"\tAuth: {auth}")
        logging.getLogger("coretexpylib").debug(f"\tStream: {stream}")
        logging.getLogger("coretexpylib").debug(f"\tRetry count: {retryCount}")

        # If Content-Type is application/json make sure that body is converted to json
        data: Optional[Any] = body
        if headers.get("Content-Type") == "application/json" and data is not None:
            data = json.dumps(body)

        try:
            rawResponse = self._session.request(
                requestType.value,
                url,
                params = query,
                data = data,
                auth = auth,
                timeout = timeout,
                files = files,
                headers = headers
            )

            response = NetworkResponse(rawResponse, endpoint)
            if response.hasFailed():
                logRequestFailure(endpoint, response)

            if self.shouldRetry(retryCount, response):
                if self._apiToken is not None:
                    headers[API_TOKEN_HEADER] = self._apiToken

                # If we hit rate limiter sleep before retrying the request
                if response.statusCode == HTTPStatus.TOO_MANY_REQUESTS:
                    delay = getDelayBeforeRetry(retryCount)
                    logging.getLogger("coretexpylib").debug(f">> [Coretex] Waiting for {delay} seconds before retrying failed \"{endpoint}\" request")

                    time.sleep(delay)

                return self.request(endpoint, requestType, headers, query, body, files, auth, timeout, stream, retryCount + 1)

            return response
        except BaseException as exception:
            logging.getLogger("coretexpylib").debug(f">> [Coretex] Request failed. Reason \"{exception}\"", exc_info = exception)

            if self.shouldRetry(retryCount, None):
                if self._apiToken is not None:
                    headers[API_TOKEN_HEADER] = self._apiToken

                return self.request(endpoint, requestType, headers, query, body, files, auth, timeout, stream, retryCount + 1)

            raise RequestFailedError(endpoint, requestType)

    def post(
        self,
        endpoint: str,
        params: Optional[RequestBodyType] = None,
        timeout: TimeoutType = REQUEST_TIMEOUT
    ) -> NetworkResponse:

        """
            Sends post HTTP request

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            params : Optional[RequestBodyType]
                body of the request
            timeout : TimeoutType
                timeout for the request

            Returns
            -------
            NetworkResponse -> object containing the request response

            Raises
            ------
            RequestFailedError -> if request failed due to connection issues
        """

        return self.request(endpoint, RequestType.post, body = params, timeout = timeout)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> NetworkResponse:
        """
            Sends get HTTP request

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            params : Optional[RequestBodyType]
                query parameters of the request

            Returns
            -------
            NetworkResponse -> object containing the request response

            Raises
            ------
            RequestFailedError -> if request failed due to connection issues
        """

        return self.request(endpoint, RequestType.get, query = params)

    def put(self, endpoint: str, params: Optional[RequestBodyType] = None) -> NetworkResponse:
        """
            Sends put HTTP request

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            params : Optional[RequestBodyType]
                body of the request

            Returns
            -------
            NetworkResponse -> object containing the request response

            Raises
            ------
            RequestFailedError -> if request failed due to connection issues
        """

        return self.request(endpoint, RequestType.put, body = params)

    def delete(self, endpoint: str) -> NetworkResponse:
        """
            Sends delete HTTP request

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent

            Returns
            -------
            NetworkResponse -> object containing the request response

            Raises
            ------
            RequestFailedError -> if request failed due to connection issues
        """

        return self.request(endpoint, RequestType.delete)

    def formData(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[List[FileData]] = None,
        timeout: TimeoutType = REQUEST_TIMEOUT
    ) -> NetworkResponse:

        """
            Sends multipart/form-data request

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            params : Optional[Dict[str, Any]]
                form data parameters
            files : Optional[List[FileData]]
                form data files
            timeout : Optional[Union[int, Tuple[int, int]]]
                timeout for the request

            Returns
            -------
            NetworkResponse -> object containing the request response

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.formData(
                    endpoint = "dummyObject/form",
                    params = {
                        "key": "value"
                    }
                )
            >>> if response.hasFailed():
                    print("Failed to send form data request")
        """

        if files is None:
            files = []

        with ExitStack() as stack:
            filesData = [file.prepareForUpload(stack) for file in files]

            headers = self._headers("multipart/form-data")
            del headers["Content-Type"]

            if len(files) > 0:
                response = self.request(endpoint, RequestType.options, timeout = REQUEST_TIMEOUT)
                if response.hasFailed():
                    raise NetworkRequestError(response, "Could not establish a connection with the server")

                timeout = None

            return self.request(endpoint, RequestType.post, headers, body = params, files = filesData, timeout = timeout)

        # mypy is complaining about missing return statement but this code is unreachable
        # see: https://github.com/python/mypy/issues/7726
        raise RuntimeError("Unreachable")

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
            NetworkResponse -> object containing the request response

            Example
            -------
            >>> from coretex.networking import networkManager
            \b
            >>> response = networkManager.authenticate("dummy@coretex.ai", "123456")
            >>> if response.hasFailed():
                    print("Failed to authenticate")
        """

        # authenticate using credentials stored in requests.Session.auth

        response = self.request(LOGIN_ENDPOINT, RequestType.post, auth = (username, password))
        if response.hasFailed():
            return response

        responseJson = response.getJson(dict)

        self._apiToken = responseJson[API_TOKEN_KEY]
        self._refreshToken = responseJson[REFRESH_TOKEN_KEY]

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
            NetworkResponse -> object containing the request response
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
                endpoint to which the request is sent
            destination : Union[Path, str]
                path to save file

            Returns
            -------
            NetworkResponse -> object containing the request response

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
            downloadedFile.write(response.getContent())

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
                endpoint to which the request is sent
            destination : Union[Path, str]
                path to save file
            retryCount : int
                number of function calls if request has failed, used
                for internal retry mechanism

            Returns
            -------
            NetworkResponse -> object containing the request response

            Example
            -------
            >>> from coretex import networkManager
            \b
            >>> response = networkManager.streamDownload(
                    endpoint = "dummyObject/download",
                    destination = "path/to/destination/folder"
                )
            >>> if response.hasFailed():
                    print("Failed to download the file")
        """

        if isinstance(destination, str):
            destination = Path(destination)

        response = self.request(endpoint, RequestType.get, query = params, stream = True, timeout = (5, 60))
        if response.hasFailed():
            return response

        if destination.exists() and "Content-Length" in response.headers:
            contentLength = int(response.headers["Content-Length"])
            if contentLength == destination.stat().st_size:
                return response

            destination.unlink()

        with destination.open("wb") as file:
            for chunk in response.stream():
                file.write(chunk)

        return response

    def refreshToken(self) -> NetworkResponse:
        """
            Uses refresh token functionality to fetch new API access token

            Returns
            -------
            NetworkResponse -> object containing the request response
        """

        if self._refreshToken is None:
            raise ValueError(f">> [Coretex] Cannot send \"{REFRESH_ENDPOINT}\" request, refreshToken is None")

        headers = self._headers()
        headers[API_TOKEN_HEADER] = self._refreshToken

        response = self.request(REFRESH_ENDPOINT, RequestType.post, headers = headers)
        if response.hasFailed():
            return response

        responseJson = response.getJson(dict)
        self._apiToken = responseJson[API_TOKEN_KEY]

        return response

    def reset(self) -> None:
        """
            Removes api and refresh token
        """

        self._apiToken = None
        self._refreshToken = None
