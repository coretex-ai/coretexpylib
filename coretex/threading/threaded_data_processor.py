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

from typing import Any, Callable, Optional, List
from concurrent.futures import ThreadPoolExecutor, Future

import logging
import os


MAX_WORKER_COUNT = 8


class MultithreadedDataProcessor:

    """
        Used for splitting data processing on multiple threads
        Only useful for I/O bound operations, do not use for
        heavy data processing operations

        data: List[Any]
            list which will be split-processed on multiple threads
        singleElementProcessor: Callable[[Any], None]
            function which will be called for a single element from the provided list
        threadCount: Optional[int]
            number of threads which will be used for processing (maximum is 8), if None
            it will use min(cpuCores, 8)
        title: Optional[str]
            message which is displayed when the processing starts

        Example
        -------
        >>> import os
        >>> from pathlib import Path
        >>> from coretex import CustomItem
        >>> from coretex.networking import networkManager
        >>> from coretex.threading import MultithreadedDataProcessor
        \b
        >>> networkManager.authenticate("dummyUser@coretex.ai", *******) # login on coretex
        >>> path = "" #path to dir which contains samples for upload to dataset
        >>> listOfFiles = []
        \b
        >>> def createItem(path: str) -> CustomItem:
                item = CustomItem.createCustomItem(Path(path).stem, 1023, path)  # first make new dataset
                if item is None:
                    pass
        \b
        >>> for file in os.listdir(path):
                if file.endswith(".zip"):
                    file = os.path.join(path, file)
                    listOfFiles.append(file)
        \b
        >>> processor = MultithreadedDataProcessor(
                listOfFiles,
                createItem,
                threadCount = 8, # set threadCount on desired value default is 8
                title = "createItem"
            )
        >>> processor.process()
    """

    def __init__(
        self,
        data: List[Any],
        singleElementProcessor: Callable[[Any], None],
        workerCount: Optional[int] = None,
        message: Optional[str] = None
    ) -> None:

        if workerCount is None:
            cpuCount = os.cpu_count()

            if cpuCount is None:
                cpuCount = 1

            workerCount = min(MAX_WORKER_COUNT, cpuCount)
        else:
            if workerCount > MAX_WORKER_COUNT:
                logging.warning(f">> [Coretex] \"workerCount\" value: {workerCount} is higher than maximum allowed: {MAX_WORKER_COUNT}. Using {MAX_WORKER_COUNT} workers")

            workerCount = min(MAX_WORKER_COUNT, workerCount)

        self.__data = data
        self.__singleElementProcessor = singleElementProcessor
        self.__workerCount = workerCount
        self.__message = message

    def process(self) -> None:
        """
            Starts the multithreaded processing of the data

            Raises
            ------
            Any unhandled exception which happened during the processing
        """

        if self.__message is not None:
            logging.getLogger("coretexpylib").info(f">> [Coretex] {self.__message}")
            logging.getLogger("coretexpylib").info(f"\tUsing {self.__workerCount} workers")

        futures: List[Future] = []

        with ThreadPoolExecutor(max_workers = self.__workerCount) as pool:
            for element in self.__data:
                future = pool.submit(self.__singleElementProcessor, element)
                futures.append(future)

        for future in futures:
            exception = future.exception()
            if exception is not None:
                raise exception
