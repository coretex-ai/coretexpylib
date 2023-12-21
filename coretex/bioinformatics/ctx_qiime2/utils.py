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
from zipfile import ZipFile

import logging
import shutil
import gzip

from ...entities import TaskRun, CustomSample, CustomDataset
from ... import folder_manager


def createSample(name: str, datasetId: int, path: Path, taskRun: TaskRun, stepName: str, retryCount: int = 0) -> CustomSample:
    sample = CustomSample.createCustomSample(name, datasetId, str(path))
    if sample is None:
        if retryCount < 3:
            logging.info(f">> [Coretex] Retry count: {retryCount}")
            return createSample(name, datasetId, path, taskRun, stepName, retryCount + 1)

        raise ValueError(">> [Coretex] Failed to create sample")

    taskRun.createQiimeArtifact(f"{stepName}/{name}", path)

    return sample


def compressGzip(source: Path, destination: Path, deleteSource: bool = False) -> None:
    logging.info(f"{source} -> {destination}")

    with gzip.open(destination, "w") as destinationFile:
        destinationFile.write(source.read_bytes())

    if deleteSource:
        source.unlink()


def sampleNumber(sample: CustomSample) -> int:
    return int(sample.name.split("-")[0])


def isFastqMPSample(sample: CustomSample) -> bool:
    sample.unzip()

    sequenceFileNames = ["forward.fastq", "forward.fastq.gz", "sequences.fastq", "sequences.fastq.gz"]
    barcodesFileNames = ["barcodes.fastq", "barcodes.fastq.gz"]

    folderContent = list(sample.load().folderContent)

    sequenceFilePresent = any([path.name in sequenceFileNames for path in folderContent])
    barcodesFilePresent = any([path.name in barcodesFileNames for path in folderContent])

    return sequenceFilePresent and barcodesFilePresent


def isFastqDPSample(sample: CustomSample) -> bool:
    sample.unzip()

    return any([path.suffix == ".fastq" for path in sample.load().folderContent])


def isImportedSample(sample: CustomSample) -> bool:
    sample.unzip()

    sampleContent = [path.name for path in sample.load().folderContent]
    return "multiplexed-sequences.qza" in sampleContent


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


def getFastqMPSamples(dataset: CustomDataset) -> List[CustomSample]:
    # Multiplexed fastq data
    return dataset.getSamples(isFastqMPSample)


def getFastqDPSamples(dataset: CustomDataset) -> List[CustomSample]:
    # Demultiplexed fastq data
    return dataset.getSamples(isFastqDPSample)


def getImportedSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isImportedSample)


def getDemuxSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isDemultiplexedSample)


def getDenoisedSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isDenoisedSample)


def getPhylogeneticTreeSamples(dataset: CustomDataset) -> List[CustomSample]:
    return dataset.getSamples(isPhylogeneticTreeSample)


def getMetadata(sample: CustomSample) -> Path:
    metadataPathList = list(sample.path.glob("*.tsv"))
    if len(metadataPathList) != 1:
        raise RuntimeError(f">> [Coretex] Metadata sample must contain one .tsv file. Found {len(metadataPathList)}")

    return metadataPathList[0]


def isPairedEnd(sample: CustomSample) -> bool:
    # In order to determine whether we are dealing with paired-end
    # sequences, this function unzips the qiime artifact and
    # reads the metadata, looking for the second (type) row, which will have
    # "PairedEnd" somewhere if it's paired-end

    sampleTemp = folder_manager.createTempFolder("qzaSample")
    qzaPath = list(sample.path.iterdir())[0]

    with ZipFile(qzaPath, "r") as qzaFile:
        qzaFile.extractall(sampleTemp)

    metadataPath = list(sampleTemp.rglob("*metadata.yaml"))[0]

    with metadataPath.open("r") as metadata:
        pairedEnd = "PairedEnd" in metadata.readlines()[1]

    shutil.rmtree(sampleTemp)

    return pairedEnd
