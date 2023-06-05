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

from typing import Any, Tuple

from pathlib import Path
from zipfile import ZipFile

import os
import logging
import shutil
import pickle
import hashlib
import zipfile

import requests

from ..folder_management import FolderManager


IGNORED_FILE_TYPES = [".pt"]


class CacheException(Exception):

    """
        Exception which is raised due to any unexpected behaviour with Cache module
    """

    pass


def __hashedKey(key: str) -> str:
    return hashlib.sha256(key.encode("UTF-8")).hexdigest()


def __zip(zipPath: Path, filePath: Path, fileName: str) -> None:
    baseName, fileExtension = os.path.splitext(filePath)

    if fileExtension in IGNORED_FILE_TYPES or not zipfile.is_zipfile(filePath):
        with ZipFile(zipPath, mode = "w") as archive:
            archive.write(filePath, fileName)

        filePath.unlink(missing_ok = True)
    else:
        filePath.rename(FolderManager.instance().cache / filePath.name)


def __downloadFromUrl(url: str, fileName: str) -> Tuple[Path, str]:
    tempPath = FolderManager.instance().temp
    hashUrl = __hashedKey(url)
    fileName, fileExtension = os.path.splitext(fileName)

    with requests.get(url, stream = True) as r:
        r.raise_for_status()

        resultPath = os.path.join(tempPath, hashUrl)
        fileName = f"{hashUrl}{fileExtension}"
        resultPath = os.path.join(tempPath, fileName)

        with open(resultPath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return Path(resultPath), fileName


def storeObject(key: str, object: Any, override: bool = False) -> None:
    """
        Caches the specified object using pickle

        Parameters
        ----------
        key : str
            key to which the cached object will be linked
        object : Any
            object which supports being pickled
        override : bool
            should the cache be overriden if it exists or not

        Raises
        ------
        CacheException -> if something went wrong

        Example
        -------
        >>> from coretex import cache
        \b
        >>> dummyObject = {"name": "John", "age": 24, "gender": "Male"}
        >>> cache.storeObject("Person", dummyObject)
    """

    hashedKey = __hashedKey(key)
    zipPath = (FolderManager.instance().cache / hashedKey).with_suffix(".zip")

    pickleName = f"{hashedKey}.pickle"
    picklePath = FolderManager.instance().cache / pickleName

    if override:
        zipPath.unlink(missing_ok = True)
        logging.getLogger("coretexpylib").info(">> [Coretex] Overriding existing cache.")

    if not override and picklePath.exists():
        raise CacheException(">> [Coretex] Cache with given key already exists. Set parameter override to True if you wanna override existing cache.")

    with open(picklePath, "wb") as pickleFile:
        pickle.dump(object, pickleFile)

    __zip(zipPath, picklePath, pickleName)


def storeFile(key: str, filePath: str, override: bool = False) -> None:
    """
        Caches the specified file

        Parameters
        ----------
        key : str
            key to which the cached file will be linked
        filePath : str
            path to the file which will be cached
        override : bool
            should the cache be overriden if it exists or not

        Raises
        ------
        CacheException -> if something went wrong

        Example
        -------
        >>> from coretex import cache
        \b
        >>> filePath = "path/to/file"
        >>> cache.storeFile("dummyFile", filePath)
    """
    hashedKey = __hashedKey(key)
    cachePath = FolderManager.instance().cache / hashedKey

    cacheZipPath = cachePath.with_suffix(".zip")

    if override:
        cacheZipPath.unlink(missing_ok = True)
        logging.getLogger("coretexpylib").info(">> [Coretex] Overriding existing cache.")

    if not override and cacheZipPath.exists():
        raise CacheException(">> [Coretex] Cache with given key already exists. Set parameter override to True if you wanna override existing cache.")

    logging.getLogger("coretexpylib").info(">> [Coretex] Cache with given key doesn't exist, caching...")
    shutil.copy(filePath, cachePath)

    __zip(cacheZipPath, cachePath, hashedKey)


def storeUrl(url: str, fileName: str, override: bool = False) -> None:
    """
        Downloads and caches file from the specified URL

        Parameters
        ----------
        url : str
            URL of the file which is downloaded
        fileName : str
            Name of the downloaded file with extension - used as a key for cache

        Returns
        -------
        Tuple[Path, str] -> Path of the cached file and the name of the cached file

        Raises
        ------
        CacheException -> if something went wrong

        Example
        -------
        >>> from coretex import cache
        \b
        >>> url = "https://dummy_url.com/download"
        >>> fileName = "dummyFile.ext"
        >>> cache.storeUrl(url, fileName)
    """

    hashedKey = __hashedKey(url)
    cacheZipPath = (FolderManager.instance().cache / hashedKey).with_suffix(".zip")

    if override:
        cacheZipPath.unlink(missing_ok = True)
        logging.getLogger("coretexpylib").info(">> [Coretex] Overriding existing cache.")

    if not override and cacheZipPath.exists():
        raise CacheException(">> [Coretex] Cache with given key already exists. Set parameter override to True if you wanna override existing cache.")

    logging.getLogger("coretexpylib").info(f">> [Coretex] Caching file from {url}.")

    resultPath, fileName = __downloadFromUrl(url, fileName)

    __zip(cacheZipPath, resultPath, fileName)

    logging.getLogger("coretexpylib").info(f">> [Coretex] File cached successfully.")


def load(key: str) -> Any:
    """
        Loads the object cached with storeObject function

        Parameters
        ----------
        key : str
            key to which the object was linked when cached

        Returns
        -------
        Any -> unpickled object

        Raises
        ------
        CacheException -> if something went wrong

        Example
        -------
        >>> from coretex import cache
        \b
        >>> loadedObject = cache.load("dummyObject")
        >>> print(loadedObject)
        {"name": "John", "age": 24, "gender": "Male"}
    """

    hashedKey = __hashedKey(key)
    cacheZipPath = (FolderManager.instance().cache / hashedKey).with_suffix(".zip")
    picklePath = (FolderManager.instance().cache / hashedKey).with_suffix(".pickle")

    if not cacheZipPath.exists():
        raise CacheException(">> [Coretex] Cache with given key doesn't exist.")

    with ZipFile(cacheZipPath, "r") as zipFile:
        zipFile.extractall(FolderManager.instance().cache)

        logging.getLogger("coretexpylib").info(">> [Coretex] Cache with given key exists, loading cache...")

        with open((picklePath), "rb") as pickleFile:
            loadedPickle = pickle.load(pickleFile)

    return loadedPickle


def getPath(key: str) -> Path:
    """
        Retrieves the path of the cache

        Parameters
        ----------
        key : str
            key to which the cache item was linked

        Returns
        -------
        pathlib.Path -> path of the cached item

        Raises
        ------
        CacheException -> if something went wrong

        Example
        -------
        >>> from coretex import cache
        \b
        >>> key = "dummyFile"
        >>> print(cache.getPath(key))
        Path("/Users/dummyUser/.coretex/cache/c147efcfc2d7ea666a9e4f5187b115c90903f0fc896a56df9a6ef5d8f3fc9f31.zip")
    """

    hashedKey = __hashedKey(key)
    cacheZipPath = (FolderManager.instance().cache / hashedKey).with_suffix(".zip")

    if not cacheZipPath.exists():
        raise CacheException(">> [Coretex] Cache with given key doesn't exist.")

    return cacheZipPath


def exists(key: str) -> bool:
    """
        Checks if the cache item exists

        Parameters
        ----------
        key : str
            key to which the cache item was linked

        Returns
        -------
        bool -> True if it exists, False otherwise

        Example
        -------
        >>> from coretex import cache
        \b
        >>> key = "dummyFile"
        >>> print(cache.exists(key))
        True
    """

    hashedKey = __hashedKey(key)
    cacheZipPath = (FolderManager.instance().cache / hashedKey).with_suffix(".zip")

    return cacheZipPath.exists()


def remove(key: str) -> None:
    """
        Removes cached item from the cache

        Parameters
        ----------
        key : str -> Key to which the cache item was linked

        Raises
        ------
        CacheException -> if the cache item does not exist

        Example
        -------
        >>> from coretex import cache
        \b
        >>> cache.remove("dummyFile")
    """

    hashedKey = __hashedKey(key)
    cacheZipPath = (FolderManager.instance().cache / hashedKey).with_suffix(".zip")

    if not cacheZipPath.exists():
        raise CacheException(">> [Coretex] Cache with given key doesn't exist.")

    logging.getLogger("coretexpylib").info(">> [Coretex] Cache with given key exists, removing cache...")
    cacheZipPath.unlink(missing_ok = True)


def clear() -> None:
    """
        Clears all cached items

        Example
        -------
        >>> from coretex import cache
        \b
        >>> cache.clear()
    """

    shutil.rmtree(FolderManager.instance().cache)
