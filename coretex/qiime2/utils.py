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

from typing import List
from pathlib import Path

import logging
import gzip

from ..coretex import Experiment, CustomSample, CustomDataset


def createSample(name: str, datasetId: int, path: Path, experiment: Experiment, stepName: str, retryCount: int = 0) -> CustomSample:
    sample = CustomSample.createCustomSample(name, datasetId, str(path))
    if sample is None:
        if retryCount < 3:
            logging.info(f">> [Coretex] Retry count: {retryCount}")
            return createSample(name, datasetId, path, experiment, stepName, retryCount + 1)

        raise ValueError(">> [Coretex] Failed to create sample")

    experiment.createQiimeArtifact(f"{stepName}/{name}", path)

    return sample


def compressGzip(source: Path, destination: Path) -> None:
    logging.info(f"{source} -> {destination}")

    with gzip.open(destination, "w") as destinationFile:
        destinationFile.write(source.read_bytes())

    source.unlink()


def sampleNumber(sample: CustomSample) -> int:
    return int(sample.name.split("-")[0])


def isFastqMPSample(sample: CustomSample) -> bool:
    sample.unzip()

    for path in sample.load().folderContent:
        if path.name != "sequences":
            continue

        return (path / "sequences.fastq").exists() and (path / "barcodes.fastq").exists()

    return False


def isFastqDPSample(sample: CustomSample) -> bool:
    sample.unzip()

    return any([path.suffix == ".fastq" for path in sample.load().folderContent])


def isDemultiplexedSample(sample: CustomSample) -> bool:
    sample.unzip()

    sampleContent = [path.name for path in sample.load().folderContent]
    return "demux.qza" in sampleContent


def isDenoisedSample(sample: CustomSample) -> bool:
    sample.unzip()

    sampleContent = [path.name for path in sample.load().folderContent]
    return (
        "table.qza" in sampleContent and
        "rep-seqs.qza" in sampleContent and
        "stats.qza" in sampleContent
    )


def isPhylogeneticTreeSample(sample: CustomSample) -> bool:
    sample.unzip()

    sampleContent = [path.name for path in sample.load().folderContent]
    return (
        "rooted-tree.qza" in sampleContent and
        "unrooted-tree.qza" in sampleContent and
        "aligned-rep-seqs.qza" in sampleContent and
        "masked-aligned-rep-seqs.qza" in sampleContent
    )


def isMetadataSample(sample: CustomSample) -> bool:
    sample.unzip()

    return any([path.suffix == ".tsv" for path in sample.load().folderContent])


def getFastqMPSamples(dataset: CustomDataset) -> List[CustomSample]:
    # Multiplexed fastq data
    return dataset.getSamples(isFastqMPSample)


def getFastqDPSamples(dataset: CustomDataset) -> List[CustomSample]:
    # Demultiplexed fastq data
    return dataset.getSamples(isFastqDPSample)


def getDemuxSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isDemultiplexedSample)


def getDenoisedSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isDenoisedSample)


def getPhylogeneticTreeSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isPhylogeneticTreeSample)


def getMetadataSample(dataset: CustomDataset) -> CustomSample:
    metadataSample = dataset.getSamples(isMetadataSample)
    if len(metadataSample) != 1:
        raise ValueError(f">> [Coretex] Dataset must contain exaclty one metadata sample. Found {len(metadataSample)}")

    return metadataSample[0]
