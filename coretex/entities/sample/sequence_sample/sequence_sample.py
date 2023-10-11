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

from typing import Union
from typing_extensions import Self
from pathlib import Path

import logging

from .local_sequence_sample import LocalSequenceSample
from ..utils import chunkSampleImport
from ..network_sample import NetworkSample
from .... import folder_manager
from ....utils import file as file_utils


class SequenceSample(NetworkSample, LocalSequenceSample):

    """
        Represents the local custom Sample class
        which is used for working with Other Task locally
    """

    def __init__(self) -> None:
        NetworkSample.__init__(self)

    @classmethod
    def createSequenceSample(cls, path: Union[Path, str], datasetId: int) -> Self:
        """
            Creates a new sequence sample and adds it to the specified dataset

            Parameters
            ----------
            datasetId : int
                id of dataset to which the sample will be added
            path : Union[Path, str]
                path to the sample

            Returns
            -------
            Optional[Self] -> The created sample object or None if creation failed

            Raises
            ------
            NetworkRequestError, ValueError -> if some kind of error happened during
            the upload of the provided file

            Example
            -------
            >>> from coretex import SequenceSample
            \b
            >>> sample = SequenceSample.createSequenceSample("path/to/file", 1023)
            >>> print(sample.id)
        """

        if isinstance(path, str):
            path = Path(path)

        archivePath = path
        isTemp = False

        if not file_utils.isArchive(path):
            # Check if the file is valid sequence file
            if not path.suffix in cls.supportedExtensions():
                # If not check if file is valid compressed sequence file
                if len(path.suffixes) < 2:
                    raise ValueError(f">> [Coretex] \"{path}\" is not a valid sequence file, supported extensions are \"{cls.supportedExtensions()}\"")

                if not path.suffixes[-2] in cls.supportedExtensions():
                    raise ValueError(f">> [Coretex] \"{path}\" is not a valid sequence file, supported extensions are \"{cls.supportedExtensions()}\"")

                if not path.suffix == ".gz":
                    raise ValueError(f">> [Coretex] \"{path}\" is not a valid sequence file, supported extensions are \"{cls.supportedExtensions()}\"")

            logging.getLogger("coretexpylib").info(f">> [Coretex] Provided path \"{path}\" is not an archive, zipping...")

            archivePath = folder_manager.temp / f"{path.stem}.zip"
            file_utils.archive(path, archivePath)

            isTemp = True

        response = chunkSampleImport(path.stem, datasetId, archivePath)

        # Delete the archive if we created it
        if isTemp:
            archivePath.unlink()

        return cls.decode(response.getJson(dict))
