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

from typing import Optional, Any, Dict, List, Union, Tuple, BinaryIO

import io
import time
import random
import logging

from .network_response import NetworkResponse


logger = logging.getLogger("coretexpylib")


RequestBodyType = Dict[str, Any]
RequestFormType = List[Tuple[str, Tuple[str, Union[bytes, BinaryIO], str]]]


def logFilesData(files: Optional[RequestFormType]) -> List[Dict[str, Any]]:
    if files is None:
        return []

    debugFilesData: List[Dict[str, Any]] = []

    for paramName, (fileName, fileData, mimeType) in files:
        if isinstance(fileData, bytes):
            fileSize = len(fileData)
        else:
            fileSize = fileData.seek(0, io.SEEK_END)
            fileData.seek(0)

        debugFilesData.append({
            "paramName": paramName,
            "fileName": fileName,
            "fileSize": fileSize,  # Dump file size instead of file data because file data can be in GBs
            "mimeType": mimeType
        })

    return debugFilesData


def logRequestFailure(endpoint: str, response: NetworkResponse) -> None:
    if not response.hasFailed():
        raise ValueError(f">> [Coretex] Invalid response status code: \"{response.statusCode}\"")

    logger.debug(f">> [Coretex] Request to \"{endpoint}\" failed with status code: {response.statusCode}")

    try:
        responseJson = response.getJson(dict)

        message = responseJson.get("message")
        if message is not None:
            logger.debug(f"\tResponse: {message}")
        else:
            logger.debug(f"\tResponse: {responseJson}")
    except (ValueError, TypeError):
        logger.debug(f"\tResponse: {response.getContent()!r}")


def getDelayBeforeRetry(retry: int) -> int:
    # retry starts from 0 so we add +1/+2 to start/end
    # to make it have proper delay

    start = (retry + 1) ** 2
    end   = (retry + 2) ** 2

    return random.randint(start, end)


def sleepBeforeRetry(retry: int, endpoint: str) -> None:
    delay = getDelayBeforeRetry(retry)
    logger.debug(f">> [Coretex] Waiting for {delay} seconds before retrying failed \"{endpoint}\" request")

    time.sleep(delay)


def getTimeoutForRetry(retry: int, timeout: Tuple[int, int], maxTimeout: Tuple[int, int]) -> Tuple[int, int]:
    connectTimeout, readTimeout = timeout
    maxConnectTimeout, maxReadTimeout = maxTimeout

    return (
        min(connectTimeout * retry, maxConnectTimeout),
        min(readTimeout * retry, maxReadTimeout)
    )
