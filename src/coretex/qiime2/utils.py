#     Copyright (C) 2023  BioMech LLC

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

from typing import Optional, List
from pathlib import Path

import logging
import gzip

from ..coretex import Experiment, CustomSample, CustomDataset


def createSample(name: str, datasetId: int, path: Path, experiment: Experiment, stepName: str, retryCount: int = 0) -> CustomSample:
    mimeType: Optional[str] = None
    if path.suffix in [".qza", ".qzv"]:
        mimeType = "application/zip"

    sample = CustomSample.createCustomSample(name, datasetId, str(path), mimeType)
    if sample is None:
        if retryCount < 3:
            logging.info(f">> [Workspace] Retry count: {retryCount}")
            return createSample(name, datasetId, path, experiment, stepName, retryCount + 1)

        raise ValueError(">> [Workspace] Failed to create sample")

    experiment.createQiimeArtifact(f"{stepName}/{name}", path)

    return sample


def compressGzip(source: Path, destination: Path) -> None:
    logging.info(f"{source} -> {destination}")

    with gzip.open(destination, "w") as destinationFile:
        destinationFile.write(source.read_bytes())

    source.unlink()


def sampleNumber(sample: CustomSample) -> int:
    return int(sample.name.split("-")[0])


def isFastqSample(sample: CustomSample) -> bool:
    sample.unzip()

    for path in sample.load().folderContent:
        if path.name != "sequences":
            continue

        return (path / "sequences.fastq").exists() and (path / "barcodes.fastq").exists()

    return False


def isDemultiplexedSample(sample: CustomSample) -> bool:
    sample.unzip()

    sampleContent = [path.name for path in sample.load().folderContent]
    return "demux.qza" in sampleContent and "demux-details.qza" in sampleContent


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


def getFastqSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isFastqSample)


def getDemuxSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isDemultiplexedSample)


def getDenoisedSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isDenoisedSample)


def getPhylogeneticTreeSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isPhylogeneticTreeSample)
