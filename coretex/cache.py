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

from typing import Any, Union
from pathlib import Path

import os
import shutil
import pickle
import hashlib

import requests

from . import folder_manager


class CacheException(Exception):

    """
        Exception which is raised due to any unexpected behaviour with Cache module
    """

    pass


def _hashCacheKey(key: str) -> str:
    return hashlib.sha256(key.encode("UTF-8")).hexdigest()


MAX_RETRY_COUNT = 3


def _download(source: str, destination: Path, retryCount: int = 0) -> Path:
    if destination.exists():
        raise FileExistsError(destination)

    try:
        with requests.get(source, stream = True) as r:
            r.raise_for_status()

            with destination.open("wb") as destinationFile:
                for chunk in r.iter_content(chunk_size = 8192):
                    destinationFile.write(chunk)
    except:
        if retryCount >= MAX_RETRY_COUNT:
            raise

        destination.unlink(missing_ok = True)
        return _download(source, destination, retryCount + 1)

    return destination


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

    if not exists(key):
        raise CacheException(">> [Coretex] Cache with given key doesn't exist.")

    return folder_manager.cache / _hashCacheKey(key)


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

    return folder_manager.cache.joinpath(_hashCacheKey(key)).exists()


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

    if not exists(key):
        raise CacheException(">> [Coretex] Cache with given key doesn't exist.")

    getPath(key).unlink()


def clear() -> None:
    """
        Clears all cached items

        Example
        -------
        >>> from coretex import cache
        \b
        >>> cache.clear()
    """

    shutil.rmtree(folder_manager.cache)


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

    if not override and exists(key):
        raise CacheException(">> [Coretex] Cache with given key already exists. Set \"override\" to \"True\" if you want to override existing cache.")

    if override and exists(key):
        getPath(key).unlink()

    cachePath = folder_manager.cache / _hashCacheKey(key)
    with cachePath.open("wb") as cacheFile:
        pickle.dump(object, cacheFile)


def storeFile(key: str, source: Union[Path, str], override: bool = False) -> None:
    """
        Caches the specified file

        Parameters
        ----------
        key : str
            key to which the cached file will be linked
        source : str
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

    if not isinstance(source, Path):
        source = Path(source)

    if not override and exists(key):
        raise CacheException(">> [Coretex] Cache with given key already exists. Set \"override\" to \"True\" if you want to override existing cache.")

    if override and exists(key):
        getPath(key).unlink()

    cachePath = folder_manager.cache / _hashCacheKey(key)

    # Hardlink the file to the cache directory
    os.link(source, cachePath)


def storeUrl(key: str, url: str, override: bool = False) -> None:
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

    if not override and exists(key):
        raise CacheException(">> [Coretex] Cache with given key already exists. Set \"override\" to \"True\" if you want to override existing cache.")

    if override and exists(key):
        getPath(key).unlink()

    cachePath = folder_manager.cache / _hashCacheKey(key)
    _download(url, cachePath)


def loadObject(key: str) -> Any:
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

    if not exists(key):
        raise CacheException(">> [Coretex] Cache with given key doesn't exist.")

    with getPath(key).open("rb") as pickleFile:
        return pickle.load(pickleFile)
