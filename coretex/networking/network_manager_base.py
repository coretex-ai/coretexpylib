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

import requests
import requests.adapters

from .utils import RequestBodyType, RequestFormType, logFilesData, logRequestFailure, sleepBeforeRetry, getTimeoutForRetry
from .request_type import RequestType
from .network_response import NetworkResponse, NetworkRequestError
from .file_data import FileData


logger = logging.getLogger("coretexpylib")

REQUEST_TIMEOUT      = (5, 10)     # Connection = 5 seconds, Read = 10 seconds
MAX_REQUEST_TIMEOUT  = (60, 180)   # Connection = 60 seconds, Read = 3 minutes
DOWNLOAD_TIMEOUT     = (5, 60)     # Connection = 5 seconds, Read = 1 minute
MAX_DOWNLOAD_TIMEOUT = (60, 180)   # Connection = 1 minute, Read = 3 minutes
UPLOAD_TIMEOUT       = (5, 60)     # Connection = 5 seconds, Read = 1 minute
MAX_UPLOAD_TIMEOUT   = (60, 1800)  # Connection = 1 minute, Read = 30 minutes

MAX_RETRY_COUNT        = 5        # Request will be retried 5 times before raising an error
MAX_DELAY_BEFORE_RETRY = 180      # 3 minute

LOGIN_ENDPOINT    = "user/login"
REFRESH_ENDPOINT  = "user/refresh"
API_TOKEN_HEADER  = "api-token"
API_TOKEN_KEY     = "token"
REFRESH_TOKEN_KEY = "refresh_token"

RETRY_STATUS_CODES = [
    HTTPStatus.TOO_MANY_REQUESTS,
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.SERVICE_UNAVAILABLE
]

DOWNLOAD_CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB


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
        timeout: Tuple[int, int] = REQUEST_TIMEOUT,
        maxTimeout: Tuple[int, int] = MAX_REQUEST_TIMEOUT,
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
            timeout : Tuple[int, int]
                timeout for the request, default <connection: 5s>, <read: 10s>
            maxTimeout : Tuple[int, int]
                timeout for the request, default <connection: 60s>, <read: 180s>
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
        logger.debug(f">> [Coretex] Sending request to \"{url}\"")
        logger.debug(f"\tType: {requestType}")
        logger.debug(f"\tHeaders: {headers}")
        logger.debug(f"\tQuery: {query}")
        logger.debug(f"\tBody: {body}")
        logger.debug(f"\tFiles: {logFilesData(files)}")
        logger.debug(f"\tAuth: {auth}")
        logger.debug(f"\tStream: {stream}")
        logger.debug(f"\tTimeout: {timeout}")
        logger.debug(f"\tMax timeout: {maxTimeout}")
        logger.debug(f"\tRetry count: {retryCount}")

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

                if response.statusCode == HTTPStatus.TOO_MANY_REQUESTS:
                    # If the rate limiter is hit sleep before retrying the request
                    sleepBeforeRetry(retryCount, endpoint)

                return self.request(endpoint, requestType, headers, query, body, files, auth, timeout, maxTimeout, stream, retryCount + 1)

            return response
        except requests.exceptions.RequestException as ex:
            logger.debug(f">> [Coretex] Request failed. Reason \"{ex}\"", exc_info = ex)

            if self.shouldRetry(retryCount, None):
                # If an exception happened during the request add a delay before retrying
                sleepBeforeRetry(retryCount, endpoint)

                if isinstance(ex, requests.exceptions.ConnectionError) and "timeout" in str(ex):
                    # If request failed due to timeout recalculate (increase) the timeout
                    oldTimeout = timeout
                    timeout = getTimeoutForRetry(retryCount + 1, timeout, maxTimeout)

                    logger.debug(f">> [Coretex] \"{endpoint}\" failed failed due to timeout. Increasing the timeout from {oldTimeout} to {timeout}")

                if self._apiToken is not None:
                    headers[API_TOKEN_HEADER] = self._apiToken

                return self.request(endpoint, requestType, headers, query, body, files, auth, timeout, maxTimeout, stream, retryCount + 1)

            raise RequestFailedError(endpoint, requestType)

    def head(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> NetworkResponse:

        """
            Sends head HTTP request

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            params : Optional[RequestBodyType]
                query parameters of the request
            headers : Optional[Dict[str, str]]
                additional headers of the request

            Returns
            -------
            NetworkResponse -> object containing the request response

            Raises
            ------
            RequestFailedError -> if request failed due to connection/timeout issues
        """

        if headers is not None:
            headers = {**self._headers(), **headers}

        return self.request(endpoint, RequestType.head, headers, query = params)

    def post(self, endpoint: str, params: Optional[RequestBodyType] = None) -> NetworkResponse:
        """
            Sends post HTTP request

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

        return self.request(endpoint, RequestType.post, body = params)

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
        files: Optional[List[FileData]] = None
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
                response = self.request(endpoint, RequestType.options)
                if response.hasFailed():
                    raise NetworkRequestError(response, "Could not establish a connection with the server")

                # If files are being uploaded bigger timeout is required
                timeout = UPLOAD_TIMEOUT
                maxTimeout = MAX_UPLOAD_TIMEOUT
            else:
                # If there are no files there is no need for big timeouts
                timeout = REQUEST_TIMEOUT
                maxTimeout = MAX_REQUEST_TIMEOUT

            return self.request(
                endpoint,
                RequestType.post,
                headers,
                body = params,
                files = filesData,
                timeout = timeout,
                maxTimeout = maxTimeout
            )

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
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> NetworkResponse:

        """
            Downloads file to the given destination

            Parameters
            ----------
            endpoint : str
                endpoint to which the request is sent
            destination : Union[Path, str]
                path to save file
            params : Optional[Dict[str, Any]]
                query parameters of the request
            headers : Optional[Dict[str, str]]
                additional headers of the request

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

        # If the destination exists check if it's corrupted
        if destination.exists():
            response = self.head(endpoint, params, headers)
            if response.hasFailed():
                return response

            # If the Content-Length returned by the head request is not equal to destination's
            # file size force the file to be re-downloaded
            try:
                contentLength = int(response.headers["Content-Length"])
                if destination.stat().st_size == contentLength:
                    return response
            except (ValueError, KeyError):
                # KeyError - Content-Length is not present in headers
                # ValueError - Content-Length cannot be converted to int
                pass

        if headers is not None:
            headers = {**self._headers(), **headers}

        # Timeout for download applies per chunk, not for the full file download
        response = self.request(
            endpoint,
            RequestType.get,
            headers,
            query = params,
            stream = True,
            timeout = DOWNLOAD_TIMEOUT,
            maxTimeout = MAX_DOWNLOAD_TIMEOUT
        )

        if response.hasFailed():
            return response

        with destination.open("wb") as file:
            for chunk in response.stream(chunkSize = DOWNLOAD_CHUNK_SIZE):
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
