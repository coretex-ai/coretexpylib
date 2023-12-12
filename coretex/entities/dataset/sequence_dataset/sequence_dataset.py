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

from typing import Dict, Optional, Any, Union
from typing_extensions import Self
from pathlib import Path

import logging

from .base import BaseSequenceDataset
from ..utils import createDataset
from ..network_dataset import NetworkDataset
from ..custom_dataset import CustomDataset
from ...sample import SequenceSample, CustomSample
from ....codable import KeyDescriptor


class SequenceDataset(BaseSequenceDataset, NetworkDataset[SequenceSample]):

    """
        Sequence Dataset class which is used for Datasets whose
        samples contain sequence data (.fasta, .fastq)
    """

    metadata: CustomSample

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["samples"] = KeyDescriptor("sessions", SequenceSample, list)

        return descriptors

    def onDecode(self) -> None:
        metadataSample = self.getSample("_metadata")
        if metadataSample is None:
            raise FileNotFoundError(">> [Coretex] _metadata sample could not be found in the dataset")

        self.metadata = CustomSample.decode(metadataSample.encode())
        self.samples = [
            sample for sample in self.samples
            if sample.id != self.metadata.id
        ]

    @classmethod
    def createSequenceDataset(
        cls,
        name: str,
        projectId: int,
        metadataPath: Union[Path, str],
        meta: Optional[Dict[str, Any]] = None
    ) -> Optional[Self]:

        """
            Creates a new sequence dataset with the provided name and metadata

            Parameters
            ----------
            name : str
                dataset name
            projectId : int
                project for which the dataset will be created
            metadataPath : Union[Path, str]
                path the zipped metadata file

            Returns
            -------
            The created sequence dataset object or None if creation failed

            Example
            -------
            >>> from coretex import SequenceDataset
            \b
            >>> dummyDataset = SequenceDataset.createSequenceDataset("dummyDataset", 123, pathToMetadata)
            >>> if dummyDataset is not None:
                    print("Dataset created successfully")
        """

        if isinstance(metadataPath, str):
            metadataPath = Path(metadataPath)

        with createDataset(CustomDataset, name, projectId, meta) as dataset:
            if CustomSample.createCustomSample(
                "_metadata",
                dataset.id,
                metadataPath
            ) is None:

                logging.getLogger("coretexpylib").warning(">> [Coretex] Failed to create _metadata sample")
                return None

        return cls.fetchById(dataset.id)

    def download(self, ignoreCache: bool = False) -> None:
        super().download(ignoreCache)

        self.metadata.download(ignoreCache)

    def isPairedEnd(self) -> bool:
        """
            This function returns True if the dataset holds paired-end reads and
            False if it holds single end. Files for paired-end reads must contain
            "_R1_" and "_R2_" in their names, otherwise an exception will be raised.
            If the sample contains gzip compressed sequences, you will have to call
            Sample.unzip method first otherwise calling Sample.isPairedEnd will
            raise an exception

            Raises
            ------
            FileNotFoundError -> if no files meeting the requirements for either single-end
                or paired-end sequencing reads
            ValueError -> if dataset has a combination of single-end and paired-end samples
        """

        pairedEndSamples = [sample.isPairedEnd() for sample in self.samples]

        if all(pairedEndSamples):
            return True

        if not any(pairedEndSamples):
            return False

        raise ValueError(">> [Coretex] Dataset contains a mix of paired-end and single-end sequences. It should contain either one or the other")
