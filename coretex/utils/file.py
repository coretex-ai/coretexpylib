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

from typing import Generator, Optional, Union
from pathlib import Path
from zipfile import ZipFile

import mimetypes
import zipfile
import tarfile
import gzip
import shutil
import logging


class InvalidFileExtension(Exception):

    """
        Exception raised if file extension is unkown or invalid
    """

    pass


def guessMimeType(filePath: Union[Path, str]) -> str:
    """
        Tries to guess mime type of the file

        Parameters
        ----------
        filePath : Union[Path, str]
            file whose mime type will be guessed

        Returns
        -------
        str -> guessed mime type, or "application/octet-stream" if
        it was not possible to guess
    """

    mimeTypesResult = mimetypes.guess_type(filePath)

    mimeType = mimeTypesResult[0]
    if mimeType is None:
        return "application/octet-stream"

    return mimeType


def isGzip(path: Path) -> bool:
    """
        Checks if the file is compressed with gz

        Might not be 100% reliable, it checks the first 2 bytes
        of the file for the gz-compressed file header (0x1F and 0x8B)
        and checks for .gz file extension

        Parameters
        ----------
        path : Path
            the file to be checked

        Returns
        -------
        bool -> True if file is gz compressed, False otherwise
    """

    # .gz compressed files always start with 2 bytes: 0x1F and 0x8B
    # Testing for this is not 100% reliable, it is highly unlikely
    # that "ordinary text files" start with those two bytes—in UTF-8 it's not even legal.
    # That's why we check for extension and do the byte checking
    # Ref: https://stackoverflow.com/a/3703300/7585106

    if not path.is_file():
        return False

    with open(path, 'rb') as file:
        return file.read(2) == b'\x1f\x8b' and path.name.endswith(".gz")


def isArchive(path: Path) -> bool:
    """
        Checks if the file is an archive

        Parameters
        ----------
        path : Path
            file to be checked

        Returns
        -------
        bool -> True if it is an archive, False otherwise
    """

    return zipfile.is_zipfile(path) or tarfile.is_tarfile(path)


def gzipDecompress(source: Path, destination: Path) -> None:
    """
        Decompresses a gz-compressed file

        Parameters
        ----------
        source : Path
            file to be decompressed
        destination : Path
            location to which the decompressed file will be stored

        Raises
        ------
        ValueError -> if the file is not a gz-compressed file
    """

    if not isGzip(source):
        raise ValueError(">> [Coretex] Not a .gz file")

    with gzip.open(source, "r") as gzipFile, open(destination, "wb") as destinationFile:
        shutil.copyfileobj(gzipFile, destinationFile)


def archive(source: Path, destination: Path) -> None:
    """
        Archives and compresses the provided file or directory
        using ZipFile module

        Parameters
        ----------
        source : Path
            file to be archived and compressed
        destination : Path
            location to which the zip file will be stored
    """

    with ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as destinationFile:
        if source.is_file():
            destinationFile.write(source, source.name)
        else:
            for path in source.rglob("*"):
                if not path.is_file():
                    continue

                destinationFile.write(path, path.relative_to(source))


def walk(path: Path) -> Generator[Path, None, None]:
    """
        os.walk implementation for pathlib.Path

        Parameters
        ----------
        path : Path
            starting point of the walk function, must be a directory

        Returns
        -------
        Generator[Path, None, None] -> generator which contains all
        subdirectories and subfiles
    """

    for p in path.iterdir():
        yield p.resolve()

        if p.is_dir():
            yield from walk(p)


def recursiveUnzip(entryPoint: Path, destination: Optional[Path] = None, remove: bool = False) -> None:
    """
        Recursively unarchives the file

        Parameters
        ----------
        entryPoint : Path
            initial archive
        destination : Optional[Path]
            destination of unarchived files
        remove : bool
            delete archive after unarchive is done

        Raises
        ------
        ValueError -> if the path is not an archive
    """

    logging.getLogger("coretexpylib").debug(f">> [Coretex] recursiveUnzip: source = {str(entryPoint)}, destination = {str(destination)}")

    if destination is None:
        destination = entryPoint.parent / entryPoint.stem

    # Decompress with gzip if is gzip
    if isGzip(entryPoint):
        gzipDecompress(entryPoint, destination)

        if remove:
            entryPoint.unlink()

        if not isArchive(destination):
            return

        # gzip nameing convention is .original_file_ext.gz, so by calling .stem we remove .gz
        # for destination
        recursiveUnzip(destination, destination.parent / destination.stem, remove = True)
        return

    if not isArchive(entryPoint):
        raise ValueError(">> [Coretex] Not an archive")

    if zipfile.is_zipfile(entryPoint):
        with ZipFile(entryPoint, "r") as zipFile:
            zipFile.extractall(destination)

    if tarfile.is_tarfile(entryPoint):
        with tarfile.open(entryPoint, "r") as tarFile:
            tarFile.extractall(destination)

    if remove:
        entryPoint.unlink()

    for path in walk(destination):
        if isArchive(path) or isGzip(path):
            recursiveUnzip(path, remove = True)
