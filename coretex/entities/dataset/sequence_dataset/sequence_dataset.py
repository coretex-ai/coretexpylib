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
from ..network_dataset import NetworkDataset, _chunkSampleImport, _encryptedSampleImport
from ...sample import SequenceSample, CustomSample
from .... import folder_manager
from ....codable import KeyDescriptor
from ....cryptography import getProjectKey
from ....utils import file as file_utils


class SequenceDataset(BaseSequenceDataset, NetworkDataset[SequenceSample]):

    """
        Sequence Dataset class which is used for Datasets whose
        samples contain sequence data (.fasta, .fastq)
    """

    metadata: CustomSample

    def __init__(self) -> None:
        super().__init__(SequenceSample)

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

        dataset = cls.createDataset(name, projectId, meta)

        if dataset.isEncrypted:
            dataset.metadata = _encryptedSampleImport(CustomSample, "_metadata", metadataPath, dataset.id, getProjectKey(dataset.projectId))
        else:
            dataset.metadata = _chunkSampleImport(CustomSample, "_metadata", metadataPath, dataset.id)

        return dataset

    def download(self, decrypt: bool = True, ignoreCache: bool = False) -> None:
        super().download(decrypt, ignoreCache)

        self.metadata.download(decrypt, ignoreCache)

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

    def _uploadSample(self, samplePath: Path, sampleName: str, **metadata: Any) -> SequenceSample:
        if not self._sampleType.isValidSequenceFile(samplePath):
            raise ValueError(f"\"{samplePath}\" is not a valid sequence")

        if file_utils.isArchive(samplePath):
            sample = _chunkSampleImport(self._sampleType, sampleName, samplePath, self.id)
        else:
            with folder_manager.tempFile() as archivePath:
                logging.getLogger("coretexpylib").info(f">> [Coretex] Provided Sample \"{samplePath}\" is not an archive, zipping...")
                file_utils.archive(samplePath, archivePath)

                sample = _chunkSampleImport(self._sampleType, sampleName, archivePath, self.id)

        return sample
