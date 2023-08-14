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

from typing import Dict

from .base import BaseSequenceDataset
from ..network_dataset import NetworkDataset
from ...sample import SequenceSample, CustomSample
from ....codable import KeyDescriptor


class SequenceDataset(BaseSequenceDataset, NetworkDataset[SequenceSample]):

    """
        Sequence Dataset class which is used for Datasets whose
        samples contain sequence data (.fasta, .fastq)
    """

    metadata: CustomSample
    pairedEnd: bool

    @classmethod
    def _keyDescriptors(cls) -> Dict[str, KeyDescriptor]:
        descriptors = super()._keyDescriptors()
        descriptors["samples"] = KeyDescriptor("sessions", SequenceSample, list)

        return descriptors

    def onDecode(self) -> None:
        pairedEndSamples: list[bool] = []
        for sample in self.samples:
            if sample.name.startswith("_metadata"):
                self.metadata = CustomSample.decode(sample.encode())
                continue

            pairedEndSamples.append(sample.isPairedEnd())

        if all(pairedEndSamples):
            self.pairedEnd = True
        elif not any(pairedEndSamples):
            self.pairedEnd = False
        else:
            raise ValueError(">> [Coretex] Dataset contains a mix of paired-end and single-end sequences. It should contain either one or the other")

        self.samples = [
            sample for sample in self.samples
            if sample.id != self.metadata.id
        ]
